from spider import Spider, SpiderItemType, SpiderSource, SpiderItem, SpiderPlayURL, SpiderDanmaku
import os
import re
import json
import time
import requests
import threading
from requests import utils
from danmaku import get_danmaku_url
from proxy import get_proxy_url, get_qrcode_url
from cache import get_cache, set_cache, del_cache
from utils import get_image_path
import xbmcaddon
import xbmcgui
import xbmcvfs

_ADDON = xbmcaddon.Addon()
cookies_path = xbmcvfs.translatePath(os.path.join(_ADDON.getAddonInfo('path'), 'cookie.txt'))
#cookies_path = 'cookie.txt'

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

class Spiderbilibili(Spider):

    def name(self):
        return '哔哩哔哩'

    def logo(self):
        return get_image_path('bilibili.png')

    def is_searchable(self):
        return False

    def hide(self):
        return not _ADDON.getSettingBool('data_source_bilibili_switch')

    def list_items(self, parent_item=None, page=1):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
        }
        if parent_item is None:
            if len(self.cookies) <= 0:
                self.getCookie()
            if self.login is False:
                qrlogth = threading.Thread(target=self.qrlogin, args=(self.key,))
                qrlogth.start()
                xbmcgui.Dialog().notification('扫码登录', 'Cookies已失效，请重新扫码', get_qrcode_url(self.qrurl), 30000, False)
            items = []
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id="推荐",
                    name='推荐',
                    params={
                        'type': 'category',
                        'pf': '',
                    },
                ))
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id="热门",
                    name='热门',
                    params={
                        'type': 'category',
                        'pf': '',
                    },
                ))
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id='动态',
                    name='动态',
                    params={
                        'type': 'category',
                        'pf': '',
                    },
                ))
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id="收藏夹",
                    name='收藏夹',
                    params={
                        'type': 'category',
                        'pf': '',
                    },
                ))
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id="历史记录",
                    name='历史记录',
                    params={
                        'type': 'category',
                        'pf': '',
                    },
                ))
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id="影视",
                    name='影视',
                    params={
                        'type': 'category',
                        'pf': '',
                    },
                ))
            if 'Bili' in jdata and 'category' in jdata['Bili']:
                infos = jdata['Bili']['category'].split('|')
                for info in infos:
                    kyinfo = info.split(',')
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.Directory,
                            id=kyinfo[1],
                            name=kyinfo[0],
                            params={
                                'type': 'category',
                                'pf': '',
                            },
                        ))
            return items, False
        elif parent_item['params']['type'] == 'category':
            if parent_item['id'] == '热门':
                url = 'https://api.bilibili.com/x/web-interface/popular?ps=20&pn={0}'.format(page)
                if len(self.cookies) <= 0:
                    self.getCookie()
                rsp = requests.get(url, cookies=self.cookies)
                jo = json.loads(rsp.text)
                items = []
                if jo['code'] == 0:
                    vodList = jo['data']['list']
                    for vod in vodList:
                        aid = str(vod['aid']).strip()
                        title = vod['title'].strip().replace("<em class=\"keyword\">", "").replace("</em>", "")
                        img = vod['pic'].strip()
                        remark = time.strftime('%H:%M:%S', time.gmtime(vod['duration']))
                        if remark.startswith('00:'):
                            remark = remark[3:]
                        if remark != '00:00':
                            items.append(
                                SpiderItem(
                                    type=SpiderItemType.Directory,
                                    name='[{0}]/{1}'.format(remark, title),
                                    id=aid,
                                    cover=img,
                                    params={
                                        'type': 'video',
                                        'pf': '',
                                    },
                                ))
                    if jo['data']['no_more'] is False:
                        has_next_page = True
                    else:
                        has_next_page = False
                    return items, has_next_page
            if parent_item['id'] == '推荐':
                url = 'https://api.bilibili.com/x/web-interface/index/top/feed/rcmd?y_num={0}&fresh_type=3&feed_version=SEO_VIDEO&fresh_idx_1h=1&fetch_row=1&fresh_idx=1&brush=0&homepage_ver=1&ps=20'.format(
                    page)
                if len(self.cookies) <= 0:
                    self.getCookie()
                rsp = requests.get(url, cookies=self.cookies)
                jo = json.loads(rsp.text)
                items = []
                if jo['code'] == 0:
                    vodList = jo['data']['item']
                    for vod in vodList:
                        aid = str(vod['id']).strip()
                        title = vod['title'].strip().replace("<em class=\"keyword\">", "").replace("</em>", "")
                        img = vod['pic'].strip()
                        remark = time.strftime('%H:%M:%S', time.gmtime(vod['duration']))
                        if remark.startswith('00:'):
                            remark = remark[3:]
                        if remark != '00:00':
                            items.append(
                                SpiderItem(
                                    type=SpiderItemType.Directory,
                                    name='[{0}]/{1}'.format(remark, title),
                                    id=aid,
                                    cover=img,
                                    params={
                                        'type': 'video',
                                        'pf': '',
                                    },
                                ))
                    return items, True
            if parent_item['id'] == "动态":
                items = []
                if len(self.cookies) <= 0:
                    self.getCookie()
                if page == 1:
                    del_cache('offset')
                offset = get_cache('offset')
                url = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/all?timezone_offset=-480&type=all&offset={0}'.format(offset)
                rsp = requests.get(url, cookies=self.cookies)
                jo = json.loads(rsp.text)
                if jo['code'] == 0:
                    offset_value = jo['data']['offset']
                    set_cache('offset', offset_value)
                    vodList = jo['data']['items']
                    for vod in vodList:
                        if vod['type'] == 'DYNAMIC_TYPE_AV':
                            remark = vod['modules']['module_author']['name'].strip()
                            vod = vod['modules']['module_dynamic']['major']['archive']
                            aid = str(vod['aid']).strip()
                            title = vod['title'].strip().replace("<em class=\"keyword\">", "").replace("</em>", "")
                            img = vod['cover'].strip()
                            items.append(
                                SpiderItem(
                                    type=SpiderItemType.Directory,
                                    name='[{0}]/{1}'.format(remark, title),
                                    id=aid,
                                    cover=img,
                                    params={
                                        'type': 'video',
                                        'pf': '',
                                    },
                                ))
                    return items, jo['data']['has_more']
            if parent_item['id'] == '影视':
                items = []
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        id="1",
                        name='番剧',
                        params={
                            'type': 'category',
                            'pf': '番剧',
                        },
                    ))
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        id="4",
                        name='国创',
                        params={
                            'type': 'category',
                            'pf': '国创',
                        },
                    ))
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        id="2",
                        name='电影',
                        params={
                            'type': 'category',
                            'pf': '电影',
                        },
                    ))
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        id="7",
                        name='综艺',
                        params={
                            'type': 'category',
                            'pf': '综艺',
                        },
                    ))
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        id="5",
                        name='电视剧',
                        params={
                            'type': 'category',
                            'pf': '电视剧',
                        },
                    ))
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        id="3",
                        name='纪录片',
                        params={
                            'type': 'category',
                            'pf': '纪录片',
                        },
                    ))
                return items, False
            if parent_item['params']['pf'] in ['番剧', '国创', '电影', '综艺', '电视剧', '纪录片']:
                url = 'https://api.bilibili.com/pgc/season/index/result?order=2&season_status=-1&style_id=-1&sort=0&area=-1&pagesize=20&type=1&st={0}&season_type={0}&page={1}'.format(parent_item['id'], page)
                if len(self.cookies) <= 0:
                    self.getCookie()
                rsp = requests.get(url, cookies=self.cookies)
                jo = json.loads(rsp.text)
                items = []
                vodList = jo['data']['list']
                for vod in vodList:
                    aid = str(vod['season_id']).strip()
                    title = vod['title'].strip()
                    img = vod['cover'].strip()
                    remark = vod['index_show'].strip()
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.Directory,
                            name='[{0}]/{1}'.format(remark, title),
                            id=aid,
                            cover=img,
                            params={
                                'type': 'video',
                                'pf': '影视',
                            },
                        ))
                if jo['data']['has_next'] ==1:
                    has_next_page = True
                else:
                    has_next_page = False
                return items, has_next_page
            if parent_item['id'] == "收藏夹":
                self.userid = self.get_userid()
                url = 'http://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid=%s&jsonp=jsonp' % (self.userid)
                if len(self.cookies) <= 0:
                    self.getCookie()
                rsp = requests.get(url, cookies=self.cookies)
                jo = json.loads(rsp.text)
                items = []
                if jo['code'] == 0:
                    for fav in jo['data'].get('list'):
                        name = fav['title']
                        cid = fav['id']
                        items.append(
                            SpiderItem(
                                type=SpiderItemType.Directory,
                                name=name,
                                id=cid,
                                params={
                                    'type': 'category',
                                    'pf': '收藏夹',
                                },
                            ))
                    return items, False
            if parent_item['params']['pf'] == "收藏夹":
                mlid = parent_item['id']
                url = 'http://api.bilibili.com/x/v3/fav/resource/list?media_id={0}&pn={1}&ps=20&platform=web&type=0'.format(mlid, page)
                if len(self.cookies) <= 0:
                    self.getCookie()
                rsp = requests.get(url, cookies=self.cookies)
                jo = json.loads(rsp.text)
                items = []
                if jo['code'] == 0:
                    vodList = jo['data']['medias']
                    for vod in vodList:
                        aid = str(vod['id']).strip()
                        title = vod['title'].replace("<em class=\"keyword\">", "").replace("</em>", "").replace(
                            "&quot;", '"')
                        img = vod['cover'].strip()
                        remark = time.strftime('%H:%M:%S', time.gmtime(vod['duration']))
                        if remark.startswith('00:'):
                            remark = remark[3:]
                        items.append(
                            SpiderItem(
                                type=SpiderItemType.Directory,
                                name='[{0}]/{1}'.format(remark, title),
                                id=aid,
                                cover=img,
                                params={
                                    'type': 'video',
                                    'pf': '',
                                },
                            ))
                    return items, jo['data']['has_more']
            if parent_item['id'] == '历史记录':
                url = 'http://api.bilibili.com/x/v2/history?pn={0}'.format(page)
                if len(self.cookies) <= 0:
                    self.getCookie()
                rsp = requests.get(url, cookies=self.cookies)
                jo = json.loads(rsp.text)
                items = []
                if jo['code'] == 0:
                    vodList = jo['data']
                    for vod in vodList:
                        if vod['duration'] > 0:
                            aid = str(vod["aid"]).strip()
                            title = vod["title"].replace("<em class=\"keyword\">", "").replace("</em>", "").replace(
                                "&quot;", '"')
                            img = vod["pic"].strip()
                            if vod['progress'] == -1:
                                process = time.strftime('%H:%M:%S', time.gmtime(vod['duration']))
                            else:
                                process = time.strftime('%H:%M:%S', time.gmtime(vod['progress']))
                            total_time = time.strftime('%H:%M:%S', time.gmtime(vod['duration']))
                            if process.startswith('00:'):
                                process = process[3:]
                            if total_time.startswith('00:'):
                                total_time = total_time[3:]
                            remark = process + '|' + total_time
                            items.append(
                                SpiderItem(
                                    type=SpiderItemType.Directory,
                                    name='[{0}]/{1}'.format(remark, title),
                                    id=aid,
                                    cover=img,
                                    params={
                                        'type': 'video',
                                        'pf': '',
                                    },
                                ))
                    if len(jo['data']) == 300:
                        has_next_page = True
                    else:
                        has_next_page = False
                    return items, has_next_page
            if parent_item['id'] not in ['热门', '推荐', '动态', '影视', '收藏夹', '历史记录'] and parent_item['params']['pf'] !='UP主':
                url = 'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={0}&page={1}'.format(parent_item['id'], page)
                if len(self.cookies) <= 0:
                    self.getCookie()
                rsp = requests.get(url, cookies=self.cookies)
                jo = json.loads(rsp.text)
                items = []
                vodList = jo['data']['result']
                for vod in vodList:
                    aid = str(vod['aid']).strip()
                    title = vod['title'].replace("<em class=\"keyword\">", "").replace("</em>", "").replace("&quot;",'"')
                    img = 'https:' + vod['pic'].strip()
                    remark = vod['duration']
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.Directory,
                            name='[{0}]/{1}'.format(remark, title),
                            id=aid,
                            cover=img,
                            params={
                                'type': 'video',
                                'pf': '',
                            },
                        ))
                if page < jo['data']['numPages']:
                    has_next_page = True
                else:
                    has_next_page = False
                return items, has_next_page
            if parent_item['params']['pf'] =='UP主':
                upheader={
                    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.62',
                    'origin': 'https://space.bilibili.com',
                    'referer': 'https://space.bilibili.com/{0}/video'.format(parent_item['id'])
                }
                url = 'https://api.bilibili.com/x/space/wbi/arc/search?mid={0}&ps=30&tid=0&pn={1}&order=pubdate&order_avoided=true'.format(parent_item['id'], page)
                if len(self.cookies) <= 0:
                    self.getCookie()
                rsp = requests.get(url, cookies=self.cookies, headers=upheader)
                jo = json.loads(rsp.text)
                items = []
                vodList = jo['data']['list']['vlist']
                for vod in vodList:
                    aid = str(vod['aid']).strip()
                    title = vod['title'].replace("<em class=\"keyword\">", "").replace("</em>", "").replace("&quot;",'"')
                    img = vod['pic'].strip()
                    remark = vod['length']
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.Directory,
                            name='[{0}]/{1}'.format(remark, title),
                            id=aid,
                            cover=img,
                            params={
                                'type': 'video',
                                'pf': '',
                            },
                        ))
                if page < jo['data']['page']['ps']:
                    has_next_page = True
                else:
                    has_next_page = False
                return items, has_next_page
            return [], False
        elif parent_item['params']['type'] == 'video':
            items = []
            del_cache('offset')
            if parent_item['params']['pf'] == '影视':
                url = "http://api.bilibili.com/pgc/view/web/season?season_id={0}".format(parent_item['id'])
                rsp = requests.get(url, headers=header)
                jRoot = json.loads(rsp.text)
                jo = jRoot['result']
                pic = jo['cover']
                areas = jo['areas'][0]['name']
                desc = jo['evaluate'].replace('\n\n', '\n').strip()
                ja = jo['episodes']
                for tmpJo in ja:
                    eid = tmpJo['id']
                    cid = str(tmpJo['cid'])
                    name = tmpJo['share_copy']
                    if name =='':
                        name = parent_item['name']
                    remark = time.strftime('%H:%M:%S', time.gmtime(tmpJo['duration']/1000))
                    if remark.startswith('00:'):
                        remark = remark[3:]
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.File,
                            name='[{0}]/{1}'.format(remark, name),
                            cover=pic,
                            description=desc,
                            area=areas,
                            danmakus=[
                                SpiderDanmaku(
                                    'bilibili',
                                    get_danmaku_url('bilibilidanmu' + cid),
                                )
                            ],
                            sources=[
                                SpiderSource(
                                    'Bili',
                                    {
                                        'eid': eid,
                                        'cid': cid,
                                        'pf': '影视',
                                    },
                                )
                            ],
                        ))
                return items, False
            else:
                url = "https://api.bilibili.com/x/web-interface/view?aid={0}".format(parent_item['id'])
                rsp = requests.get(url, headers=header)
                jRoot = json.loads(rsp.text)
                jo = jRoot['data']
                pic = jo['pic']
                desc = jo['desc'].replace('\n\n', '\n').strip()
                ja = jo['pages']
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        name='UP主：' + jo['owner']['name'],
                        id=jo['owner']['mid'],
                        cover=jo['owner']['face'],
                        params={
                            'type': 'category',
                            'pf': 'UP主',
                        },
                    ))
                for tmpJo in ja:
                    cid = str(tmpJo['cid'])
                    name = tmpJo['part']
                    if name =='':
                        name = parent_item['name']
                    remark = time.strftime('%H:%M:%S', time.gmtime(tmpJo['duration']))
                    if remark.startswith('00:'):
                        remark = remark[3:]
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.File,
                            name='[{0}]/{1}'.format(remark, name),
                            cover=pic,
                            description=desc,
                            danmakus=[
                                SpiderDanmaku(
                                    'bilibili',
                                    get_danmaku_url('bilibilidanmu' + cid),
                                )
                            ],
                            sources=[
                                SpiderSource(
                                    'Bili',
                                    {
                                        'eid': parent_item['id'],
                                        'cid': cid,
                                        'pf': '视频',
                                    },
                                )
                            ],
                        ))
                return items, False

    def resolve_play_url(self, source_params):
        del_cache('offset')
        if len(self.cookies) <= 0:
            self.getCookie()
        if self.login is False:
            qrlogth = threading.Thread(target=self.qrlogin, args=(self.key,))
            qrlogth.start()
            xbmcgui.Dialog().notification('扫码登录', 'Cookies已失效，请重新扫码', get_qrcode_url(self.qrurl), 30000,  False)
        header = {
            "Connection": "keep-alive",
            "Referer": "https://www.bilibili.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
        }
        if source_params['pf'] =='影视':
            url = 'https://api.bilibili.com/pgc/player/web/playurl?qn=120&ep_id={0}&cid={1}'.format(source_params['eid'],  source_params['cid'])
            if len(self.cookies) <= 0:
                self.getCookie()
            rsp = requests.get(url, cookies=self.cookies, headers=header)
            jRoot = json.loads(rsp.text)
            if jRoot['message'] != 'success':
                purl = ''
            else:
                jo = jRoot['result']
                ja = jo['durl']
                maxSize = -1
                position = -1
                for i in range(len(ja)):
                    tmpJo = ja[i]
                    if maxSize < int(tmpJo['size']):
                        maxSize = int(tmpJo['size'])
                        position = i
                purl = ''
                if len(ja) > 0:
                    if position == -1:
                        position = 0
                    purl = ja[position]['url']
            return SpiderPlayURL(
                get_proxy_url(
                    Spiderbilibili.__name__,
                    self.proxy_video.__name__,
                    {
                        'url': purl,
                        'headers': header,
                    },
                ))
        else:
            url = 'https://api.bilibili.com:443/x/player/playurl?avid={0}&cid={1}&qn=120&fnval=1&128=128&fourk=1'.format(source_params['eid'], source_params['cid'])
            rsp = requests.get(url, cookies=self.cookies, headers=header)
            jRoot = json.loads(rsp.text)
            jo = jRoot['data']
            ja = jo['durl']
            maxSize = -1
            position = -1
            for i in range(len(ja)):
                tmpJo = ja[i]
                if maxSize < int(tmpJo['size']):
                    maxSize = int(tmpJo['size'])
                    position = i
            purl = ''
            if len(ja) > 0:
                if position == -1:
                    position = 0
                purl = ja[position]['url']
            return SpiderPlayURL(
                get_proxy_url(
                    Spiderbilibili.__name__,
                    self.proxy_video.__name__,
                    {
                        'url': purl,
                        'headers': header,
                    },
                ))

    def search(self, keyword, page=1):
        items = []
        #url = 'https://api.bilibili.com/x/web-interface/search/type?search_type=media_ft&keyword={0}'.format(keyword)
        #if len(self.cookies) <= 0:
            #self.getCookie()
        #rsp = requests.get(url, cookies=self.cookies)
        #jo = json.loads(rsp.text)
        #if jo['data']['numResults'] != 0:
            #vodList = jo['data']['result']
            #for vod in vodList:
                #aid = str(vod['season_id']).strip()
                #title = vod['title'].strip().replace("<em class=\"keyword\">", "").replace("</em>", "")
                #img = vod['eps'][0]['cover'].strip()
                #remark = vod['index_show']
                #items.append(
                    #SpiderItem(
                        #type=SpiderItemType.Directory,
                        #name='哔哩影视：[{0}]/{1}'.format(remark, title),
                        #id=aid,
                        #cover=img,
                        #params={
                            #'type': 'video',
                            #'pf': '影视',
                        #},
                    #))
        #url = 'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={0}'.format(keyword)
        #if len(self.cookies) <= 0:
            #self.getCookie()
        #rsp = requests.get(url, cookies=self.cookies)
        #jo = json.loads(rsp.text)
        #vodList = jo['data']['result']
        #for vod in vodList:
            #aid = str(vod['aid']).strip()
            #title = vod['title'].replace("<em class=\"keyword\">", "").replace("</em>", "").replace("&quot;", '"')
            #img = 'https:' + vod['pic'].strip()
            #remark = vod['duration']
            #items.append(
                #SpiderItem(
                    #type=SpiderItemType.Directory,
                    #name='哔哩视频：[{0}]/{1}'.format(remark, title),
                    #id=aid,
                    #cover=img,
                    #params={
                        #'type': 'video',
                        #'pf': '',
                    #},
                #))
        return items

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

    userid = ''
    def get_userid(self):
        # 获取自己的userid(cookies拥有者)
        url = 'http://api.bilibili.com/x/space/myinfo'
        if len(self.cookies) <= 0:
            self.getCookie()
        rsp = requests.get(url, cookies=self.cookies)
        jo = json.loads(rsp.text)
        if jo['code'] == 0:
            return jo['data']['mid']

    cookies = ''
    login = False
    def getCookie(self):
        cookieList = []
        if 'Bili' in jdata and 'cookie' in jdata['Bili']:
            if jdata['Bili']['cookie'].startswith('http'):
                cookies_str = requests.get(jdata['Bili']['cookie']).text.strip().strip('\n').strip(';')
            else:
                cookies_str = jdata['Bili']['cookie'].strip().strip('\n').strip(';')
        else:
            cookies_str = 'innersign=0; buvid3=FCD51AAE-63B8-CE73-D988-54636BF4704C36347infoc; b_nut=1669872136; i-wanna-go-back=-1; b_ut=7; b_lsid=10D57876A_184CC22A7C3; _uuid=6DF6EAA2-15BA-3EC2-F6C1-107DAE586EA6834100infoc; buvid4=F0055CCC-4918-A008-B7E2-1B7A86CA734C38045-022120113-BXBS6svPlo7xOJLL4rHQkzDUwO8Oa0fwzli7f7k+CkdDu1XJDYGsYQ%3D%3D; buvid_fp=e560dba1f1efe603c96d4136df7a40d0'
        cookieList.append(cookies_str)
        if os.path.exists(cookies_path):
            with open(cookies_path, 'r') as f:
                cookies_str = f.read()
            if cookies_str != '{}':
                cookieList.append(cookies_str)
        for ckL in cookieList:
            if not '{' in ckL:
                cookies_dict = dict([ckL.strip().split('=', 1) for co in cookies_str.split(';')])
            else:
                cookies_dict = json.loads(ckL)
            cookies = requests.utils.cookiejar_from_dict(cookies_dict)
            content = requests.get("http://api.bilibili.com/x/web-interface/nav", cookies=cookies)
            res = json.loads(content.text)
            if res["code"] == 0:
                self.login = True
                self.cookies = cookies
                break
            else:
                self.login = False
                cookies = ''
                r = requests.get("https://passport.bilibili.com/x/passport-login/web/qrcode/generate")
                data = json.loads(r.text)
                if data['code'] == -412:
                    return cookies
                qrurl = data['data']['url']
                key = data['data']['qrcode_key']
                self.qrurl = qrurl
                self.key = key
        return cookies

    def qrlogin(self, key):
        header = {
            "Connection": "keep-alive",
            "Referer": "https://www.bilibili.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
        }
        url ='https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key={}'.format(key)
        r = requests.get(url, headers=header)
        data = json.loads(r.text)
        if data['code'] == -412:
            return
        while data['data']['code'] != 0:
            time.sleep(5)
            r = requests.get(url, headers=header)
            data = json.loads(r.text)
            if data['data']['code'] == 86038:
                break
        cookies_dict = requests.utils.dict_from_cookiejar(r.cookies)
        cookies_str = json.dumps(cookies_dict)
        if cookies_str != '{}':
            with open(cookies_path, 'w') as f:
                f.write(cookies_str)

    def proxy_video(self, ctx, params):
        url = params['url']
        headers = params['headers'].copy()
        self.proxy(ctx, url, headers)

#if __name__ == '__main__':
    #spider = Spiderbilibili()
    #res = spider.list_items(parent_item={'type': 'directory', 'id': '777471370', 'name': '[04:54]/嘎嘎代炒：炒啥啥？不知道！家宴开盲盒！', 'cover': 'http://i0.hdslb.com/bfs/archive/ecca8a472f4277cb7b268531a08ed4cc1cf7744b.jpg', 'description': '', 'cast': [], 'director': '', 'area': '', 'year': 0, 'sources': [], 'danmakus': [], 'subtitles': [], 'params': {'type': 'video', 'pf': ''}}, page=1)
    #res = spider.resolve_play_url({'eid': '903011397', 'cid': '905239153', 'pf': ''})
    #res = spider.search("蜡笔小新")
    #res = spider.getCookie()
    #print(res)
