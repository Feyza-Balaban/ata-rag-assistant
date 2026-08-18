import json
from http.server import BaseHTTPRequestHandler, HTTPServer


HOST = "127.0.0.1"
PORT = 8000


class MockRAGHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict) -> None:
        response_body = json.dumps(
            payload,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status_code)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header(
            "Content-Length",
            str(len(response_body))
        )
        self.end_headers()
        self.wfile.write(response_body)

    def do_POST(self) -> None:
        if self.path != "/ask":
            self._send_json(
                404,
                {"error": "Endpoint not found."}
            )
            return

        try:
            content_length = int(
                self.headers.get("Content-Length", "0")
            )
            request_body = self.rfile.read(content_length)
            request_data = json.loads(
                request_body.decode("utf-8")
            )
        except (
            ValueError,
            json.JSONDecodeError,
            UnicodeDecodeError
        ):
            self._send_json(
                400,
                {"error": "Invalid JSON request."}
            )
            return

        question = str(
            request_data.get("question", "")
        ).strip()

        language = str(
            request_data.get("language", "English")
        ).lower()

        if not question:
            self._send_json(
                400,
                {"error": "Question is required."}
            )
            return

        if language.startswith(("tr", "türk")):
            answer = (
                "Bu, yerel mock backend tarafından oluşturulan "
                "test cevabıdır. Frontend API bağlantısı "
                "başarıyla çalışıyor."
            )
        elif language.startswith(("pl", "pol")):
            answer = (
                "To jest odpowiedź testowa z lokalnego mock "
                "backendu. Połączenie API z frontendem działa "
                "poprawnie."
            )
        else:
            answer = (
                "This is a test response from the local mock "
                "backend. The frontend API connection is "
                "working correctly."
            )

        self._send_json(
            200,
            {
                "answer": answer,
                "sources": [
                    {
                        "title": "ATA University test source",
                        "url": "https://akademiata.pl"
                    }
                ]
            }
        )

    def log_message(self, format: str, *args) -> None:
        print(f"[Mock API] {format % args}")


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), MockRAGHandler)

    print(
        f"Mock RAG API is running at "
        f"http://{HOST}:{PORT}/ask"
    )
    print("Press Ctrl+C to stop it.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMock RAG API stopped.")
    finally:
        server.server_close()