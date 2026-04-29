import argparse
import socket


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show free ports in the given range for the given IP address.")
    parser.add_argument("ip", help="IP address to bind")
    parser.add_argument("start_port", type=int, help="range start")
    parser.add_argument("end_port", type=int, help="range end")
    return parser.parse_args()


def is_port_free(ip_address: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((ip_address, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def main():
    args = parse_args()

    if args.start_port > args.end_port:
        raise ValueError("start_port > end_port")

    print(f"Free ports for {args.ip} in range {args.start_port}-{args.end_port}:")
    for port in range(args.start_port, args.end_port + 1):
        if is_port_free(args.ip, port):
            print(port)


if __name__ == "__main__":
    main()
