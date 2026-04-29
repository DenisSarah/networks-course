import ipaddress
import socket


def get_local_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]


def get_netmask(ip_address: str) -> str:
    first_octet = int(ip_address.split(".")[0])

    if 1 <= first_octet <= 126:
        prefix_length = 8
    elif 128 <= first_octet <= 191:
        prefix_length = 16
    elif 192 <= first_octet <= 223:
        prefix_length = 24
    else:
        raise ValueError(f"Cannot infer default netmask for IP {ip_address}")

    return str(ipaddress.IPv4Network(f"0.0.0.0/{prefix_length}").netmask)


def main():
    ip_address = get_local_ip()
    netmask = get_netmask(ip_address)

    print(f"IP address: {ip_address}")
    print(f"Netmask: {netmask}")


if __name__ == "__main__":
    main()
