import socket
import sys


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    filename = sys.argv[3]

    request = (
        f"GET /{filename} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Connection: close\r\n\r\n"
    )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((host, port))
        client.sendall(request.encode())

        data = b""
        while True:
            part = client.recv(4096)
            if not part:
                break
            data += part

    print(data.decode("utf-8", errors="ignore"))


if __name__ == "__main__":
    main()
