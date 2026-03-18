import socket
import sys
from pathlib import Path


ROOT = Path(__file__).with_name("static")


def response(status: str, body: bytes) -> bytes:
    headers = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "Connection: close\r\n\r\n"
    )
    return headers.encode() + body


def handle(client: socket.socket) -> None:
    request = client.recv(4096).decode("utf-8", errors="ignore")
    try:
        method, path, _ = request.splitlines()[0].split()
    except (IndexError, ValueError):
        client.sendall(response("400 Bad Request", b"400 Bad Request"))
        return

    if method != "GET":
        client.sendall(response("400 Bad Request", b"400 Bad Request"))
        return

    name = path.lstrip("/") or "index.html"

    try:
        body = (ROOT / name).read_bytes()
        client.sendall(response("200 OK", body))
    except FileNotFoundError:
        client.sendall(response("404 Not Found", b"404 Not Found"))


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(1)

    port = int(sys.argv[1])
    ROOT.mkdir(exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", port))
        server.listen()
        print(f"сервер на http://127.0.0.1:{port}")

        while True:
            client, _ = server.accept()
            with client:
                handle(client)


if __name__ == "__main__":
    main()
