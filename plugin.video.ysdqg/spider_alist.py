from spider import Spider, SpiderItemType, SpiderItem, SpiderSubtitle, SpiderSource, SpiderPlayURL
import re
import requests
from utils import get_image_path
import xbmcaddon

_ADDON = xbmcaddon.Addon()

base = {
    'ver': 0,
    'baseurl': '',
}

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

class SpiderAlist(Spider):

    def name(self):
        return 'Alist网盘'

    def logo(self):
        return get_image_path('alist.png')

    def is_searchable(self):
        return False

    def hide(self):
        return not _ADDON.getSettingBool('data_source_alist_switch')

    def list_items(self, parent_item=None, page=1):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
        }
        if parent_item is None:
            items = []
            if 'Alist' in jdata and len(jdata['Alist']) != 0:
                for ids in jdata['Alist']:
                    name = ids
                    id = jdata['Alist'][ids]
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.Directory,
                            id=id,
                            name=name,
                            params={
                                'type': 'category',
                            },
                        ))
            else:
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        id='https://al.chirmyram.com',
                        name='七米蓝',
                        params={
                            'type': 'category',
                        },
                    ))
            return items, False

        elif parent_item['params']['type'] == 'category':
            if parent_item['id'].endswith('/'):
                category_id = parent_item['id']
            else:
                category_id = parent_item['id'] + '/'
            # get ver start
            if base['ver'] == '' or base['baseurl'] == '':
                baseurl = re.findall(r"http.*://.*?/", category_id)[0]
                ver, pagetype = self.getVer(baseurl, header)
                base['ver'] = ver
                base['baseurl'] = baseurl
            else:
                ver = base['ver']
                baseurl = base['baseurl']
                # get ver end
            if pagetype == 'pagination':
                header.update({'Referer': '{}?page={}'.format(parent_item['id'].encode('UTF-8'), page)})
                pagenumid = 'per_page'
                pagenum = 30
            elif pagetype == 'all':
                header.update({'Referer': baseurl})
                pagenumid = 'per_page'
                pagenum = 0
            else:
                header.update({'Referer': baseurl})
                pagenumid = 'page_size'
                pagenum = 30
            pat = category_id.replace(baseurl, "")
            if 'password' in parent_item['params']:
                password = parent_item['params']['password']
            else:
                password = ''
            param = {
                "path": '/' + pat,
                "refresh": False,
                pagenumid: pagenum,
                'page': page,
                'password': password
            }
            if ver == 2:
                r = requests.post(baseurl + 'api/public/path', json=param, headers=header)
                datas = r.json()
                total = datas['meta']['total']
                dataappend = 'files'
                picappend ='thumbnail'
            elif ver == 3:
                r = requests.post(baseurl + 'api/fs/list', json=param, headers=header)
                datas = r.json()
                total = datas['data']['total']
                dataappend = 'content'
                picappend = 'thumb'
            data = datas['data'][dataappend]
            diritems = []
            fileitems = []
            subtitles = []
            data.sort(key=lambda x: (x['name']), reverse=False)
            for video in data:
                if video['type'] == 1:
                    id = category_id + video['name']
                    diritems.append(
                        SpiderItem(
                            type=SpiderItemType.Directory,
                            name=video['name'],
                            id=id,
                            params={
                                'type': 'category',
                            },
                        ))
                else:
                    pic = video[picappend]
                    # 计算文件大小 start
                    size = video['size']
                    if size > 1024 * 1024 * 1024 * 1024.0:
                        fs = "TB"
                        sz = round(size / (1024 * 1024 * 1024 * 1024.0), 2)
                    elif size > 1024 * 1024 * 1024.0:
                        fs = "GB"
                        sz = round(size / (1024 * 1024 * 1024.0), 2)
                    elif size > 1024 * 1024.0:
                        fs = "MB"
                        sz = round(size / (1024 * 1024.0), 2)
                    elif size > 1024.0:
                        fs = "KB"
                        sz = round(size / (1024.0), 2)
                    else:
                        fs = "KB"
                        sz = round(size / (1024.0), 2)
                    # 计算文件大小 end
                    remark = str(sz) + fs
                    endits = video['name'].split('.')[-1]
                    if endits in ['mp4', 'mkv', 'ts', 'TS', 'avi', 'flv', 'rmvb', 'mp3', 'flac', 'wav', 'wma', 'dff']:
                        fileitems.append(
                            SpiderItem(
                                type=SpiderItemType.File,
                                name='[{}]/{}'.format(remark, video['name']),
                                id=category_id,
                                cover=pic,
                                subtitles=[],
                                sources=[
                                    SpiderSource(
                                        'Alist网盘',
                                        {
                                            'url': video['name'],
                                            'id': category_id,
                                        },
                                    )
                                ],
                            ))
                    elif endits in ['srt', 'ass', 'vtt']:
                        subname = video['name']
                        subtitles.append(SpiderSubtitle(subname, 'alist@@@' + category_id + subname))
            if len(subtitles) != 0 and len(fileitems) != 0:
                for i in range(0, len(fileitems)):
                    fileitems[i]['subtitles'] = subtitles
            items = diritems + fileitems
            if len(data) * page < total:
                has_next_page = True
            else:
                has_next_page = False
            return items, has_next_page
        else:
            return [], False

    def resolve_play_url(self, source_params):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"}
        url = source_params['id'] + source_params['url']
        # get ver start
        if base['ver'] == '' or base['baseurl'] == '':
            baseurl = re.findall(r"http.*://.*?/", url)[0]
            header.update({'Referer': baseurl})
            ver, pagetype = self.getVer(baseurl, header)
            base['ver'] = ver
            base['baseurl'] = baseurl
        else:
            ver = base['ver']
            baseurl = base['baseurl']
            header.update({'Referer': baseurl})
            # get ver end
        param = {
            "path": '/' + url.replace(baseurl, '')
        }
        if ver == 2:
            r = requests.post(baseurl + 'api/public/path', json=param, headers=header)
            purl = r.json()['data']['files'][0]['url']
        elif ver == 3:
            r = requests.post(baseurl + 'api/fs/get', json=param, headers=header)
            purl = r.json()['data']['raw_url']
        if not purl.startswith('http'):
            head = re.findall(r"h.*?:", baseurl)[0]
            purl = head + purl
        return SpiderPlayURL(purl)

    def resolve_subtitles(self, suburl):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"}
        url = suburl.split('@@@')[1]
        # get ver start
        if base['ver'] == '' or base['baseurl'] == '':
            baseurl = re.findall(r"http.*://.*?/", url)[0]
            header.update({'Referer': baseurl})
            ver, pagetype = self.getVer(baseurl, header)
            base['ver'] = ver
            base['baseurl'] = baseurl
        else:
            ver = base['ver']
            baseurl = base['baseurl']
            header.update({'Referer': baseurl})
            # get ver end
        param = {
            "path": '/' + url.replace(baseurl, '')
        }
        if ver == 2:
            r = requests.post(baseurl + 'api/public/path', json=param, headers=header)
            suburl = r.json()['data']['files'][0]['url']
        elif ver == 3:
            r = requests.post(baseurl + 'api/fs/get', json=param, headers=header)
            suburl = r.json()['data']['raw_url']
        if suburl.startswith('http') is False:
            head = re.findall(r"h.*?:", baseurl)[0]
            suburl = head + suburl
        return suburl

    def search(self, keyword, page=1):
        return []

    def getVer(self, baseurl, header):
        ver = requests.get(baseurl + 'api/public/settings', headers=header)
        vjo = ver.json()['data']
        if type(vjo) is dict:
            ver = 3
            pagetype = vjo['pagination_type']
        else:
            ver = 2
            pagetype = ''
        return ver, pagetype

#if __name__ == '__main__':
    #spider = SpiderAlist()
    #res = spider.list_items(parent_item={'type': 'directory', 'id': 'http://alist.xiaoya.pro/电影/2022', 'name': '100T影视', 'cover': '', 'description': '', 'cast': [], 'director': '', 'area': '', 'year': 0, 'sources': [], 'danmakus': [], 'subtitles': [], 'params': {'type': 'category'}}, page=3)
    #res = spider.resolve_play_url({'url': '20220104.尖峰对决之古墓神兵.HD1080p.国语中字.mp4', 'id': 'http://alist.xiaoya.pro/电影/2022/'})
    #res = spider.search("红小豆")
    #res = spider.resolve_subtitles('alist@@@http://alist.xiaoya.pro/电影/2022/囚禁.Shut.In.2022.1080p.WEBRip.x264-RARBG.srt')
    #print(res)