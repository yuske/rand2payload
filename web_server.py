#!/usr/bin/env python3

"""Simple static web server with CORS support and verbose logging."""

import argparse
import json
import math
import os
import sys
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from extensions import constraint_rounded
from xs128p import predict_sequence


class StaticRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, verbose=False, **kwargs):
        self.verbose = verbose
        super().__init__(*args, directory=directory, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, HEAD')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Max-Age', '86400')
        super().end_headers()

    def do_OPTIONS(self):
        body = self._read_request_body()
        self._log_request(body)
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        body = self._read_request_body()
        self._log_request(body)
        self._serve_static(send_body=True)

    def do_HEAD(self):
        body = self._read_request_body()
        self._log_request(body)
        self._serve_static(send_body=False)

    # Treat mutating verbs as static file requests for simplicity.
    def do_POST(self):  # noqa: N802
        body = self._read_request_body()
        self._log_request(body)
        parsed = urlparse(self.path)
        if parsed.path == '/predict':
            self._handle_predict(body)
        else:
            self._serve_static(send_body=True)

    def do_PUT(self):  # noqa: N802
        body = self._read_request_body()
        self._log_request(body)
        self._serve_static(send_body=True)

    def do_DELETE(self):  # noqa: N802
        body = self._read_request_body()
        self._log_request(body)
        self._serve_static(send_body=True)

    def do_PATCH(self):  # noqa: N802
        body = self._read_request_body()
        self._log_request(body)
        self._serve_static(send_body=True)

    def _read_request_body(self):
        length = int(self.headers.get('Content-Length', 0) or 0)
        if length <= 0:
            return b''
        return self.rfile.read(length)

    def _log_request(self, body: bytes):
        print(f"{self.command} {self.path}")
        if not self.verbose:
            return
        print('Headers:')
        for header, value in self.headers.items():
            print(f"  {header}: {value}")
        if body:
            try:
                decoded = body.decode('utf-8')
            except UnicodeDecodeError:
                decoded = body.hex()
            print('Body:')
            print(decoded)

    def _serve_static(self, send_body: bool):
        parsed = urlparse(self.path)
        local_path = self.translate_path(parsed.path)
        if os.path.isdir(local_path):
            local_path = os.path.join(local_path, 'index.html')

        if not os.path.exists(local_path):
            self.send_error(HTTPStatus.NOT_FOUND, 'File not found')
            return

        try:
            stat_result = os.stat(local_path)
            self.send_response(HTTPStatus.OK)
            content_type = self.guess_type(local_path)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(stat_result.st_size))
            self.end_headers()
            if send_body:
                with open(local_path, 'rb') as file_obj:
                    self.copyfile(file_obj, self.wfile)
        except OSError as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f'Error reading file: {exc}')

    def log_message(self, format, *args):  # noqa: A003
        # Suppress default stderr logging; custom logging is handled elsewhere.
        if self.verbose:
            super().log_message(format, *args)

    def _handle_predict(self, body: bytes):
        if not body:
            self._send_json({'error': 'Request body must contain a JSON object.'}, HTTPStatus.BAD_REQUEST)
            return
    
        payload = json.loads(body.decode('utf-8'))
        kind = payload.get('kind')
        count = payload.get('count')
        observations = payload.get('observations')
        scale = payload.get('scale') if kind == 'round' else None

        predictions = None
        if kind == 'round':
            effective_scale = scale if scale is not None else self._infer_scale(prepared)
            predictions = predict_sequence(
                observations,
                count,
                browser='chrome',
                # direction='backward',
                constraint_fn=constraint_rounded(effective_scale),
            )
        else:
            predictions = predict_sequence(observations, count, browser='chrome')

        self._send_json(predictions, HTTPStatus.OK)

    def _infer_scale(self, observations):
        max_val = max(observations)
        if max_val < 0:
            raise ValueError('Observations must be non-negative integers.')
        scale = 1
        while scale < max_val:
            scale *= 10
        return max(scale, 1)

    def _send_json(self, payload, status):
        data = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description='Serve files from a directory with CORS enabled.')
    parser.add_argument('--host', default='127.0.0.1', help='Interface to bind (default: 127.0.0.1).')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind (default: 8000).')
    parser.add_argument('--directory', default='public', help='Directory to serve (default: public).')
    parser.add_argument('--verbose', action='store_true', help='Log headers and bodies in addition to the request line.')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    directory = Path(args.directory).resolve()
    if not directory.exists():
        print(f"Error: directory '{directory}' does not exist.", file=sys.stderr)
        return 1

    handler = partial(StaticRequestHandler, directory=str(directory), verbose=args.verbose)
    with ThreadingHTTPServer((args.host, args.port), handler) as httpd:
        host, port = httpd.server_address
        print(f'Serving {directory} at http://{host}:{port} (verbose={args.verbose})')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nShutting down server...')
    return 0


if __name__ == '__main__':
    sys.exit(main())
