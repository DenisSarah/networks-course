#!/usr/bin/env python3
import argparse
import base64
import socket
import ssl
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a text email using raw SMTP over sockets."
    )
    parser.add_argument("recipient", help="recipient email address")
    parser.add_argument("--sender", required=True, help="sender email address")
    parser.add_argument("--smtp-user", required=True, help="SMTP login")
    parser.add_argument("--smtp-password", required=True, help="SMTP app password")
    parser.add_argument("--subject", required=True, help="email subject")
    parser.add_argument("--body", help="message body")
    parser.add_argument("--body-file", help="path to a file containing the message body")
    parser.add_argument("--smtp-host", default="smtp.gmail.com", help="SMTP server")
    parser.add_argument("--smtp-port", type=int, default=587, help="SMTP port")
    return parser.parse_args()


def load_body(args: argparse.Namespace) -> str:
    if args.body:
        return args.body
    if args.body_file:
        with open(args.body_file, "r", encoding="utf-8") as file:
            return file.read()
    raise ValueError("Message body is required")


def read_response(stream) -> tuple[int, str]:
    lines = []
    while True:
        line = stream.readline()
        if not line:
            raise RuntimeError("SMTP server closed the connection unexpectedly.")
        decoded = line.decode("utf-8", errors="replace").rstrip("\r\n")
        lines.append(decoded)
        if len(decoded) >= 4 and decoded[:3].isdigit() and decoded[3] == " ":
            return int(decoded[:3]), "\n".join(lines)


def expect_code(stream, expected_codes: tuple[int, ...]) -> str:
    code, response = read_response(stream)
    if code not in expected_codes:
        raise RuntimeError(f"SMTP error {code}:\n{response}")
    return response


def send_command(stream, command: str, expected_codes: tuple[int, ...]) -> str:
    stream.write((command + "\r\n").encode("utf-8"))
    stream.flush()
    return expect_code(stream, expected_codes)


def auth_login(stream, username: str, password: str) -> None:
    send_command(stream, "AUTH LOGIN", (334,))
    send_command(
        stream,
        base64.b64encode(username.encode("utf-8")).decode("ascii"),
        (334,),
    )
    send_command(
        stream,
        base64.b64encode(password.encode("utf-8")).decode("ascii"),
        (235,),
    )


def build_message(sender: str, recipient: str, subject: str, body: str) -> str:
    safe_body = body.replace("\r\n", "\n").replace("\r", "\n")
    safe_body = safe_body.replace("\n.", "\n..")
    headers = [
        f"From: {sender}",
        f"To: {recipient}",
        f"Subject: {subject}",
        "MIME-Version: 1.0",
        'Content-Type: text/plain; charset="utf-8"',
        "Content-Transfer-Encoding: 8bit",
        "",
        safe_body,
    ]
    return "\r\n".join(headers)


def send_email(args: argparse.Namespace, body: str) -> None:
    with socket.create_connection((args.smtp_host, args.smtp_port), timeout=30) as sock:
        stream = sock.makefile("rwb")
        expect_code(stream, (220,))
        send_command(stream, "EHLO localhost", (250,))
        send_command(stream, "STARTTLS", (220,))

        tls_sock = ssl.create_default_context().wrap_socket(
            sock, server_hostname=args.smtp_host
        )
        stream = tls_sock.makefile("rwb")

        send_command(stream, "EHLO localhost", (250,))
        auth_login(stream, args.smtp_user, args.smtp_password)
        send_command(stream, f"MAIL FROM:<{args.sender}>", (250,))
        send_command(stream, f"RCPT TO:<{args.recipient}>", (250, 251))
        send_command(stream, "DATA", (354,))

        message = build_message(args.sender, args.recipient, args.subject, body)
        stream.write((message + "\r\n.\r\n").encode("utf-8"))
        stream.flush()
        expect_code(stream, (250,))
        send_command(stream, "QUIT", (221,))
        tls_sock.close()


def main() -> None:
    try:
        args = parse_args()
        body = load_body(args)
        send_email(args, body)
        print(f"Email sent to {args.recipient} via {args.smtp_host}:{args.smtp_port}")
    except (ValueError, OSError, ssl.SSLError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
