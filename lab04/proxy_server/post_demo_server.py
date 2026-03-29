from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sys


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"GET works"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        response = json.dumps({"method": "POST", "body": body}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        return


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(1)

    port = int(sys.argv[1])
    with HTTPServer(("127.0.0.1", port), Handler) as server:
        print(f"тестовый сервер на http://127.0.0.1:{port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
