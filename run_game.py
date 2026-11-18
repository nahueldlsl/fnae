import http.server
import socketserver
import webbrowser
import os
import sys
import mimetypes

PORT = 8000

# Ensure correct MIME types for modern media
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("video/webm", ".webm")
mimetypes.add_type("audio/wav", ".wav")
mimetypes.add_type("audio/ogg", ".ogg")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("text/css", ".css")

class FNAFRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS and caching headers for smooth performance
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, must-revalidate")
        super().end_headers()

    def log_message(self, format, *args):
        # Clean terminal output
        if "404" in format % args:
            print(f"[404 NOT FOUND] {format % args}")

def find_available_port(start_port=8000):
    import socket
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
            port += 1
    return start_port

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = find_available_port(PORT)
    url = f"http://localhost:{port}/index.html"
    
    print("=" * 60)
    print("      FIVE NIGHTS AT EZEQUIEL'S - SERVIDOR LOCAL")
    print("=" * 60)
    print(f"[*] Servidor iniciado en: {url}")
    print("[*] Abriendo juego en el navegador...")
    print("[*] Presiona CTRL+C para detener el servidor")
    print("=" * 60)

    webbrowser.open(url)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), FNAFRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Servidor detenido con exito.")
            sys.exit(0)

if __name__ == "__main__":
    main()
