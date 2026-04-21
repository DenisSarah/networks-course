def compute_checksum(data: bytes) -> int:
    if len(data) % 2 == 1:
        data += b"\x00"

    total = 0
    for index in range(0, len(data), 2):
        word = (data[index] << 8) + data[index + 1]
        total += word
        total = (total & 0xFFFF) + (total >> 16)

    return (~total) & 0xFFFF


def verify_checksum(data: bytes, checksum: int) -> bool:
    return compute_checksum(data) == checksum
