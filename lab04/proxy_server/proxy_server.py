from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import sys


LOG_FILE = Path(__file__).with_name("proxy.log")
HOP_BY_HOP = {
    "connection",
    "date",
    "server",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def write_log(url: str, status: int) -> None:
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(f"{url} {status}\n")


class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.forward()

    def do_POST(self):
        self.forward()

    def forward(self):
        target_url = self.target_url()
        if not target_url:
            self.send_error_response(400, "Bad Request")
            return

        parsed = urlsplit(target_url)
        if parsed.scheme != "http" or not parsed.netloc:
            self.send_error_response(400, "Only http URLs are supported")
            return

        body = b""
        if self.command == "POST":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)

        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in HOP_BY_HOP
        }
        headers["Host"] = parsed.netloc

        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        try:
            connection = HTTPConnection(parsed.hostname, parsed.port or 80, timeout=10)
            connection.request(self.command, path, body=body, headers=headers)
            response = connection.getresponse()
            data = response.read()
            connection.close()

            self.send_response(response.status, response.reason)
            for key, value in response.getheaders():
                if key.lower() not in HOP_BY_HOP:
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

            write_log(target_url, response.status)
        except Exception:
            self.send_error_response(502, "Bad Gateway", target_url)

    def target_url(self) -> str:
        if self.path.startswith("http://"):
            return self.path
        if self.path.startswith("/http://"):
            return self.path.lstrip("/")
        if self.path.startswith("/"):
            return "http://" + self.path.lstrip("/")
        return ""

    def send_error_response(self, status: int, message: str, url: str = "-") -> None:
        body = message.encode("utf-8")
        self.send_response(status, message)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        write_log(url, status)

    def log_message(self, format, *args):
        return


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(1)

    port = int(sys.argv[1])
    with HTTPServer(("127.0.0.1", port), ProxyHandler) as server:
        print(f"сервер на http://127.0.0.1:{port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
