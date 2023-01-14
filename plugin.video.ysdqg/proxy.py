from urllib.parse import urlencode
from proxy_config import ProxyConfig
import json
import socket
import time


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def get_proxy_url(spider_class, func_name, params):
    return 'http://{}:{}/proxy?'.format(ProxyConfig.HOST,
                                        ProxyConfig.PORT) + urlencode(
                                            {
                                                'spider_class': spider_class,
                                                'func_name': func_name,
                                                'params': json.dumps(params),
                                            })


def get_base_url():
    return 'http://{}:{}'.format(get_local_ip(), ProxyConfig.PORT)


def get_web_url():
    return 'http://{}:{}/web'.format(get_local_ip(), ProxyConfig.PORT)


def get_qrcode_url(tag, burst_cache=True):
    url = 'http://{}:{}/qrcode'.format(get_local_ip(), ProxyConfig.PORT)
    if burst_cache:
        if tag == 'ali':
            url += '?t={}'.format(time.time())
        else:
            url += '?t={}'.format(tag)
    return url
