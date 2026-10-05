"""Serve the viewer on http://localhost:8765 — run from anywhere: python tools/serve.py"""
import http.server, socketserver, webbrowser, os, sys
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'web')

class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      '.js': 'text/javascript', '.mjs': 'text/javascript', '.wasm': 'application/wasm'}
    def __init__(self, *a, **k): super().__init__(*a, directory=WEB, **k)
    def log_message(self, *a): pass

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', PORT), Handler) as s:
    print(f'Viewer running at http://localhost:{PORT}  (Ctrl+C to stop)')
    webbrowser.open(f'http://localhost:{PORT}')
    try: s.serve_forever()
    except KeyboardInterrupt: print('Stopped.')
