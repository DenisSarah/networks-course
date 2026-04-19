import socket
import time


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12000
REQUEST_COUNT = 10
TIMEOUT_SECONDS = 1


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(TIMEOUT_SECONDS)

    for sequence_number in range(1, REQUEST_COUNT + 1):
        send_time = time.time()
        message = f"Ping {sequence_number} {send_time}"

        try:
            client_socket.sendto(message.encode("utf-8"), (SERVER_HOST, SERVER_PORT))
            response, _ = client_socket.recvfrom(1024)
            receive_time = time.time()
            rtt = receive_time - send_time

            print(response.decode("utf-8", errors="replace"))
            print(f"RTT = {rtt:.6f} seconds")
        except socket.timeout:
            print("Request timed out")

    client_socket.close()


if __name__ == "__main__":
    main()
