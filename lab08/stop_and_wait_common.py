import random
import socket
import struct
from pathlib import Path

from checksum_utils import compute_checksum, verify_checksum


TYPE_DATA = 1
TYPE_ACK = 2
HEADER_FORMAT = "!BBBHI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
MAX_DATAGRAM_SIZE = 65535
FINAL_ACK_GRACE_TIMEOUTS = 3


def log(prefix: str, message: str):
    print(f"[{prefix}] {message}")


def build_packet(packet_type: int, sequence_number: int, eof: bool, payload: bytes) -> bytes:
    payload_length = len(payload)
    header_without_checksum = struct.pack(HEADER_FORMAT, packet_type, sequence_number, int(eof), 0, payload_length    )
    checksum = compute_checksum(header_without_checksum + payload)
    header = struct.pack(HEADER_FORMAT, packet_type, sequence_number, int(eof), checksum, payload_length)
    return header + payload


def parse_packet(datagram: bytes) -> dict:
    if len(datagram) < HEADER_SIZE:
        raise ValueError("Datagram is too short.")

    packet_type, sequence_number, eof_flag, checksum, payload_length = struct.unpack(HEADER_FORMAT, datagram[:HEADER_SIZE])
    payload = datagram[HEADER_SIZE:]

    if len(payload) != payload_length:
        raise ValueError("Payload length does not match header.")

    header_without_checksum = struct.pack(HEADER_FORMAT, packet_type, sequence_number, eof_flag, 0, payload_length)
    checksum_ok = verify_checksum(header_without_checksum + payload, checksum)

    return {
        "type": packet_type,
        "sequence_number": sequence_number,
        "eof": bool(eof_flag),
        "checksum_ok": checksum_ok,
        "payload": payload,
    }


def maybe_send(
    sock: socket.socket,
    datagram: bytes,
    address: tuple[str, int],
    loss_probability: float,
    prefix: str,
    description: str,
):
    if random.random() < loss_probability:
        log(prefix, f"simulated loss: {description}")
        return
    sock.sendto(datagram, address)


def send_ack(
    sock: socket.socket,
    address: tuple[str, int],
    sequence_number: int,
    loss_probability: float,
    prefix: str,
):
    ack_packet = build_packet(TYPE_ACK, sequence_number, False, b"")
    maybe_send(sock, ack_packet, address, loss_probability, prefix, f"ACK {sequence_number}")


def send_file(
    sock: socket.socket,
    remote_address: tuple[str, int],
    file_path: str,
    chunk_size: int,
    timeout_seconds: float,
    loss_probability: float,
    prefix: str,
):
    sock.settimeout(timeout_seconds)
    sequence_number = 0

    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(chunk_size)
            eof = len(chunk) == 0
            packet = build_packet(TYPE_DATA, sequence_number, eof, chunk)

            while True:
                description = f"DATA seq={sequence_number} eof={eof} size={len(chunk)}"
                maybe_send(sock, packet, remote_address, loss_probability, prefix, description)

                try:
                    while True:
                        datagram, address = sock.recvfrom(MAX_DATAGRAM_SIZE)
                        if address != remote_address:
                            log(prefix, f"ignored packet from unexpected peer {address}")
                            continue

                        ack = parse_packet(datagram)
                        if not ack["checksum_ok"]:
                            log(prefix, "received corrupted ACK, waiting for retransmission")
                            continue
                        if ack["type"] != TYPE_ACK:
                            log(prefix, "received non ACK packet while waiting for ACK")
                            continue
                        if ack["sequence_number"] != sequence_number:
                            log(prefix, f"received ACK {ack['sequence_number']} but expected {sequence_number}")
                            continue

                        log(prefix, f"received ACK {sequence_number}")
                        sequence_number ^= 1
                        break
                    break
                except socket.timeout:
                    log(prefix, f"timeout for seq={sequence_number}, retransmitting")

            if eof:
                log(prefix, f"finished sending file {file_path}")
                return


def receive_file(
    sock: socket.socket,
    output_path: str,
    timeout_seconds: float,
    loss_probability: float,
    prefix: str,
) -> tuple[str, int]:
    sock.settimeout(timeout_seconds)
    expected_sequence = 0
    peer_address = None

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "wb") as file:
        eof_sequence = None
        grace_timeouts_left = FINAL_ACK_GRACE_TIMEOUTS
        while True:
            try:
                datagram, address = sock.recvfrom(MAX_DATAGRAM_SIZE)
            except socket.timeout:
                if eof_sequence is not None:
                    grace_timeouts_left -= 1
                    if grace_timeouts_left <= 0:
                        log(prefix, f"finished receiving file into {output_path}")
                        return peer_address
                else:
                    log(prefix, "waiting for incoming packet")
                continue

            if peer_address is None:
                peer_address = address
                log(prefix, f"connected to peer {peer_address}")
            elif address != peer_address:
                log(prefix, f"ignored packet from unexpected peer {address}")
                continue

            try:
                packet = parse_packet(datagram)
            except ValueError as error:
                log(prefix, f"packet parse error: {error}")
                continue

            if not packet["checksum_ok"]:
                log(prefix, "detected corrupted packet, discarding without ACK")
                continue

            if packet["type"] != TYPE_DATA:
                log(prefix, "received non data packet while waiting for data")
                continue

            seq = packet["sequence_number"]
            if seq == expected_sequence:
                if packet["payload"]:
                    file.write(packet["payload"])
                send_ack(sock, peer_address, seq, loss_probability, prefix)
                log(prefix, f"accepted seq={seq}, eof={packet['eof']}, size={len(packet['payload'])}")
                expected_sequence ^= 1

                if packet["eof"]:
                    eof_sequence = seq
                    grace_timeouts_left = FINAL_ACK_GRACE_TIMEOUTS
            else:
                log(prefix, f"received duplicate seq={seq}, resending ACK")
                send_ack(sock, peer_address, seq, loss_probability, prefix)
                if eof_sequence is not None and seq == eof_sequence:
                    grace_timeouts_left = FINAL_ACK_GRACE_TIMEOUTS
