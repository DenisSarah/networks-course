import argparse
import socket
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser( description="Send email")
    parser.add_argument("recipient", help="recipient email address")
    parser.add_argument("--sender", required=True, help="sender Gmail address")
    parser.add_argument("--smtp-user", required=True, help="sender Gmail address")
    parser.add_argument("--smtp-password", required=True, help="Gmail app password")
    parser.add_argument(
        "--format",
        choices=("txt", "html"),
        default="txt",
        help="message format",
    )
    parser.add_argument("--subject", required=True, help="email subject")
    parser.add_argument("--body", help="message body")
    parser.add_argument("--body-file", help="path to a file containing the message body")
    return parser.parse_args()


def load_body(args: argparse.Namespace) -> str:
    if args.body:
        return args.body
    if args.body_file:
        with open(args.body_file, "r", encoding="utf-8") as file:
            return file.read()
    raise ValueError("Message body is required")


def build_message(args: argparse.Namespace, body: str) -> MIMEMultipart:
    message = MIMEMultipart()
    message["From"] = args.sender
    message["To"] = args.recipient
    message["Subject"] = args.subject
    subtype = "html" if args.format == "html" else "plain"
    message.attach(MIMEText(body, subtype, "utf-8"))
    return message


def send_email(args: argparse.Namespace, message: MIMEMultipart) -> None:
    smtp_host = "smtp.gmail.com"
    smtp_port = 587

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(args.smtp_user, args.smtp_password)
            server.sendmail(args.sender, [args.recipient], message.as_string())
    except socket.gaierror as error:
        raise RuntimeError(f"Cannot resolve SMTP host '{smtp_host}'") from error
    except ConnectionRefusedError as error:
        raise RuntimeError(
            f"Connection to SMTP server {smtp_host}:{smtp_port} was refused"
        ) from error
    except smtplib.SMTPAuthenticationError as error:
        raise RuntimeError(
            "SMTP authentication failed"
        ) from error
    except smtplib.SMTPException as error:
        raise RuntimeError(f"SMTP error: {error}") from error


def main() -> None:
    try:
        args = parse_args()
        body = load_body(args)
        message = build_message(args, body)
        send_email(args, message)
        print(
            f"Email sent to {args.recipient} in {args.format} format "
            "via smtp.gmail.com:587"
        )
    except (ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
