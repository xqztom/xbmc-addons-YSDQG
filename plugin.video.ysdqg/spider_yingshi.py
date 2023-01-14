from spider import Spider, SpiderItemType, SpiderSource, SpiderDanmaku, SpiderItem, SpiderPlayURL
from spider_aliyundrive import SpiderAliyunDrive
import re
import time
import json
import base64
import urllib
import difflib
import hashlib
import requests
import concurrent.futures
from bs4 import BeautifulSoup
from proxy import get_proxy_url
from urllib.parse import urlparse
from danmaku import get_danmaku_url
from cache import get_cache, set_cache, del_cache
from utils import get_image_path
import xbmcaddon

_ADDON = xbmcaddon.Addon()

base_params = {
    'pcode': '010110005',
    'version': '2.0.5',
    'devid': hashlib.md5(str(time.time()).encode()).hexdigest(),
    'sys': 'android',
    'sysver': 11,
    'brand': 'google',
    'model': 'Pixel_3_XL',
    'package': 'com.sevenVideo.app.android'
}
base_headers = {
    'User-Agent': 'okhttp/3.12.0',
}

try:
    bbexists = True
    from spider_bilibili import Spiderbilibili
except Exception:
    bbexists = False

bbhide = Spiderbilibili.hide(Spiderbilibili())
#bbhide = False

jsonurl = _ADDON.getSettingString('aliyundrive_refresh_token')
#jsonurl = 'https://mpimg.cn/down.php/c8f9e6ed2446c6d5c6973df99ff2fbe1.json'
if jsonurl.startswith('http'):
    try:
        jr = requests.get(jsonurl, verify=False, timeout=5)
        jdata = jr.json()
    except Exception:
        jdata = {}
else:
    jdata = {}
if 'YSDQ' in jdata and 'speedLimit' in jdata['YSDQ']:
    spLimit = jdata['YSDQ']['speedLimit']
else:
    spLimit = '512K'
if 'YSDQ' in jdata and 'thlimit' in jdata['YSDQ']:
    thlimit = jdata['YSDQ']['thlimit']
else:
    thlimit = 5

class Spideryingshi(Spider):

    def name(self):
        return '影视'

    def logo(self):
        return get_image_path('yingshi.png')

    def hide(self):
        return not _ADDON.getSettingBool('data_source_yingshi_switch')

    def is_searchable(self):
        return True

    def list_items(self, parent_item=None, page=1):
        if parent_item is None:
            items = []
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id='豆瓣高分',
                    name='高分电影',
                    params={
                        'type': 'category',
                        'pf': 'db'
                    },
                ))
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id='热门',
                    name='电影',
                    params={
                        'type': 'category',
                        'pf': 'db'
                    },
                ))
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id='剧集',
                    name='剧集',
                    params={
                        'type': 'category',
                        'pf': 'db'
                    },
                ))
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id='综艺',
                    name='综艺',
                    params={
                        'type': 'category',
                        'pf': 'db'
                    },
                ))
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id='日本动画',
                    name='动画',
                    params={
                        'type': 'category',
                        'pf': 'db'
                    },
                ))
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id='纪录片',
                    name='纪录片',
                    params={
                        'type': 'category',
                        'pf': 'db'
                    },
                ))
            return items, False
        elif parent_item['params']['type'] == 'category':
            if parent_item['params']['pf'] == 'db':
                if page < 10:
                    has_next_page = True
                else:
                    has_next_page = False
                items = []
                header = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
                }
                tag = parent_item['id']
                idname = parent_item['name']
                if idname == '剧集':
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.Directory,
                            id='全部剧集',
                            name='全部剧集',
                            params={
                                'type': 'category',
                                'pf': 'db'
                            },
                        ))
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.Directory,
                            id='国产剧',
                            name='国产剧',
                            params={
                                'type': 'category',
                                'pf': 'db'
                            },
                        ))
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.Directory,
                            id='美剧',
                            name='美剧',
                            params={
                                'type': 'category',
                                'pf': 'db'
                            },
                        ))
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.Directory,
                            id='日剧',
                            name='日剧',
                            params={
                                'type': 'category',
                                'pf': 'db'
                            },
                        ))
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.Directory,
                            id='韩剧',
                            name='韩剧',
                            params={
                                'type': 'category',
                                'pf': 'db'
                            },
                        ))
                    return items, False
                elif '电影' in idname:
                    type = 'movie'
                    url = 'https://movie.douban.com/j/search_subjects?type={}&tag={}&page_limit=50&page_start={}'.format(
                        type, tag, (page - 1) * 50)
                    r = requests.get(url, headers=header)
                    data = json.loads(r.text)['subjects']
                elif idname in ['综艺', '动画', '纪录片', '日剧', '韩剧', '美剧', '国产剧']:
                    type = 'tv'
                    url = 'https://movie.douban.com/j/search_subjects?type={}&tag={}&page_limit=50&page_start={}'.format(
                        type, tag, (page - 1) * 50)
                    r = requests.get(url, headers=header)
                    data = json.loads(r.text)['subjects']
                elif idname == '全部剧集':
                    type = 'tv'
                    data = []
                    contents = []
                    infos = ['国产剧', '美剧', '日剧', '韩剧']
                    with concurrent.futures.ThreadPoolExecutor(max_workers=thlimit) as executor:
                        db = []
                        for info in infos:
                            url = 'https://movie.douban.com/j/search_subjects?type={}&tag={}&page_limit=50&page_start={}'.format(type, info, (page - 1) * 50)
                            future = executor.submit(self.getData, url, header, '', info)
                            db.append(future)
                        for future in concurrent.futures.as_completed(db, timeout=10):  # 并发执行
                            contents.append(future.result())
                    for content in contents:
                        data = data + json.loads(content)['subjects']
                    data.sort(key=lambda i: i['is_new'], reverse=True)
                for video in data:
                    vid = video['id']
                    cover = video['cover']
                    name = video['title'].strip()
                    if '电影' in idname:
                        remark = video['rate']
                        if remark != '':
                            remark = '豆瓣评分：{}分'.format(remark)
                        else:
                            remark = '完结'
                    else:
                        remark = video['episodes_info']
                        if remark == '':
                            remark = video['rate']
                            if remark != '':
                                remark = '豆瓣评分：{}分'.format(remark)
                            else:
                                remark = '完结'
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.Search,
                            name='[{0}]/{1}'.format(remark, name),
                            id=vid,
                            cover=cover,
                            params={
                                'pf': 'db'
                            },
                        ))
                return items, has_next_page
            else:
                return SpiderAliyunDrive.list_items(SpiderAliyunDrive(), parent_item, page)
        elif parent_item['params']['type'] == 'video':
            if parent_item['params']['pf'] == 'qq':
                ts = int(time.time())
                params = base_params.copy()
                params['ids'] = parent_item['id']
                params['sj'] = ts
                headers = base_headers.copy()
                headers['t'] = str(ts)
                url = 'http://api.kunyu77.com/api.php/provide/videoDetail'
                headers['TK'] = self._get_tk(url, params, ts)
                r = requests.get(url, params=params, headers=headers)
                detail = r.json()['data']
                url = 'http://api.kunyu77.com/api.php/provide/videoPlaylist'
                headers['TK'] = self._get_tk(url, params, ts)
                r = requests.get(url, params=params, headers=headers)
                episodes = r.json()['data']['episodes']
                items = []
                for episode in episodes:
                    sources = []
                    danmakus = []
                    for playurl in episode['playurls']:
                        sources.append(
                            SpiderSource(
                                playurl['playfrom'],
                                {
                                    'playfrom': playurl['playfrom'],
                                    'url': playurl['playurl'],
                                    'pf': 'qq'
                                },
                            ))
                        if playurl['playfrom'] in ['qq', 'mgtv', 'qiyi', 'youku', 'bilibili']:
                            if playurl['playfrom'] != 'bilibili':
                                danmu = playurl['playurl']
                            else:
                                r = requests.get(url=playurl['playurl'], headers=headers, timeout=5)
                                m = re.search(r'"cid":(.*?),', r.text)
                                oid = m.group(1)
                                if not oid or oid == '0':
                                    m = re.search(r'bilivideo.com/upgcxcode/\d+/\d+(?:/(\d+)){2}', r.text)
                                    oid = m.group(1)
                                danmu = 'bilibilidanmu' +oid
                            danmakus.append(
                                SpiderDanmaku(
                                    playurl['playfrom'],
                                    get_danmaku_url(danmu),
                                )
                            )
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.File,
                            name=episode['title'].strip(),
                            cover=detail['videoCover'],
                            description=detail['brief'].replace('\u3000', '').replace('<p>', '').replace('</p>','').strip(),
                            cast=detail['actor'].replace(' ', '').split('/'),
                            director=detail['director'],
                            area=detail['area'].strip(),
                            year=int(detail['year'].strip()),
                            sources=sources,
                            danmakus=danmakus,
                            params={
                                'speedtest': spLimit,
                                'thlimit': thlimit,
                            }
                        ))
                return items, False
            if parent_item['params']['pf'] == 'bw':
                items = []
                url = 'https://beiwo360.com{}'.format(parent_item['id'])
                header = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
                    "Referer": 'https://beiwo360.com/'
                }
                r = requests.get(url, headers=header)
                soup = BeautifulSoup(r.text, 'html.parser')
                cover = parent_item['cover']
                desc = soup.select('span.sketch.content')
                if desc != []:
                    desc = desc[0].get_text().strip().replace('\u3000\u3000', '\n')
                else:
                    desc = soup.select('div.hl-content-wrap > span.hl-content-text')[0].get_text().strip().replace('\u3000\u3000', '\n')
                episinfos = soup.select('div.tab-pane.fade.clearfix > ul')
                if episinfos == []:
                    episinfos = soup.select('div.hl-list-wrap > ul#hl-plays-list')
                numepis = []
                episList = []
                titleInfos = []
                titleList = re.findall(r'playlist\d+\" data-toggle=\"tab\">(.*?)</a>', r.text)
                if titleList == []:
                    titleList = re.findall(r'class=\"hl-tabs-btn hl-slide-swiper active\".*?<i class=\"iconfont hl-icon-shipin\"></i>(.*?)</a>', r.text)
                i = 0
                for episinfo in episinfos:
                    lennp = len(episinfo.select('li'))
                    numepis.append(lennp)
                    episList.append(episinfo.select('li'))
                    titleInfos.append([lennp, titleList[i].strip()])
                    i = i + 1
                episList.sort(key=lambda i: len(i), reverse=True)
                titleInfos.sort(key=lambda i:i[0], reverse=True)
                maxepis = max(numepis)
                episodes = episList[0]
                a = 0
                b = 0
                for episode in episodes:
                    sources = []
                    i = 0
                    name = episode.find('a').get_text().strip()
                    for epis in episList:
                        if i == 0:
                            k = a
                        else:
                            k = b
                        if k >= len(epis):
                            continue
                        if epis[k] == episode:
                            sepisode = episode
                        else:
                            sepisode = epis[b]
                        title = titleInfos[i][1].strip('&nbsp;')
                        sname = sepisode.select('a')[0].get_text().strip()
                        if len(sepisode) == maxepis or '1080P' in sname or 'HD' in sname or '正片' in sname or '国语' in sname or '粤语' in sname or '韩语' in sname or '英语' in sname or '中字' in sname:
                            ratio = 1
                        else:
                            ratio = difflib.SequenceMatcher(None, name, sname).ratio()
                        if ratio < 0.1 or '预告' in sname or '回顾' in sname:
                            b = b - 1
                            if b < 0:
                                b = 0
                            continue
                        purl = sepisode.find('a').get('href')
                        sources.append(
                            SpiderSource(
                                title,
                                {
                                    'playfrom': '',
                                    'pf': 'bw',
                                    'url': purl,
                                },
                            ))
                        i = i + 1
                    a = a + 1
                    b = b + 1
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.File,
                            name=name,
                            cover=cover,
                            description=desc,
                            sources=sources,
                            params={
                                'speedtest': spLimit,
                                'thlimit': thlimit,
                            }
                        ))
                return items, False
            if parent_item['params']['pf'] == 'ik':
                items = []
                header = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
                }
                url = 'https://ikan6.vip/voddetail/{0}/'.format(parent_item['id'])
                r = requests.get(url, headers=header)
                soup = BeautifulSoup(r.text, 'html.parser')
                cover = parent_item['cover']
                infos = soup.select('div.myui-content__detail > p.data')
                yainfo = infos[0].get_text().replace('\n\n', '\n').replace('\t', '').strip('\n').split('\n')
                year = int(yainfo[2].replace('年份：', ''))
                area = yainfo[1].replace('地区：', '')
                cast = infos[2].get_text().replace('主演：', '').strip('\xa0').split('\xa0')
                dire = infos[3].get_text().replace('导演：', '').replace('\xa0',',')
                desc = soup.select('div.col-pd.text-collapse.content > span.data')[0].get_text().replace('\n', '').replace('\u3000', '').replace('：', '').replace('详情', '').replace('\xa0', '').replace(' ', '')
                episinfos = soup.select('div.tab-content.myui-panel_bd > div')
                numepis = []
                episList = []
                titleInfos = []
                titleList = re.findall(r'<a href=\"#playlist\d\" data-toggle=\"tab\">(.*?)</a>',r.text)
                i = 0
                for episinfo in episinfos:
                    lennp = len(episinfo.select('ul > li'))
                    numepis.append(lennp)
                    episList.append(episinfo.select('ul > li'))
                    titleInfos.append([lennp, titleList[i].strip()])
                    i = i + 1
                episList.sort(key=lambda i: len(i), reverse=True)
                titleInfos.sort(key=lambda i: (i)[0], reverse=True)
                maxepis = max(numepis)
                episodes = episList[0]
                a = 0
                b = 0
                for episode in episodes:
                    sources = []
                    i = 0
                    name = episode.select('a')[0].get_text().strip()
                    for epis in episList:
                        if i == 0:
                            k = a
                        else:
                            k = b
                        if k >= len(epis):
                            continue
                        if epis[k] == episode:
                            sepisode = episode
                        else:
                            sepisode = epis[b]
                        title = titleInfos[i][1]
                        sname = sepisode.select('a')[0].get_text().strip()
                        if len(sepisode) == maxepis or '1080P' in sname or 'HD' in sname or '正片' in sname or '国语' in sname or '粤语' in sname or '韩语' in sname or '英语' in sname or '中字' in sname:
                            ratio = 1
                        else:
                            ratio = difflib.SequenceMatcher(None, name, sname).ratio()
                        if ratio < 0.1 or '预告' in sname or '回顾' in sname:
                            b = b - 1
                            continue
                        purl = re.search(r'/vodplay/(.*?)/', sepisode.select('a')[0].get('href')).group(1)
                        sources.append(
                            SpiderSource(
                                title,
                                {
                                    'playfrom': '',
                                    'pf': 'ik',
                                    'url': purl,
                                },
                            ))
                        i = i + 1
                    a = a + 1
                    b = b + 1
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.File,
                            name=name,
                            cover=cover,
                            description=desc,
                            cast=cast,
                            director=dire,
                            area=area,
                            year=int(year),
                            sources=sources,
                            params={
                                'speedtest': spLimit,
                                'thlimit': thlimit,
                            }
                        ))
                return items, False
            if parent_item['params']['pf'] == 'ld':
                items = []
                header = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
                }
                url = 'https://ldtv.top/index.php/vod/detail/id/{}.html'.format(parent_item['id'])
                r = requests.get(url, headers=header)
                soup = BeautifulSoup(r.text, 'html.parser')
                cover = parent_item['cover']
                infos = soup.select('div.module-info-items > div')
                cast = infos[2].get_text().replace('主演：', '').strip('\n').strip(' ').strip('/').split('/')
                dire = infos[1].get_text().replace('导演：', '').strip('\n').strip(' ').strip('/')
                desc = infos[0].get_text().strip('\n').replace('　　','\n').strip()
                episinfos = soup.select('div.module > div.module-list')
                numepis = []
                episList = []
                titleInfos = []
                titleList = soup.select('div.module-tab-items-box.hisSwiper > div > span')
                i = 0
                for episinfo in episinfos:
                    lennp = len(episinfo.select('div.module-play-list-content > a'))
                    numepis.append(lennp)
                    episList.append(episinfo.select('div.module-play-list-content > a'))
                    titleInfos.append([lennp, titleList[i].get_text().strip()])
                    i = i + 1
                episList.sort(key=lambda i: len(i), reverse=True)
                titleInfos.sort(key=lambda i: (i)[0], reverse=True)
                maxepis = max(numepis)
                episodes = episList[0]
                a = 0
                b = 0
                for episode in episodes:
                    sources = []
                    i = 0
                    name = episode.select('span')[0].get_text().strip()
                    for epis in episList:
                        if i == 0:
                            k = a
                        else:
                            k = b
                        if k >= len(epis):
                            continue
                        if epis[k] == episode:
                            sepisode = episode
                        else:
                            sepisode = epis[b]
                        title = titleInfos[i][1]
                        sname = sepisode.select('span')[0].get_text().strip()
                        if len(sepisode) == maxepis or '1080P' in sname or 'HD' in sname or '正片' in sname or '国语' in sname or '粤语' in sname or '韩语' in sname or '英语' in sname or '中字' in sname:
                            ratio = 1
                        else:
                            ratio = difflib.SequenceMatcher(None, name, sname).ratio()
                        if ratio < 0.1 or '预告' in sname or '回顾' in sname:
                            b = b - 1
                            if b < -1:
                                b = -1
                            continue
                        purl = sepisode.get('href')
                        sources.append(
                            SpiderSource(
                                title,
                                {
                                    'playfrom': '',
                                    'pf': 'ld',
                                    'url': purl,
                                },
                            ))
                        i = i + 1
                    a = a + 1
                    b = b + 1
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.File,
                            name=name,
                            cover=cover,
                            description=desc,
                            cast=cast,
                            director=dire,
                            sources=sources,
                            params={
                                'speedtest': spLimit,
                                'thlimit': thlimit,
                            }
                        ))
                return items, False
            if parent_item['params']['pf'] == 'ps':
                if not parent_item['id'].startswith('http'):
                    header = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
                        'Referer': 'https://www.alipansou.com' + '/s/' + parent_item['id']
                    }
                    r = requests.get('https://www.alipansou.com' + '/cv/' + parent_item['id'], allow_redirects=False, headers=header)
                    url = re.search(r'href=\"(.*)\"', r.text).group(1)
                    parent_item['id'] = url
                return SpiderAliyunDrive.list_items(SpiderAliyunDrive(), parent_item, page)
            if parent_item['params']['pf'] == 'ys' or parent_item['params']['pf'] == 'xzt':
                return SpiderAliyunDrive.list_items(SpiderAliyunDrive(), parent_item, page)
            if parent_item['params']['pf'] == 'zzy':
                regex_url = re.compile(r'https://www.aliyundrive.com/s/[^"]+')
                if not 'zzy' in self.ckList:
                    self.getCookie('zzy')
                    zzycookie = self.ckList['zzy']
                r = requests.get('https://zhaoziyuan.la/' + parent_item['id'], cookies=zzycookie)
                m = regex_url.search(r.text)
                url = m.group().replace('\\', '')
                parent_item['id'] = url
                return SpiderAliyunDrive.list_items(SpiderAliyunDrive(), parent_item, page)
            if parent_item['params']['pf'] == 'ali':
                return SpiderAliyunDrive.list_items(SpiderAliyunDrive(), parent_item, page)
            if bbexists is True and parent_item['params']['pf'] == '影视':
                return Spiderbilibili.list_items(Spiderbilibili(), parent_item, page)
        else:
            return [], False

    def resolve_play_url(self, source_params):
        if not source_params['pf'] in ['ali', '影视']:
            return SpiderPlayURL(source_params['url'])
        if source_params['pf'] == 'ali':
            return SpiderAliyunDrive.resolve_play_url(SpiderAliyunDrive(), source_params)
        if bbexists is True and source_params['pf'] == '影视':
            return Spiderbilibili.resolve_play_url(Spiderbilibili(), source_params)

    def checkPurl(self, source_params, tag):
        try:
            if source_params['pf'] == 'qq':
                url = source_params['url']
                headers = {}
                if source_params['playfrom'] != 'ppayun':
                    if 'QiQi' in jdata and len(jdata['QiQi']) != 0 and 'jx' in jdata['QiQi'][0] and 'jxfrom' in jdata['QiQi'][0] and 'gs' in jdata['QiQi'][0] and 'erro' in jdata['QiQi'][0]:
                        jxinfos = jdata['QiQi']
                        for jxinfo in jxinfos:
                            jx = jxinfo['jx']
                            jxfrom = jxinfo['jxfrom']
                            gs = jxinfo['gs'].strip().split(',')
                            erro = jxinfo['erro']
                            jurl = jx + url
                            r = requests.get(jurl)
                            if erro in r.text and erro != '':
                                break
                            url = r.json()
                            for i in range(0, len(gs)):
                                url = url[gs[i]]
                            if url == '':
                                break
                            tspList = self.readM3U8(url, headers, tag)
                            purl = tspList[1]
                            tspDict  = tspList[0]
                            if tspList[2] == 'proxy':
                                purl = get_proxy_url(Spideryingshi.__name__,self.proxy_m3u8.__name__,{'url': purl,'headers': headers})
                            return [tspDict, purl]
                    else:
                        return [{tag: 0}, '']
                else:
                    tspList = self.readM3U8(url, headers, tag)
                    purl = get_proxy_url(Spideryingshi.__name__, self.proxy_m3u8.__name__,{'url': tspList[1], 'headers': headers})
                    tspDict = tspList[0]
                    return [tspDict, purl]
            if source_params['pf'] == 'ik':
                header = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
                    "Referer": "https://ikan6.vip/"
                }
                url = 'https://ikan6.vip/vodplay/{0}/'.format(source_params['url'])
                r = requests.get(url, verify=False, headers=header)
                cookie = r.cookies
                info = json.loads(re.search(r'var player_data=(.*?)</script>', r.text).group(1))
                string = info['url'][8:len(info['url'])]
                substr = base64.b64decode(string).decode('UTF-8')
                str = substr[8:len(substr) - 8]
                if 'Ali' in info['from']:
                    url = 'https://cms.ikan6.vip/ali/nidasicaibudaowozaina/nicaibudaowozaina.php?url={0}'.format(str)
                else:
                    url = 'https://cms.ikan6.vip/nidasicaibudaowozaina/nicaibudaowozaina.php?url={0}'.format(str)
                r = requests.get(url, verify=False, headers=header, cookies=cookie)
                randomurl = re.search(r"getrandom\(\'(.*?)\'", r.text).group(1)
                pstring = randomurl[8:len(randomurl)]
                psubstr = base64.b64decode(pstring).decode('UTF-8')
                purl = urllib.parse.unquote(psubstr[8:len(psubstr) - 8])
                pheader = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
                }
                if 'Ali' in info['from']:
                    tspList = self.readM3U8(purl, pheader, tag)
                    tspDict = tspList[0]
                    purl = tspList[1]
                    return [tspDict, purl]
                else:
                    tspList = self.readM3U8(purl, header, tag)
                    purl = tspList[1]
                    tspDict = tspList[0]
                    purl = get_proxy_url(Spideryingshi.__name__, self.proxy_m3u8.__name__, {'url': purl, 'headers': header})
                    return [tspDict, purl]
            if source_params['pf'] == 'bw':
                header = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
                    "Referer": "https://beiwo360.com/"
                }
                url = 'https://beiwo360.com/{0}'.format(source_params['url'])
                r = requests.get(url, headers=header)
                jo = json.loads(re.search(r'var player_aaaa=({.*?)</script>', r.text).group(1))
                purl = jo['url']
                tspList = self.readM3U8(purl, header, tag)
                purl = tspList[1]
                tspDict = tspList[0]
                if tspList[2] == 'proxy':
                    del header['Referer']
                    purl = get_proxy_url(Spideryingshi.__name__, self.proxy_m3u8.__name__,{'url': purl, 'headers': header})
                return [tspDict, purl]
            if source_params['pf'] == 'ld':
                header = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
                }
                url = 'https://ldtv.top{0}'.format(source_params['url'])
                r = requests.get(url, headers=header)
                jo = json.loads(re.search(r'var player_aaaa=({.*?)</script>', r.text).group(1))
                if jo['from'] in ['qq', 'youku', 'qiyi', 'mgtv', 'bilibili']:
                    url = 'https://ldtv.top/addons/dp/player/dp.php?key=0&from=&id={0}&api=&url={1}'.format(jo['id'],
                                                                                                            jo['url'])
                    r = requests.get(url, headers=header)
                    purl = re.search(r'url\": \"(.*?)\"', r.text)
                    if not purl is None:
                        purl = purl.group(1)
                elif jo['from'] == 'rx':
                    url = 'https://ldtv.top/addons/dp/player/dp.php?key=0&from={}&id={}&api=&url={}&jump='.format(
                        jo['from'], jo['id'], jo['url'])
                    r = requests.get(url, headers=header)
                    purl = re.search(r'url\": \"(.*?)\"', r.text)
                    if not purl is None:
                        purl = purl.group(1)
                else:
                    url = 'https://ldtv.top/addons/dp/player/dp.php?key=0&from={}{}&id={}&api=&url={}&jump='.format(
                        jo['from'], jo['from'], jo['id'], jo['url'])
                    r = requests.get(url, headers=header)
                    purl = re.search(r'url\": \"(.*?)\"', r.text)
                    if not purl is None:
                        purl = purl.group(1)
                if 'rongxing' in purl or 'rdxnnnnnnnn' in purl:
                    r = requests.get(purl, headers=header, allow_redirects=False)
                    if 'Location' in r.headers:
                        purl = r.headers['Location']
                if jo['from'] == 'BYGA' or jo['from'] == 'RRYS' or jo['from'] == 'mgtv':
                    purl = purl + '@@@False'
                tspList = self.readM3U8(purl, header, tag)
                purl = tspList[1]
                tspDict  = tspList[0]
                if tspList[2] == 'proxy':
                    purl = get_proxy_url(Spideryingshi.__name__, self.proxy_m3u8.__name__,{'url': purl, 'headers': header})
                return [tspDict, purl]
        except Exception as e:
            return [{tag: 0}, '']

    def sub(self, string, p, c):
        new = []
        for s in string:
            new.append(s)
        new[p] = c
        return ''.join(new)

    def readM3U8(self, url, header, tag):
        url = url.strip('/')
        if '@@@' in url:
            url = url.split('@@@')[0]
        s_url = None
        try:
            response = requests.get(url, headers=header, stream=True, allow_redirects=False, verify=False, timeout=5)
            if 'video' in response.headers['Content-Type']:
                response.close()
                return self.SpeedInfo(url, header, tag)
            if 'Location' in response.headers and response.text == '':
                url = response.headers['Location']
                response.close()
                response = requests.get(url, headers=header, allow_redirects=False, verify=False, timeout=5)
            response.encoding = 'utf-8'
            str = response.text
            if str.find(".jpg") != -1 or str.find(".jepg") != -1 or str.find(".ico") != -1 or str.find(".icon") != -1 or str.find(".bmp") != -1 or str.find(".png") != -1 :
                proxy = 'proxy'
            else:
                proxy = 'nomral'
            result = urlparse(url)
            url_tou = result[0] + '://' + result[1]
            # 获取m3u8中的片段ts文件
            # 需要替换 ../
            list = str.split("\n");
            for str in list:
                if str.find(".ts") != -1 or str.find(".jpg") != -1 or str.find(".jepg") != -1 or str.find(".ico") != -1 or str.find(".icon") != -1 or str.find(".bmp") != -1 or str.find(".png") != -1:
                    # 特殊格式==>回退目录
                    if str.find("../../../../..") != -1:
                        s_url = str.replace("../../../../..", url_tou)
                    # 普通格式，直接替换，如果ts文件的开头是/则表示根目录
                    else:
                        if str[0:1] == '/':
                            s_url = self.sub(str, 0, url_tou + "/").strip('\r').strip('\n').strip()
                        elif str.startswith('http'):
                            s_url = str.strip('\r').strip('\n').strip()
                        else:
                            pos = url.rfind("/")
                            s_url = url.replace(url[pos:], "/" + str).strip('\r').strip('\n').strip()
                    break
                elif str.find(".m3u") != -1:
                    if str[0:1] == '/':
                        s_url = self.sub(str, 0, url_tou + "/").strip('\r').strip('\n').strip()
                    elif str.startswith('http'):
                        s_url = str.strip('\r').strip('\n').strip()
                    else:
                        pos = url.rfind("/")
                        s_url = url.replace(url[pos:], "/" + str).strip('\r').strip('\n').strip()
                    return self.readM3U8(s_url, header, tag)
                elif str.startswith("http"):
                    s_url = str
                    return self.SpeedInfo(s_url, header, tag, url, proxy)
            return self.SpeedInfo(s_url, header, tag, url, proxy)
        except Exception as e:
            return {tag: 0}

    def SpeedInfo(self, url, header, tag, purl, proxy):
        header.update({'Proxy-Connection':'keep-alive'})
        r = requests.get(url, stream=True, headers=header, verify=False, timeout=5)
        count = 0
        count_tmp = 0
        stime = time.time()
        i = 0
        speed = 0
        for chunk in r.iter_content(chunk_size=40960):
            if chunk:
                if i == 2:
                    break
                count += len(chunk)
                sptime = time.time() - stime
                if count == int(r.headers['content-length']):
                    speed = int((count - count_tmp) / sptime)
                if sptime > 0:
                    speed = int((count - count_tmp)/sptime)
                    stime = time.time()
                    count_tmp = count
                    i = i + 1
        return [{tag: speed}, purl, proxy]

    def search(self, keyword, page=1):
        items = []
        if 'YSDQ' in jdata and 'searchList' in jdata['YSDQ']:
            strsws = jdata['YSDQ']['searchList'].strip().strip(',').strip('\n')
        else:
            strsws ="qq,ik,bw,ld,bb,ps,ys,zzy,xzt"
        if page > 1:
            strsws = get_cache('strsws')
            del_cache('strsws')
        sws = strsws.split(',')
        if bbhide is True or bbexists is False:
            if 'bb' in sws:
                sws.remove('bb')
        contents = []
        keyword = keyword.replace('/', '%2F')
        with concurrent.futures.ThreadPoolExecutor(max_workers=thlimit) as executor:
            searchList = []
            try:
                for sw in sws:
                    future = executor.submit(self.runSearch, keyword, sw, page)
                    searchList.append(future)
                for future in concurrent.futures.as_completed(searchList, timeout=10):  # 并发执行
                    contents.append(future.result())
            except Exception:
                executor.shutdown(wait=False)
        nextpageList = []
        for content in contents:
            key = list(content.keys())[0]
            infos = content[key]
            items = items + content[key][0]
            nextpageList.append(infos[1])
            if not infos[1]:
                strsws = strsws.replace(key, '').replace(',,', ',').strip(',')
        if True in nextpageList:
            has_next_page = True
        else:
            has_next_page = False
        del_cache('strsws')
        set_cache('strsws',strsws)
        items.sort(key=lambda i: i['params']['num'], reverse=False)
        return items, has_next_page

    def runSearch(self, keyword, tag, page):
        try:
            funList = dir(Spideryingshi)
            defname = 'self.search' + tag
            if defname.replace('self.', '') in funList and tag != '':
                result = eval(defname)(keyword, tag, page)
            return result
        except Exception:
            return {tag: [[], False]}

    def searchqq(self, keyword, tag, page):
        items = []
        keyword = keyword.replace('/', '%2F')
        url = 'http://api.kunyu77.com/api.php/provide/searchVideo'
        ts = int(time.time())
        params = base_params.copy()
        params['sj'] = ts
        params['searchName'] = keyword
        params['pg'] = page
        headers = base_headers.copy()
        headers['t'] = str(ts)
        headers['TK'] = self._get_tk(url, params, ts)
        r = requests.get(url, params=params, headers=headers, timeout=5)
        data = r.json()['data']
        if len(data) == 20:
            nexpage = True
        else:
            nexpage = False
        for video in data:
            remark = video['msg'].strip()
            if remark == '':
                remark = 'HD'
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    name='七七：[{0}]/{1}'.format(remark.strip(), video['videoName'].strip()),
                    id=video['id'],
                    cover=video['videoCover'],
                    description=video['brief'].replace('<p>', '').replace('</p>','').replace('\r','').replace('&nbsp; ','').replace('&\u3000','').strip(),
                    cast=video['starName'].replace(' ','').replace('声优','').replace(':',',').replace('：',',').replace(' ',',').strip(',').split(','),
                    year=int(video['year']),
                    params={
                        'type': 'video',
                        'pf': 'qq',
                        'num': 1
                    },
                ))
        return {tag: [items, nexpage]}

    def searchik(self, keyword, tag, page):
        items = []
        keyword = keyword.replace('/', '%2F')
        header = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
        }
        url = 'https://ikan6.vip/vodsearch/-------------/?wd={0}&submit='.format(keyword)
        verifyCode, session = self.verifyCode('https://ikan6.vip/index.php/verify/index.html?', 'https://ikan6.vip/index.php/ajax/verify_check?type=search&verify=')
        if verifyCode is False:
            return {tag: [items, False]}
        if not session:
            return {tag: [items, False]}
        r = session.get(url, headers=header, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        data = soup.select('ul#searchList > li')
        for video in data:
            sid = re.search(r'/voddetail/(.*?)/', video.find('a').get('href')).group(1)
            name = video.find('h4').get_text().strip()
            year = int(video.select('div.detail > p')[2].get_text().split('年份：')[1])
            description = video.select('div.detail > p')[3].get_text().replace('简介：', '').replace('详情 >', '')
            cover = video.select('div.thumb > a')[0].get('data-original')
            remark = video.select('div.thumb > a')[0].get_text().strip().strip('\n').split('\n')[-1].strip()
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    name='爱看：[{0}]/{1}'.format(remark, name),
                    id=sid,
                    cover=cover,
                    description=description,
                    year=int(year),
                    params={
                        'type': 'video',
                        'pf': 'ik',
                        'num': 2
                    },
                ))
        return {tag: [items, False]}

    def searchbw(self, keyword, tag, page):
        items = []
        keyword = keyword.replace('/', '%2F')
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
            "Referer": "https://beiwo360.com/"
        }
        url = 'https://beiwo360.com/bws/{}----------{}---/'.format(keyword, page)
        r = requests.get(url, headers=header, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        data = soup.select('ul#searchList> li')
        mpg = soup.select('ul.myui-page.text-center.clearfix > li')
        if data == []:
            data = soup.select('ul.hl-one-list > li.hl-list-item')
            mpg = soup.select('ul.hl-page-wrap > li')
        if mpg != []:
            maxpage = int(re.search(r'-(\d+)-', mpg[-1].find('a').get('href')).group(1))
        else:
            maxpage = 1

        for video in data:
            sid = video.find('a').get('href')
            remark = video.select('a > span.pic-text')
            if remark != []:
                remark = remark[0].get_text().strip().replace(' ','|')
            else:
                remark = video.select('div.hl-pic-text')[0].get_text().strip().replace(' ','|')
            name = video.find('a').get('title').strip()
            cover = video.find('a').get('data-original')
            desc = video.select('p.hidden-xs')
            if desc != []:
                desc = desc[0].get_text().strip().replace('简介：', '').replace('详情 >', '')
            else:
                desc = video.select('div.hl-item-content > p.hl-item-sub.hl-text-muted.hl-lc-2')[0].get_text().replace('\u3000', '').replace('简介：', '').replace('详情 >', '').strip()
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    name='被窝：[{0}]/{1}'.format(remark, name),
                    id=sid,
                    cover=cover,
                    description=desc,
                    params={
                        'type': 'video',
                        'pf': 'bw',
                        'num': 3
                    },
                ))
        if page < maxpage:
            nexpage = True
        else:
            nexpage = False
        return {tag: [items, nexpage]}

    def searchld(self, keyword, tag, page):
        items = []
        keyword = keyword.replace('/','%2F')
        header = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
        }
        url = 'https://ldtv.top/index.php/vod/search.html?wd={}&page={}'.format(keyword, page)
        verifyCode, session = self.verifyCode('https://ldtv.top/index.php/verify/index.html?', 'https://ldtv.top/index.php/ajax/verify_check?type=search&verify=')
        if verifyCode is False:
            return {tag: [items, False]}
        if not session:
            return {tag: [items, False]}
        r = session.get(url, headers=header, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        data = soup.select('div.module-items.module-card-items > div')
        mpg = soup.select('div#page > a')
        if mpg != []:
            maxpage = int(re.search(r'page/(.*?)/', mpg[-1].get('href')).group(1))
        else:
            maxpage = 1
        for video in data:
            sid = re.search(r'/id/(.*?).html', video.find('a').get('href')).group(1)
            name = video.select('div.module-card-item-title')[0].get_text().strip()
            description = video.select('div.module-info-item-content')[1].get_text().strip().replace('　　','\n')
            cover = video.select('div.module-item-pic > img')[0].get('data-original')
            remark = video.select('div.module-item-note')[0].get_text().strip()
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    name='零度：[{0}]/{1}'.format(remark, name),
                    id=sid,
                    cover=cover,
                    description=description,
                    params={
                        'type': 'video',
                        'pf': 'ld',
                        'num': 4
                    },
                ))
        if page < maxpage:
            nexpage = True
        else:
            nexpage = False
        return {tag: [items, nexpage]}

    def searchbb(self, keyword, tag, page):
        items = []
        url = 'https://api.bilibili.com/x/web-interface/search/type?search_type=media_bangumi&keyword={0}'.format(keyword)
        if not hasattr(self, 'bbck'):
            cookie = self.getCookie('bb')
        else:
            cookie = self.bbck
        r = requests.get(url, cookies=cookie, timeout=5)
        jo = json.loads(r.text)
        if jo['data']['numResults'] != 0:
            vodList = jo['data']['result']
            for vod in vodList:
                aid = str(vod['season_id']).strip()
                title = vod['title'].strip().replace("<em class=\"keyword\">", "").replace("</em>", "")
                img = vod['eps'][0]['cover'].strip()
                remark = vod['index_show']
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        name='哔哩影视：[{0}]/{1}'.format(remark, title),
                        id=aid,
                        cover=img,
                        params={
                            'type': 'video',
                            'pf': '影视',
                            'num': 5
                        },
                    ))
        return {tag: [items, False]}

    def searchps(self, keyword, tag, page):
        items = []
        r = requests.get('https://www.alipansou.com/search', params={'k': keyword, 't': 7}, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.select('van-row > a')
        for row in rows:
            remark = re.search(r'时间: (.*?) ', str(row.get_text)).group(1)
            clean = re.compile('<.*?>')
            name = re.sub(clean, '', row.find('template').__str__()).replace('\n', '').replace('\t', '').replace(' ', '')
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    name='盘搜：[{0}]/{1}'.format(remark, name),
                    id=re.search(r'/s/(.*)', row.get('href')).group(1),
                    params={
                        'type': 'video',
                        'pf': 'ps',
                        'num': 6
                    }
                ))
        return {tag: [items, False]}

    def searchys(self, keyword, tag, page):
        items = []
        header = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 12; V2049A Build/SP1A.210812.003; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/103.0.5060.129 Mobile Safari/537.36",
            "Referer": "https://yiso.fun/"
        }
        url = "https://yiso.fun/api/search?name={0}&from=ali".format(keyword)
        elements = requests.get(url=url, headers=header, timeout=5).json()["data"]["list"]
        for element in elements:
            id = element["url"]
            name = element["fileInfos"][0]["fileName"]
            remark = element['gmtCreate'].split(' ')[0]
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id=id,
                    name='易搜：[{0}]/{1}'.format(remark, name),
                    params={
                        'type': 'video',
                        'pf': 'ys',
                        'num': 7
                    }
                ))
        return {tag: [items, False]}

    def searchzzy(self, keyword, tag, page):
        items = []
        if not hasattr(self, 'zzy'):
            cookie = self.getCookie('zzy')
        else:
            cookie = self.zzy
        r = requests.get('https://zhaoziyuan.la/so', params={'filename': keyword}, cookies=cookie, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        elements = soup.select('div.news_text > a')
        for element in elements:
            name = element.find('h3')
            if name is None:
                return []
            else:
                name = element.find('h3').text
                remark = element.find('p').text.split('|')[-1].split('：')[1].split(' ')[0].strip()
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        id=element.get('href'),
                        name='找资源：[{0}]/{1}'.format(remark, name),
                        params={
                            'type': 'video',
                            'pf': 'zzy',
                            'num': 8
                        }
                    ))
        return {tag: [items, False]}

    def searchxzt(self, keyword, tag, page):
        items = []
        r = requests.post('https://gitcafe.net/tool/alipaper/', data={'action': 'search', 'keyword': keyword}, timeout=5)
        data = r.json()
        for video in data:
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id='https://www.aliyundrive.com/s/' + video['key'],
                    name='小纸条：' + video['title'],
                    params={
                        'type': 'video',
                        'pf': 'xzt',
                        'num': 9
                    }
                ))
        return {tag: [items, False]}

    def getCookie(self, tag):
        if tag == 'zzy':
            header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36",
                "Referer": "https://zhaoziyuan.la/login.html",
                "Origin": "https://zhaoziyuan.la/"
            }
            if 'Zhaozy' in jdata:
                logininfo = {'username': jdata['Zhaozy']['username'], 'password': jdata['Zhaozy']['password']}
                r = requests.post('https://zhaoziyuan.la/logiu.html', data=logininfo, headers=header, timeout=5)
                self.zztck = r.cookies
                return r.cookies
        if tag =='bb':
            r = requests.get("https://www.bilibili.com/")
            self.bbck = r.cookies
            return r.cookies

    def getDanm(self, oid):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36"
        }
        r = requests.get('https://api.bilibili.com/x/v1/dm/list.so', params={'oid': oid}, headers=header, timeout=5)
        danmu = re.search(r'<?xml version.*?</source>(.*)</i>', r.content.decode())
        if danmu:
            danmu = danmu.group(1)
        else:
            danmu = ''
        set_cache('bilibilidanmu' + oid, danmu)
        return danmu

    def getData(self, url, header, cookie, tag):
        r = requests.get(url, headers=header, cookies=cookie)
        return r.text

    def verifyCode(self, imgurl, resurl):
        if 'YSDQ' in jdata and 'ocrurl' in jdata['YSDQ']:
            ocrurl = jdata['YSDQ']['ocrurl']
        else:
            return False, None
        retry = 5
        header = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
        }
        while retry:
            try:
                session = requests.session()
                img = session.get(imgurl, headers=header).content
                code = session.post(url=ocrurl, data=base64.b64encode(img).decode()).text
                res = session.post(url="{}{}".format(resurl, code), headers=header).json()
                if res["msg"] == "ok":
                    return True, session
            except Exception as e:
                print(e)
            finally:
                retry = retry - 1
        return False, None

    def _get_tk(self, url, params, ts):
        keys = []
        for key in params:
            keys.append(key)
        keys.sort()
        src = urlparse(url).path
        for key in keys:
            src += str(params[key])
        src += str(ts)
        src += 'XSpeUFjJ'
        return hashlib.md5(src.encode()).hexdigest()

    def proxy_m3u8(self, ctx, params):
        url = params['url']
        redirects = ''
        if '@@@' in url:
            infos = url.split('@@@')
            url = infos[0]
            redirects = infos[1]
        headers = params['headers'].copy()
        if redirects == 'False':
            r = requests.get(url, headers=headers, stream=True, verify=False, allow_redirects=False)
        else:
            r = requests.get(url, headers=headers, stream=True, verify=False)
        content_type = r.headers['Content-Type'] if 'Content-Type' in r.headers else ''
        if content_type.startswith('image/') or content_type.startswith('text/'):
            content_type = 'application/vnd.apple.mpegurl'
        r.headers['Content-Type'] = content_type
        try:
            ctx.send_response(r.status_code)
            for key in r.headers:
                if key.lower() in ['connection', 'transfer-encoding']:
                    continue
                if content_type.lower() == 'application/vnd.apple.mpegurl':
                    if key.lower() in ['content-length', 'content-range']:
                        continue
                ctx.send_header(key, r.headers[key])
            ctx.end_headers()
            if content_type.lower() == 'application/vnd.apple.mpegurl':
                for line in r.iter_lines(8192):
                    line = line.decode()
                    if len(line) > 0 and not line.startswith('#'):
                        if not line.startswith('http'):
                            if line.startswith('/'):
                                line = url[:url.index('/', 8)] + line
                            else:
                                line = url[:url.rindex('/') + 1] + line
                        line = get_proxy_url(
                            Spideryingshi.__name__,
                            self.proxy_ts.__name__,
                            {
                                'url': line,
                                'headers': params['headers'],
                            },
                        )
                    ctx.wfile.write((line + '\n').encode())
            else:
                for chunk in r.iter_content(8192):
                    ctx.wfile.write(chunk)
        except Exception as e:
            print(e)
        finally:
            try:
                r.close()
            except:
                pass

    def proxy_ts(self, ctx, params):
        url = params['url']
        headers = params['headers'].copy()
        for key in ctx.headers:
            if key.lower() in ['user-agent', 'host']:
                continue
            headers[key] = ctx.headers[key]
        r = requests.get(url, headers=headers, stream=True, verify=False)
        r.headers['Content-Type'] = 'video/MP2T'

        try:
            ctx.send_response(r.status_code)
            for key in r.headers:
                if key.lower() in ['connection', 'transfer-encoding', 'accept-ranges']:
                    continue
                ctx.send_header(key, r.headers[key])
            ctx.end_headers()
            stripped_image_header = False
            for chunk in r.iter_content(8192):
                if not stripped_image_header:
                    chunk = chunk.lstrip(b'\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46')
                    chunk = chunk.lstrip(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A')
                    chunk = chunk.lstrip(b'\x42\x4D\x5A\x27\x4C')
                    chunk = chunk.lstrip(b'\x42\x4D')
                    stripped_image_header = True
                ctx.wfile.write(chunk)
        except Exception as e:
            print(e)
        finally:
            try:
                r.close()
            except:
                pass

#if __name__ == '__main__':
    #spider = Spideryingshi()
    #res = spider.list_items(parent_item={'type': 'directory', 'id': '/bd/bw-xianweidayuan/', 'name': '被窝：[完结]/县委大院', 'cover': 'https://pic.wujinpp.com/upload/vod/20221207-1/720ff4c2095d892e6e744d45bd5501d5.jpg', 'description': '《县委大院》是献礼党的“二十大”的一项重要作品。讲述了梅晓歌和他在新旧县委大院里先后两任同事们在新时代之大趋势、大变革之下，顺势而为一路前行，艰苦奋斗，纵横上下实现理想的故事。反应了新时期党员干部敢担', 'cast': [], 'director': '', 'area': '', 'year': 0, 'sources': [], 'danmakus': [], 'subtitles': [], 'params': {'type': 'video', 'pf': 'bw', 'num': 3}}, page=1)
    #res = spider.getDanm("https%3A%2F%2Fwww.bilibili.com%2Fbangumi%2Fplay%2Fep718240")
    #res = spider.search('县委大院', page=1)
    #res = spider.checkPurl({'playfrom': '', 'pf': 'bw', 'url': '/bp/xianweidayuan-1-24/'},'bw')
    #res = spider.runSearch('县委大院', 'bw', page=1)
    #res = spider.getCookie('zzy')
    #print(res)