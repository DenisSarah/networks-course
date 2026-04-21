import argparse
import socket
import sys

from stop_and_wait_common import receive_file, send_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stop-and-Wait UDP client.")
    parser.add_argument("--host", default="127.0.0.1", help="local host")
    parser.add_argument("--port", type=int, default=12001, help="local port")
    parser.add_argument("--server-host", default="127.0.0.1", help="server host")
    parser.add_argument("--server-port", type=int, default=12000, help="server port")
    parser.add_argument("--timeout", type=float, default=1.0, help="timeout in seconds")
    parser.add_argument("--loss", type=float, default=0.3, help="simulated packet loss probability")
    parser.add_argument("--chunk-size", type=int, default=512, help="payload size for one frame")

    subparsers = parser.add_subparsers(dest="mode", required=True)

    send_parser = subparsers.add_parser("send", help="send file to server")
    send_parser.add_argument("--file", required=True, help="file to send")

    receive_parser = subparsers.add_parser("receive", help="receive file from server")
    receive_parser.add_argument("--output", required=True, help="path to save received file")

    return parser.parse_args()


def main():
    args = parse_args()

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.bind((args.host, args.port))
        print(f"[client] bound to {args.host}:{args.port}")

        if args.mode == "send":
            send_file(
                client_socket,
                (args.server_host, args.server_port),
                args.file,
                args.chunk_size,
                args.timeout,
                args.loss,
                "client",
            )
        else:
            receive_file(
                client_socket,
                args.output,
                args.timeout,
                args.loss,
                "client",
            )
    except Exception as error:
        print(f"client error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
