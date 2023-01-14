from spider import Spider, SpiderItemType, SpiderSource, SpiderItem, SpiderPlayURL
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from utils import get_image_path
import xbmcaddon

_ADDON = xbmcaddon.Addon()

jsonurl = _ADDON.getSettingString('aliyundrive_refresh_token')
#jsonurl = 'https://mpimg.cn/down.php/c8f9e6ed2446c6d5c6973df99ff2fbe1.json'
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
if 'YSDQ' in jdata and 'disableIPV6' in jdata['YSDQ']:
    disableIPV6 = jdata['YSDQ']['disableIPV6']
else:
    disableIPV6 = 'yes'

class SpiderDianShiZhiBo(Spider):

    def name(self):
        return '电视直播'

    def logo(self):
        return get_image_path('dianshi.png')

    def is_searchable(self):
        return True

    def hide(self):
        return not _ADDON.getSettingBool('data_source_dianshi_switch')

    def list_items(self, parent_item=None, page=1):
        header = {
            "User-Agent": "Mozilla/5.0 (Linux; U; Android 9; zh-cn; MIX 2S Build/PKQ1.180729.001) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/61.0.3163.128 Mobile Safari/537.36 XiaoMi/MiuiBrowser/10.1.1"}
        if parent_item is None:
            items = []
            r = requests.get('http://www.lu1.cc/c/tv/sjtv/index.htm', headers=header)
            soup = BeautifulSoup(r.content.decode('utf-8'), 'html.parser')
            datas = soup.select('ul > li')
            for data in datas:
                name = data.get_text().strip()
                id = data.select('a')[0].get('href')
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        name=name.replace('网络', '数字频道'),
                        id=id,
                        params={
                            'type': 'category',
                        },
                    ))
            items.sort(key=lambda i: len(i['name']), reverse=False)
            return items, False
        elif parent_item['params']['type'] == 'category':
            url = 'http://www.lu1.cc/c/tv/sjtv/{0}'.format(parent_item['id'])
            r = requests.get(url=url, headers=header)
            soup = BeautifulSoup(r.content.decode('utf-8'), 'html.parser')
            data = soup.select('li')
            items = []
            for video in data:
                vid = video.select('a')
                if vid ==[]:
                    continue
                vid = video.get_text().replace('-', '').replace('中央新影', '').replace('电视台', '').replace('·法治', '')
                if vid.startswith('CCTV'):
                    vid = vid.replace(re.search(r'[\u4e00-\u9fa5]+', vid).group(0), '')
                if vid.startswith('CETV') and '早期教育' not in vid:
                    vid = re.search(r'CETV\d+', vid).group(0)
                if 'CNC' in vid:
                    vid = vid.replace('新闻', '').replace('台', '')
                if '凤凰卫视' in vid and len(vid) != 4:
                    vid = vid.replace('卫视', '').replace('台', '')
                name = video.get_text()
                cover = 'https://i.postimg.cc/QxCn329F/television.png'
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        id=vid,
                        name=name,
                        cover=cover,
                        params={
                            'type': 'video',
                        },
                    ))
            return items, False
        elif parent_item['params']['type'] == 'video':
            items = []
            header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
            }
            url = 'https://www.foodieguide.com/iptvsearch/?page={}&s={}'.format(page,  parent_item['id'])
            r = requests.get(url, headers=header)
            soup = BeautifulSoup(r.content, 'html.parser')
            data = soup.select('table.tables > tr')
            mpg = soup.select('div[style="display:flex;justify-content:center;"] > a')
            if mpg != []:
                maxpage = int(re.search(r'page=(.*?)&', mpg[-1].get('href')).group(1))
            else:
                maxpage = 1
            nameList = []
            for video in data:
                strvideo = video.get_text().replace('\r', '').replace('\n', '').replace('\t', '')
                if strvideo == '':
                    continue
                infos = strvideo.split('checked')
                name = re.search(r'(.*?)\d\d-\d+-\d+', infos[0]).group(1)
                purl = infos[1].strip()
                if not purl.startswith('http'):
                    continue
                if name in nameList:
                    num = nameList.index(name)
                    sources = (
                        SpiderSource(
                            'Checked ' + re.search(r'\d+-\d+-\d+', infos[0]).group(0).strip(),
                            {
                                'url': purl,
                             }
                        ))
                    items[num]['sources'].append(sources)
                else:
                    nameList.append(name)
                    sources = []
                    sources.append(
                        SpiderSource(
                            'Checked ' + re.search(r'\d+-\d+-\d+', infos[0]).group(0).strip(),
                            {
                                'url': purl,
                            },
                        ))
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.File,
                            name=name,
                            id='',
                            cover='',
                            description='',
                            sources=sources,
                            params={
                                'speedtest': spLimit,
                                'thlimit': thlimit,
                            }
                        ))
            if page < maxpage:
                has_next_page = True
            else:
                has_next_page = False
            return items, has_next_page
        else:
            return [], False

    def resolve_play_url(self, source_params):
        return SpiderPlayURL(source_params['url'])

    def search(self, keyword, page=1):
        items = []
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
        }
        url = 'https://www.foodieguide.com/iptvsearch/?page={}&s={}'.format(page, keyword)
        r = requests.get(url, headers=header)
        soup = BeautifulSoup(r.content, 'html.parser')
        data = soup.select('table.tables > tr')
        mpg = soup.select('div[style="display:flex;justify-content:center;"] > a')
        if mpg != []:
            maxpage = int(re.search(r'page=(.*?)&', mpg[-1].get('href')).group(1))
        else:
            maxpage = 1
        nameList= []
        for video in data:
            strvideo = video.get_text().replace('\r','').replace('\n','').replace('\t','')
            if strvideo == '':
                continue
            infos = strvideo.split('checked')
            name = re.search(r'(.*?)\d\d-\d+-\d+', infos[0]).group(1)
            purl = infos[1].strip()
            if not purl.startswith('http'):
                continue
            if name in nameList:
                num = nameList.index(name)
                sources = (SpiderSource('Checked ' + re.search(r'\d+-\d+-\d+', infos[0]).group(0).strip(),
                        {
                            'url': purl
                        }))
                items[num]['sources'].append(sources)
            else:
                nameList.append(name)
                sources = []
                sources.append(
                    SpiderSource(
                        'Checked ' + re.search(r'\d+-\d+-\d+', infos[0]).group(0).strip(),
                        {
                            'url': purl

                        },
                    ))
                items.append(
                    SpiderItem(
                        type=SpiderItemType.File,
                        name='电视直播：{}'.format(name),
                        id='',
                        cover='',
                        description='',
                        sources=sources,
                        params={
                            'speedtest': spLimit,
                            'thlimit': thlimit,
                        }
                    ))
        if page < maxpage:
            has_next_page = True
        else:
            has_next_page = False
        return items, has_next_page

    def checkPurl(self, source_params, tag):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
        }
        purl = source_params['url']
        try:
            if not purl.endswith('/') and purl.count('/') == 2:
                purl = purl + '/'
            num = re.search(r'://(.*?)/', purl).group(1).count(":")
            if disableIPV6.lower() == 'yes' and num > 4:
                return [{tag: 0}, '']
            r = requests.get(purl, stream=True, allow_redirects=False, headers=header, timeout=5)
            if 'Content-Type' in r.headers and 'video' in r.headers['Content-Type'].lower():
                r.close()
            if 'Location' in r.headers:
                purl = r.headers['Location']
            tspDict = self.readM3U8(purl, header, tag)
            return [tspDict, purl]
        except Exception:
            return [{tag: 0}, purl]

    def sub(self, string, p, c):
        new = []
        for s in string:
            new.append(s)
        new[p] = c
        return ''.join(new)

    def readM3U8(self, url, header, tag):
        url = url.strip('/')
        s_url = None
        try:
            response = requests.get(url, stream=True, headers=header, timeout=5)
            if 'video' in response.headers['Content-Type']:
                response.close()
                return self.SpeedInfo(url, header, tag)
            response.encoding = 'utf-8'
            str = response.text
            result = urlparse(url)
            url_tou = result[0] + '://' + result[1]
            # 获取m3u8中的片段ts文件
            # 需要替换 ../
            list = str.split("\n");
            for str in list:
                if str.find(".ts") != -1:
                    # 特殊格式==>回退目录
                    if (str.find("../../../../..") != -1):
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
                    elif str.startswith('#'):
                        continue
                    else:
                        pos = url.rfind("/")
                        s_url = url.replace(url[pos:], "/" + str).strip('\r').strip('\n').strip()
                    return self.readM3U8(s_url, header, tag)
            return self.SpeedInfo(s_url, header, tag)
        except Exception as e:
            print(e)
            return {tag: 0}

    def SpeedInfo(self, url, header, tag):
        header.update({'Proxy-Connection':'keep-alive'})
        r = requests.get(url, stream=True, headers=header, timeout=5)
        count = 0
        count_tmp = 0
        stime = time.time()
        i = 0
        speed = 0
        for chunk in r.iter_content(chunk_size=10240):
            if chunk:
                if i == 2:
                    break
                count += len(chunk)
                sptime = time.time() - stime
                if 'Content-Length' in r.headers and count == int(r.headers['Content-Length']):
                    speed = int((count - count_tmp) / sptime)
                if sptime > 0:
                    speed = int((count - count_tmp)/sptime)
                    stime = time.time()
                    count_tmp = count
                    i = i + 1
        r.close()
        return {tag: speed}

#if __name__ == '__main__':
    #spider = SpiderDianShiZhiBo()
    #res = spider.list_items(parent_item={'type': 'directory', 'id': 'CCTV1', 'name': 'CCTV1综合', 'cover': 'https://i.postimg.cc/QxCn329F/television.png', 'description': '', 'cast': [], 'director': '', 'area': '', 'year': 0, 'sources': [], 'danmakus': [], 'subtitles': [], 'params': {'type': 'video'}}, page=1)
    #res = spider.resolve_play_url({'url': 'http://[2409:8087:3869:8021:1001::e5]:6610/PLTV/88888888/224/3221225918/2/index.m3u8?IASHttpSessionId=OTT15232820230107121543310379'}})
    #res = spider.search("CCTV1", 1)
    #res = spider.checkPurl({'url': 'http://111.20.33.93/TVOD/88888888/224/3221225804/index.m3u8'}, '3')
    #print(res)