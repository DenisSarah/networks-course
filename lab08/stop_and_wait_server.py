import argparse
import socket
import sys

from stop_and_wait_common import receive_file, send_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stop-and-Wait UDP server.")
    parser.add_argument("--host", default="127.0.0.1", help="local host")
    parser.add_argument("--port", type=int, default=12000, help="local port")
    parser.add_argument("--timeout", type=float, default=1.0, help="timeout in seconds")
    parser.add_argument("--loss", type=float, default=0.3, help="simulated packet loss probability")
    parser.add_argument("--chunk-size", type=int, default=512, help="payload size for one frame")

    subparsers = parser.add_subparsers(dest="mode", required=True)

    receive_parser = subparsers.add_parser("receive", help="receive file from client")
    receive_parser.add_argument("--output", required=True, help="path to save received file")

    send_parser = subparsers.add_parser("send", help="send file to client")
    send_parser.add_argument("--file", required=True, help="file to send")
    send_parser.add_argument("--client-host", default="127.0.0.1", help="client host")
    send_parser.add_argument("--client-port", type=int, required=True, help="client port")

    return parser.parse_args()


def main():
    args = parse_args()

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((args.host, args.port))
        print(f"[server] listening on {args.host}:{args.port}")

        if args.mode == "receive":
            receive_file(
                server_socket,
                args.output,
                args.timeout,
                args.loss,
                "server",
            )
        else:
            send_file(
                server_socket,
                (args.client_host, args.client_port),
                args.file,
                args.chunk_size,
                args.timeout,
                args.loss,
                "server",
            )
    except Exception as error:
        print(f"server error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
