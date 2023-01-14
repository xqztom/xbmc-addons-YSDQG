from proxy_config import ProxyConfig
import requests


def get_cache(key):
    r = requests.get('http://{}:{}/cache'.format(ProxyConfig.HOST,
                                                 ProxyConfig.PORT),
                     params={
                         'key': key,
                     })
    return r.text


def set_cache(key, value):
    value = value.encode()
    requests.post('http://{}:{}/cache'.format(ProxyConfig.HOST,
                                              ProxyConfig.PORT),
                  params={
                      'key': key,
                  },
                  data=value,
                  headers={'Content-Length': str(len(value))})


def del_cache(key):
    requests.delete('http://{}:{}/cache'.format(ProxyConfig.HOST,
                                                ProxyConfig.PORT),
                    params={
                        'key': key,
                    })
