from spider import Spider, SpiderItemType, SpiderItem, SpiderSource, SpiderPlayURL
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from utils import get_image_path
import xbmcaddon

_ADDON = xbmcaddon.Addon()

jsonurl = _ADDON.getSettingString('aliyundrive_refresh_token')
#jsonurl = 'https://gitlab.com/lm317379829/ysdq/-/raw/main/YSDQ.json'
if jsonurl.startswith('http'):
    try:
        jr = requests.get(jsonurl, verify=False, timeout=5)
        jdata = jr.json()
    except Exception :
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

class SpiderZhiBo(Spider):

    def name(self):
        return '直播'

    def is_searchable(self):
        return False

    def logo(self):
        return get_image_path('zhibo.png')

    def hide(self):
        return not _ADDON.getSettingBool('data_source_zhibo_switch')

    def list_items(self, parent_item=None, page=1):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"}
        if parent_item is None:
            items = []
            if 'Zhibo' in jdata and len(jdata['Zhibo']) != 0:
                for ids in jdata['Zhibo']:
                    name = ids['name']
                    pf = ids['pf']
                    id = ids['id']
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.Directory,
                            id=id,
                            name=name,
                            params={
                                'type': 'category',
                                'pf': pf,
                            },
                        ))
            else:
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        id='208',
                        name='斗鱼-一起看',
                        params={
                            'type': 'category',
                            'pf': 'douyu',
                        },
                    ))
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        id="2135",
                        name='虎牙-一起看',
                        params={
                            'type': 'category',
                            'pf': 'huya',
                        },
                    ))
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        id="sport",
                        name='体育-全部',
                        params={
                            'type': 'category',
                            'pf': 'sport',

                        },
                    ))
            return items, False

        elif parent_item['params']['type'] == 'category':
            pf = parent_item['params']['pf']
            id = parent_item['id']
            if pf == 'douyu':
                url = 'https://www.douyu.com/gapi/rkc/directory/mixList/2_{}/{}'.format(id, page)
                r = requests.get(url)
                data = r.json()
                items = []
                for room in data['data']['rl']:
                    if room['type'] != 1:
                        continue
                    items.append(
                        SpiderItem(type=SpiderItemType.File,
                                   id=room['rid'],
                                   name='[{0}]/{1}'.format(room['nn'], room['rn']),
                                   description='在线人数:{0}'.format(room['ol']),
                                   cover=room['rs1'],
                                   sources=[
                                       SpiderSource(
                                           room['rid'],
                                           {
                                               'pf': pf,
                                               'id': room['rid'],
                                           },
                                       )
                                   ]))
                return items, page < data['data']['pgcnt']
            elif pf == 'huya':
                url = 'https://www.huya.com/cache.php?m=LiveList&do=getLiveListByPage&gameId={0}&tagAll=0&callback=getLiveListJsonpCallback&page={1}'.format(id, page)
                r = requests.get(url)
                data = re.search(r"getLiveListJsonpCallback\((.*)\)", r.text).group(1)
                data = json.loads(data)
                items = []
                for room in data['data']['datas']:
                    items.append(
                        SpiderItem(type=SpiderItemType.File,
                                   id=room['profileRoom'],
                                   name='[{0}]/{1}'.format(room['nick'], room['introduction']),
                                   description='在线人数:{0}'.format(room['totalCount']),
                                   cover=room['screenshot'],
                                   sources=[
                                       SpiderSource(
                                           room['profileRoom'],
                                           {
                                               'pf': pf,
                                               'id': room['profileRoom'],
                                           },
                                       )
                                   ]))
                return items, page < data['data']['totalPage']
            elif pf == 'bilibili':
                r = requests.get(
                    'https://api.live.bilibili.com/xlive/web-interface/v1/second/getList',
                    params={
                        'platform': 'web',
                        'parent_area_id': parent_item['id'],
                        'page': page,
                    })
                data = r.json()
                items = []
                for room in data['data']['list']:
                    items.append(
                        SpiderItem(type=SpiderItemType.File,
                                   id=room['roomid'],
                                   name='[{0}]/{1}'.format(room['uname'],room['title']),
                                   description='在线人数:{0}'.format(room['online']),
                                   cover=room['cover'],
                                   sources=[
                                       SpiderSource(
                                           room['roomid'],
                                           {
                                               'pf': pf,
                                               'id': room['roomid'],
                                           },
                                       )
                                   ]))
                return items, data['data']['has_more']
            else:
                has_next_page = False
                url = 'http://www.freezb.live/'
                r = requests.get(url=url, headers=header)
                soup = BeautifulSoup(r.content.decode('utf-8'), 'html.parser')
                data = soup.select('tr.match_main')
                items = []
                for video in data:
                    infos = video.select('td')
                    urlList= video.select('td.update_data.live_link > a')
                    status = infos[1].select('sapn')[0].get('title')
                    if '比分' not in urlList[0].get_text() and status != '已结束':
                        stime = infos[1].select('sapn')[0].get_text()
                        gtype = infos[2].get_text()
                        hainfos = ' '.join(infos[3].get_text().lower().split()).split()
                        if hainfos.count('vs') != 0:
                            vsposi = hainfos.index('vs')
                            home = hainfos[vsposi-1]
                            away = hainfos[vsposi+1]
                            vs = 'VS'
                        else:
                            home = hainfos[0]
                            vs = ''
                            away = ''
                        name = '[{0}]/[{1}]{2}{3}{4}'.format(stime, gtype, home, vs, away)
                        cover = 'https://s1.ax1x.com/2022/10/07/x3NPUO.png'
                        sources = []
                        for url in urlList:
                            title = url.get_text()
                            aurl = url.get('href')
                            if '比分' not in title:
                                sources.append(
                                    SpiderSource(
                                        title,
                                        {
                                            'pf': pf,
                                            'url': aurl,
                                        },
                                    ))
                        items.append(
                            SpiderItem(
                                type=SpiderItemType.File,
                                name=name,
                                cover=cover,
                                sources=sources,
                                params={
                                    'speedtest': spLimit,
                                    'thlimit': thlimit,
                                }
                            ))
            return items, has_next_page

    def resolve_play_url(self, source_params):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"}
        pf = source_params['pf']
        if pf == 'douyu':
            purl = 'http://epg.112114.xyz/douyu/{}'.format(source_params['id'])
            return SpiderPlayURL(purl)
        elif pf == 'huya':
            url = 'https://mp.huya.com/cache.php?m=Live&do=profileRoom&roomid={0}'.format(source_params['id'])
            r = requests.get(url=url, headers=header)
            data = r.json()['data']
            if data['liveStatus'] != 'ON':
                purl = ''
            else:
                purl = 'http://txtest-xp2p.p2p.huya.com/src/' + data['stream']['baseSteamInfoList'][0]['sStreamName'] + '.xs?ratio=4000'
            return SpiderPlayURL(purl)
        elif pf =='bilibili':
            #url = 'https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo?room_id={0}&protocol=0,1&format=0,1,2&codec=0,1'.format(id)
            url = 'https://api.live.bilibili.com/room/v1/Room/playUrl?cid={0}&qn=20000&platform=h5'.format(source_params['id'])
            r = requests.get(url=url, headers=header)
            data = r.json()['data']
            purl = data['durl'][0]['url']
            return SpiderPlayURL(purl)
        elif pf == 'sport':
            return SpiderPlayURL(source_params['url'])

    def search(self, keyword, page=1):
        return []

    def checkPurl(self, source_params, tag):
        try:
            url = source_params['url']
            headers = {
                "Referer": url,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
            }
            r = requests.get(url)
            soup = BeautifulSoup(r.content.decode('utf-8'), 'html.parser')
            rurl = soup.select('div.media > iframe ')[0].get('src')
            r = requests.get(rurl, headers=headers, cookies=r.cookies)
            if 'm3u8' in r.text:
                if 'm3u8.html?id=' in r.text:
                    purl = re.search(r'm3u8\.html\?id=(.*?m3u8.*?)\"',
                                     r.text.replace("\n", '').replace("\r", '')).group(1)
                else:
                    purl = re.search(r"url: \'(.*?)\'", r.text.replace("\n", '').replace("\r", '')).group(1)
                if not purl.startswith('http'):
                    purl = re.search(r"(.*)/", rurl).group(1) + purl
                tspDict = self.readM3U8(purl, headers, tag)
                return [tspDict, purl]
            else:
                aurl = re.search(r"(.*)/", rurl).group(1) + re.search(r'src=\"..(.*?)\"', r.text.replace("\n", '').replace("\r", '')).group(1)
                aheaders = {
                    "Referer": rurl,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
                }
                r = requests.get(aurl, headers=aheaders, cookies=r.cookies)
                purl = re.search(r"url: \'(.*?)\'", r.text.replace("\n", '').replace("\r", ''))
                if purl == None:
                    purl = re.search(r'm3u8\.html\?id=(.*?)\"', r.text.replace("\n", '').replace("\r", ''))
                purl = purl.group(1)
                tspDict = self.readM3U8(purl, {}, tag)
                return [tspDict, purl]
        except Exception as e:
            print(e)
            return [{tag: 0}, '']

    def sub(self, string, p, c):
        new = []
        for s in string:
            new.append(s)
        new[p] = c
        return ''.join(new)

    def readM3U8(self, url, header, tag):
        if '.xs' in url or '.flv' in url or '.mp4' in url or '.jpg' in url or '.jepg' in url or '.bmp' in url or '.png' in url or '.ico' in url or '.icon' in url or '###' in url:
           return self.SpeedInfo(url.replace('###', ''), header, tag)
        s_url = None
        try:
            if '@@@' in url:
                url = url.split('@@@')[0]
                response = requests.get(url, headers=header, allow_redirects=False, verify=False, timeout=5)
                if 'Location' in response.headers and response.text == '':
                    url = response.headers['Location']
                    response = requests.get(url, headers=header, allow_redirects=False, verify=False, timeout=5)
            else:
                response = requests.get(url, headers=header, verify=False, timeout=5)
            response.encoding = 'utf-8'
            str = response.text
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
            return self.SpeedInfo(s_url, header, tag)
        except Exception as e:
            return {tag: 0}

    def SpeedInfo(self, url, header, tag):
        header.update({'Proxy-Connection':'keep-alive'})
        r = requests.get(url, stream=True, headers=header, verify=False, timeout=5)
        count = 0
        count_tmp = 0
        stime = time.time()
        i = 0
        speed = 0
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                if i != 0 :
                    break
                count += len(chunk)
                sptime = time.time() - stime
                if sptime > 0:
                    speed = int((count - count_tmp) / sptime)
                    stime = time.time()
                    i = i + 1
        return {tag: speed}

#if __name__ == '__main__':
    #spider = SpiderZhiBo()
    #res = spider.list_items(parent_item={'type': 'directory', 'id': 'sport', 'name': '体育-全部', 'cover': '', 'description': '', 'cast': [], 'director': '', 'area': '', 'year': 0, 'sources': [], 'danmakus': [], 'subtitles': [], 'params': {'type': 'category', 'pf': 'sport'}}, page=1)
    #res = spider.resolve_play_url({'pf': 'douyu', 'id': 9220456})
    #res = spider.checkPurl({'pf': 'sport', 'url': 'http://www.freezb.live/tv/qqlive76.html'}, '2')
    #print(res)