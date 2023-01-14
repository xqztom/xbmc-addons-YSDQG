"""
获取官源弹幕
"""

from proxy_config import ProxyConfig
import re
import time
import json
import base64
import hashlib
import datetime
import requests
from zlib import decompress
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from cache import get_cache, set_cache, del_cache
import xbmcaddon

_ADDON = xbmcaddon.Addon()

DANMAKU_URL_CACHE_KEY = 'danmaku_url'
DANMAKU_CONTENT_CACHE_KEY = 'danmaku_content'


def del_danmaku_url_cache():
    del_cache(DANMAKU_URL_CACHE_KEY)


def set_danmaku_url_cache(url):
    set_cache(DANMAKU_URL_CACHE_KEY, url)


def get_danmaku_url_cache():
    url = get_cache(DANMAKU_URL_CACHE_KEY)
    del_danmaku_url_cache()
    return url


def set_danmaku_content_cache(content):
    set_cache(DANMAKU_CONTENT_CACHE_KEY, content)


def get_danmaku_content_cache():
    content = get_cache(DANMAKU_CONTENT_CACHE_KEY)
    return content


def get_danmaku_url(url):
    return 'http://{}:{}/danmaku?'.format(
        ProxyConfig.HOST, ProxyConfig.PORT) + urlencode({
            'url': url,
        })


def get_danmaku_cache_url():
    return 'http://{}:{}/danmaku_cache'.format(ProxyConfig.HOST,
                                               ProxyConfig.PORT)


class DanmakuItem(object):

    def __init__(self, time_offset, content):
        self.time_offset = int(time_offset)
        self.content = content.replace('\n', ' ')


def get_danmaku_ass_by_url(url):
    width = 1920
    height = 1080
    bottom_reserved = 540
    style_name = 'YSDQ'
    font_size = _ADDON.getSettingInt('danmaku_font_size')
    duration = _ADDON.getSettingInt('danmaku_duration')
    max_row = int((height - bottom_reserved) / font_size)

    yield '''[Script Info]
ScriptType: v4.00+
PlayResX: %(width)d
PlayResY: %(height)d
Aspect Ratio: %(width)d:%(height)d
Collisions: Normal
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: %(style_name)s, sans-serif, %(font_size)d, &H00FFFFFF, &H00FFFFFF, &H00000000, &H00000000, 0, 0, 0, 0, 100, 100, 0.00, 0.00, 1, 2, 0, 7, 0, 0, 0, 0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
''' % {
        'width': width,
        'height': height,
        'font_size': font_size,
        'style_name': style_name,
    }

    items = get_danmaku_items_by_url(url)
    row_to_next_free = [0 for _ in range(max_row)]
    for item in items:
        item.content = remove_emoji(item.content)
        if len(item.content) == 0:
            continue

        start = int(item.time_offset)
        for row in range(max_row):
            if start >= row_to_next_free[row]:
                end = start + int(duration / width *
                                  (width + len(item.content) * font_size))
                end = start + duration

                row_to_next_free[row] = int(start + len(item.content) *
                                            (duration / (width / font_size)) +
                                            duration / 5)
                yield (
                    'Dialogue: 2,%(start)s.00,%(end)s.00,YSDQ,,0000,0000,0000,,{\\move(%(width)d, %(row_height)d, %(neglen)d, %(row_height)d)}%(content)s'
                    % {
                        'start': str(datetime.timedelta(seconds=start)),
                        'end': str(datetime.timedelta(seconds=end)),
                        'width': width,
                        'row_height': row * font_size,
                        'neglen': int(-len(item.content) * font_size),
                        'content': item.content,
                    })
                break


def get_danmaku_items_by_url(url):
    if '://v.qq.com/' in url:
        return get_qq_danmaku_items(url)
    elif '://www.mgtv.com/' in url:
        return get_mgtv_danmaku_items(url)
    elif '://www.iqiyi.com/' in url:
        return get_iqiyi_danmaku_items(url)
    elif '://v.youku.com/' in url:
        return get_youku_danmaku_items(url)
    elif 'bilibilidanmu' in url:
        return get_bilibili_danmaku_items(url)
    else:
        return []


def get_qq_danmaku_items(url):
    m = re.search(r'://v.qq.com/x/cover/(?:.*/)?(\w+).html', url)
    vid = m.group(1)

    r = requests.get(url)
    m = re.search(r"duration\":(\d+)", r.text)
    video_duration = int(m.group(1))

    for i in range(150000, video_duration * 1000, 30000):
        if i > video_duration * 1000:
            break
        url = 'https://dm.video.qq.com/barrage/segment/{}/t/0/{}/{}'.format(
            vid, i, i + 30000)
        r = requests.get(url)
        if r.status_code != 200:
            break
        for item in r.json()['barrage_list']:
            yield DanmakuItem(int(item['time_offset']) / 1000, item['content'])


def get_mgtv_danmaku_items(url):
    m = re.search(r'://www.mgtv.com/b/(\d+)/(\d+).html', url)
    cid = m.group(1)
    vid = m.group(2)

    r = requests.get(url)
    m = re.search(r",\"(?:(\d{1,2}):)?(\d{1,2}):(\d{1,2})\"", r.text)
    hour = m.group(1)
    min = m.group(2)
    sec = m.group(3)
    video_duration = int(sec)
    video_duration += int(min) * 60
    if hour is not None:
        video_duration += int(hour) * 3600

    time = 0
    while time <= video_duration * 1000:
        r = requests.get('https://galaxy.bz.mgtv.com/rdbarrage',
                         params={
                             'cid': cid,
                             'vid': vid,
                             'time': time,
                         })
        if r.status_code != 200:
            break

        data = r.json()
        if data['status'] != 0:
            break
        items = data['data']['items']
        if items:
            for item in data['data']['items']:
                yield DanmakuItem(int(item['time']) / 1000, item['content'])
        time = data['data']['next']


def get_iqiyi_danmaku_items(url):
    r = requests.get(url)

    m = re.search(r"\"tvId\":(\d+),", r.text)
    tvid = m.group(1)

    m = re.search(r"\"duration\":\"(?:(\d{1,2}):)?(\d{2}):(\d{2})\"", r.text)
    hour = m.group(1)
    min = m.group(2)
    sec = m.group(3)
    video_duration = int(sec)
    video_duration += int(min) * 60
    if hour is not None:
        video_duration += int(hour) * 3600

    for i in range(1, int(video_duration / 300 + 1), 1):
        url = 'https://cmts.iqiyi.com/bullet/{}/{}/{}_300_{}.z'.format(
            tvid[-4:-2], tvid[-2:], tvid, i)
        r = requests.get(url)
        data = decompress(r.content)
        soup = BeautifulSoup(data.decode(), 'html.parser')
        for item in soup.select('bulletinfo'):
            time = int(item.find('showtime').text)
            content = item.find('content').text
            yield DanmakuItem(time, content)


def get_youku_danmaku_items(url):
    s = requests.Session()
    m = re.search(r'://v.youku.com/v_show/id_([\w=]+).html', url)
    vid = m.group(1)
    app_key = '24679788'
    guid = 'NJnMGnrls3wCAXQaiNsMGIsY'

    r = s.get(
        'https://acs.youku.com/h5/mtop.youku.favorite.query.isfavorite/1.0/',
        params={
            'appKey': app_key,
        })
    m = re.search(r'_m_h5_tk=(\w+)_', r.headers['Set-Cookie'])
    token = m.group(1)

    empty_mats = 0
    for mat in range(120):
        t = int(time.time()) * 1000

        msg = base64.b64encode(
            json.dumps({
                "ctime": t,
                "ctype": 10004,
                "cver": "v1.0",
                "guid": guid,
                "mat": mat,
                "mcount": 1,
                "pid": 0,
                "sver": "3.1.0",
                "vid": vid
            }).encode()).decode()

        data = {
            'pid': 0,
            'ctype': 10004,
            'sver': '3.1.0',
            'cver': 'v1.0',
            'ctime': t,
            'guid': guid,
            'vid': vid,
            "mat": mat,
            "mcount": 1,
            "type": 1,
            'msg': msg,
        }
        data['sign'] = hashlib.md5(
            (msg + 'MkmC9SoIw6xCkSKHhJ7b5D2r51kBiREr').encode()).hexdigest()
        data = json.dumps(data)

        params = {
            'jsv': '2.7.0',
            'appKey': app_key,
            't': t,
            'api': 'mopen.youku.danmu.list',
            'v': '1.0',
            'type': 'originaljson',
            'dataType': 'jsonp',
            'timeout': 20000,
            'jsonpIncPrefix': 'utility',
        }
        params['sign'] = hashlib.md5('{}&{}&{}&{}'.format(
            token,
            t,
            app_key,
            data,
        ).encode()).hexdigest()

        r = s.post(
            'https://acs.youku.com/h5/mopen.youku.danmu.list/1.0/',
            data={'data': data},
            params=params,
        )
        result = json.loads(r.json()['data']['result'])
        if result['code'] != 1:
            break

        items = result['data']['result']
        if len(items) == 0:
            empty_mats += 1
            if empty_mats >= 5:
                break
            continue
        else:
            empty_mats = 0
        for item in items:
            yield DanmakuItem(int(item['playat'] / 1000), item['content'])


def get_bilibili_danmaku_items(url):
    src = get_cache(url)
    while src == '':
        src = get_cache(url)
    items = re.findall(r"<d p=.*?</d>", src)
    del_cache(url)
    for item in items:
        time = int(float(re.search(r'\"(.*?)\"', item).group(1).split(',')[0]))
        content =re.search(r'>(.*?)<', item).group(1)
        yield DanmakuItem(time, content)


def remove_emoji(text):
    regrex_pattern = re.compile(
        pattern="["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        # 这条规则不知道为什么会把芒果的弹幕通通过滤掉
        # u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
        "]+",
        flags=re.UNICODE)
    return regrex_pattern.sub(r'', text)


if __name__ == '__main__':
    for l in get_danmaku_ass_by_url(
            'https://www.bilibili.com/bangumi/play/ep518230'):
        print(l)
