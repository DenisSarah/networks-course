import random
import socket


HOST = "127.0.0.1"
PORT = 12000
LOSS_PROBABILITY = 0.2


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))

    print(f"UDP ping server listening on {HOST}:{PORT}")

    while True:
        message, client_address = server_socket.recvfrom(1024)
        decoded_message = message.decode("utf-8", errors="replace")

        if random.random() < LOSS_PROBABILITY:
            print(f"Packet from {client_address} lost: {decoded_message}")
            continue

        response = decoded_message.upper().encode("utf-8")
        server_socket.sendto(response, client_address)
        print(f"Responded to {client_address}: {decoded_message} -> {decoded_message.upper()}")


if __name__ == "__main__":
    main()
