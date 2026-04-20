#!/usr/bin/env python
"""Simple HTTP server to serve the HTML dashboard."""

import http.server
import socketserver
from pathlib import Path

PORT = 8001
DASHBOARD_PATH = Path(__file__).parent / "dashboard.html"


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/dashboard.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(DASHBOARD_PATH.read_bytes())
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        print(f"[{self.client_address[0]}] {format % args}")


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"📊 Dashboard server running at http://127.0.0.1:{PORT}")
        print(f"   Make sure the app is running at http://127.0.0.1:8000")
        print(f"   Press Ctrl+C to stop\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✓ Dashboard server stopped")
