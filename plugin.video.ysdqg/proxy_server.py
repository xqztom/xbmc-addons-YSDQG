from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs
from threading import Thread
from spider_config import spiders
from proxy_config import ProxyConfig
from proxy import get_base_url, get_web_url
from danmaku import get_danmaku_ass_by_url, get_danmaku_content_cache
import urllib3
import json
import xbmcaddon
import os
import qrcode
import io

_ADDON = xbmcaddon.Addon()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_cache = {}


class ProxyServer(BaseHTTPRequestHandler):

    def do_GET(self):
        parse_result = urlparse(self.path)
        path = parse_result.path
        if path == '/ping':
            self._handle_ping(parse_result)
        elif path == '/proxy':
            self._handle_proxy(parse_result)
        elif path == '/cache':
            self._handle_get_cache(parse_result)
        elif path == '/danmaku':
            self._handle_danmaku(parse_result)
        elif path == '/danmaku_cache':
            self._handle_danmaku_cache(parse_result)
        elif path == '/aliyundrive_refresh_token':
            self._handle_aliyundrive_refresh_token(parse_result)
        elif path == '/aliyundrive_share_url':
            self._handle_aliyundrive_share_url(parse_result)
        elif path == '/web':
            self._handle_web(parse_result)
        elif path == '/qrcode':
            self._handle_qrcode(parse_result)

    def do_POST(self):
        parse_result = urlparse(self.path)
        path = parse_result.path
        if path == '/cache':
            self._handle_set_cache(parse_result)

    def do_DELETE(self):
        parse_result = urlparse(self.path)
        path = parse_result.path
        if path == '/cache':
            self._handle_del_cache(parse_result)

    def _handle_ping(self, parse_result):
        self.send_response(200)
        self.end_headers()
        self.wfile.write('pong'.encode())

    def _handle_proxy(self, parse_result):
        query = parse_qs(parse_result.query)
        spider_class = query['spider_class'][0]
        func_name = query['func_name'][0]
        params = json.loads(query['params'][0])
        spider = spiders[spider_class]
        getattr(spider, func_name)(self, params)

    def _handle_get_cache(self, parse_result):
        params = parse_qs(parse_result.query)
        key = params['key'][0]

        self.send_response(200)
        self.end_headers()
        if key in _cache:
            self.wfile.write(_cache[key])

    def _handle_set_cache(self, parse_result):
        params = parse_qs(parse_result.query)
        key = params['key'][0]
        content_length = int(self.headers.get('Content-Length', 0))
        value = self.rfile.read(content_length)
        _cache[key] = value

        self.send_response(200)
        self.end_headers()

    def _handle_del_cache(self, parse_result):
        params = parse_qs(parse_result.query)
        key = params['key'][0]
        _cache.pop(key, None)

        self.send_response(200)
        self.end_headers()

    def _handle_danmaku(self, parse_result):
        params = parse_qs(parse_result.query)
        url = params['url'][0]

        self.send_response(200)
        self.end_headers()
        for line in get_danmaku_ass_by_url(url):
            self.wfile.write((line + '\n').encode())

    def _handle_danmaku_cache(self, parse_result):
        self.send_response(200)
        self.end_headers()
        content = get_danmaku_content_cache()
        self.wfile.write(content.encode())

    def _handle_aliyundrive_refresh_token(self, parse_result):
        status_code = 400
        params = parse_qs(parse_result.query)
        aliyundrive_refresh_token = params['aliyundrive_refresh_token'][0]
        if len(aliyundrive_refresh_token) > 0:
            _ADDON.setSettingString('aliyundrive_refresh_token',
                                    aliyundrive_refresh_token)
            status_code = 200
        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def _handle_aliyundrive_share_url(self, parse_result):
        status_code = 400
        params = parse_qs(parse_result.query)
        aliyundrive_share_url = params['aliyundrive_share_url'][0]
        if len(aliyundrive_share_url) > 0:
            _cache['aliyundrive_share_url'] = aliyundrive_share_url.encode()
            status_code = 200
        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def _handle_web(self, parse_result):
        html_path = os.path.join(_ADDON.getAddonInfo('path'), 'web.html')
        with open(html_path, 'r', encoding='utf8') as f:
            content = f.read()
        content = content.replace('{base_url}', get_base_url())
        self.send_response(200)
        self.end_headers()
        self.wfile.write(content.encode())

    def _handle_qrcode(self, parse_result):
        tag = parse_result.query[2:]
        if 'bilibili' in tag:
            url = tag
        else:
            url = get_web_url()
        img = qrcode.make(url)
        bio = io.BytesIO()
        img.save(bio, format='PNG')
        data = bio.getvalue()
        self.send_response(200)
        self.send_header('Content-Type', 'image/png')
        self.end_headers()
        self.wfile.write(data)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


def start_proxy_server():

    def serve_forever():
        try:
            ThreadedHTTPServer(('0.0.0.0', ProxyConfig.PORT),
                               ProxyServer).serve_forever()
        except Exception as e:
            print(e)

    thread = Thread(target=serve_forever)
    thread.daemon = True
    thread.start()
