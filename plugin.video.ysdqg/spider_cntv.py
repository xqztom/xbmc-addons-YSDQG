from spider import Spider, SpiderItemType, SpiderItem, SpiderPlayURL, SpiderSource
import re
import requests
from utils import get_image_path
import xbmcaddon

_ADDON = xbmcaddon.Addon()

category = {"cid":[{"n":"CCTV-1综合","v":"EPGC1386744804340101"},{"n":"CCTV-2财经","v":"EPGC1386744804340102"},{"n":"CCTV-3综艺","v":"EPGC1386744804340103"},{"n":"CCTV-4中文国际","v":"EPGC1386744804340104"},{"n":"CCTV-5体育","v":"EPGC1386744804340107"},{"n":"CCTV-6电影","v":"EPGC1386744804340108"},{"n":"CCTV-7国防军事","v":"EPGC1386744804340109"},{"n":"CCTV-8电视剧","v":"EPGC1386744804340110"},{"n":"CCTV-9纪录","v":"EPGC1386744804340112"},{"n":"CCTV-10科教","v":"EPGC1386744804340113"},{"n":"CCTV-11戏曲","v":"EPGC1386744804340114"},{"n":"CCTV-12社会与法","v":"EPGC1386744804340115"},{"n":"CCTV-13新闻","v":"EPGC1386744804340116"},{"n":"CCTV-14少儿","v":"EPGC1386744804340117"},{"n":"CCTV-15音乐","v":"EPGC1386744804340118"},{"n":"CCTV-16奥林匹克","v":"EPGC1634630207058998"},{"n":"CCTV-17农业农村","v":"EPGC1563932742616872"},{"n":"CCTV-5+体育赛事","v":"EPGC1468294755566101"}],"fc":[{"n":"新闻","v":"新闻"},{"n":"体育","v":"体育"},{"n":"综艺","v":"综艺"},{"n":"健康","v":"健康"},{"n":"生活","v":"生活"},{"n":"科教","v":"科教"},{"n":"经济","v":"经济"},{"n":"农业","v":"农业"},{"n":"法治","v":"法治"},{"n":"军事","v":"军事"},{"n":"少儿","v":"少儿"},{"n":"动画","v":"动画"},{"n":"纪实","v":"纪实"},{"n":"戏曲","v":"戏曲"},{"n":"音乐","v":"音乐"},{"n":"影视","v":"影视"}],"fl":[{"n":"A","v":"A"},{"n":"B","v":"B"},{"n":"C","v":"C"},{"n":"D","v":"D"},{"n":"E","v":"E"},{"n":"F","v":"F"},{"n":"G","v":"G"},{"n":"H","v":"H"},{"n":"I","v":"I"},{"n":"J","v":"J"},{"n":"K","v":"K"},{"n":"L","v":"L"},{"n":"M","v":"M"},{"n":"N","v":"N"},{"n":"O","v":"O"},{"n":"P","v":"P"},{"n":"Q","v":"Q"},{"n":"R","v":"R"},{"n":"S","v":"S"},{"n":"T","v":"T"},{"n":"U","v":"U"},{"n":"V","v":"V"},{"n":"W","v":"W"},{"n":"X","v":"X"},{"n":"Y","v":"Y"},{"n":"Z","v":"Z"}]}

class SpiderCNTV(Spider):

    def name(self):
        return '央视'

    def logo(self):
        return get_image_path('yangshi.png')

    def is_searchable(self):
        return False

    def hide(self):
        return not _ADDON.getSettingBool('data_source_yangshi_switch')

    def list_items(self, parent_item=None, page=1):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36",
            "Origin": "https://tv.cctv.com",
            "Referer": "https://tv.cctv.com/"
        }
        if parent_item is None:
            items = []
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id='',
                    name='全部',
                    params={
                        'type': 'category',
                        'pf': 'all',
                    },
                ))
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id='cid',
                    name='频道',
                    params={
                        'type': 'category',
                        'pf': '',
                    },
                ))
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id='fc',
                    name='分类',
                    params={
                        'type': 'category',
                        'pf': '',
                    },
                ))
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id='fl',
                    name='字母',
                    params={
                        'type': 'category',
                        'pf': '',
                    },
                ))
            return items, False

        elif parent_item['params']['type'] == 'category':
            items = []
            pf = parent_item['params']['pf']
            if pf == '':
                data = category[parent_item['id']]
                for id in data:
                    name = id['n']
                    cid = id['v']
                    items.append(
                        SpiderItem(
                            type=SpiderItemType.Directory,
                            name=name,
                            id=cid,
                            params={
                                'type': 'category',
                                'pf': parent_item['id'],
                            },
                        ))
                return items, False
            elif pf != 'all' and pf != '':
                suffix = pf + '=' + parent_item['id']
            else:
                suffix = ''
            url = 'https://api.cntv.cn/lanmu/columnSearch?{0}&n=20&serviceId=tvcctv&t=json'.format(suffix)
            r = requests.get(url=url, headers=header)
            data = r.json()['response']['docs']
            items = []
            for id in data:
                lastVideo = id['lastVIDE']['videoSharedCode']
                if len(lastVideo) == 0:
                    lastVideo = '_'
                name = id['column_name']
                cid = id['column_name']+'###'+lastVideo+'###'+id['column_logo']
                items.append(
                    SpiderItem(
                        type=SpiderItemType.Directory,
                        name=name,
                        id=cid,
                        params={
                            'type': 'video',
                        },
                    ))
            if len(items) == 20:
                has_next_page = True
            else:
                has_next_page = False
            return items, has_next_page

        elif parent_item['params']['type'] == 'video':
            ids = parent_item['id'].split('###')
            cover = ids[2]
            lastVideo = ids[1]
            if lastVideo == '_':
                return []
            lastUrl = 'https://api.cntv.cn/video/videoinfoByGuid?guid={0}&serviceId=tvcctv'.format(lastVideo)
            lastJo = requests.get(lastUrl, headers=header).json()
            topicId = lastJo['ctid']
            url = "https://api.cntv.cn/NewVideo/getVideoListByColumn?id={0}&p=1&n=100&sort=desc&mode=0&serviceId=tvcctv&t=json".format(
                topicId)
            description = lastJo['vset_brief']
            director = lastJo['channel']
            area = lastJo['fc']
            guids = requests.get(url,headers=header).json()['data']['list']
            items = []
            for guid in guids:
                id = guid['guid']
                name = guid['title']
                items.append(
                    SpiderItem(
                        type=SpiderItemType.File,
                        name=name,
                        cover=cover,
                        description=description,
                        director=director,
                        area=area,
                        sources=[
                            SpiderSource(
                                '央视大全',
                                {
                                    'id': id,
                                },
                            )
                        ],
                    ))
            if len(items) == 100:
                has_next_page =True
            else:
                has_next_page = False
            return items, has_next_page
        else:
            return [], False

    def resolve_play_url(self, source_params):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36",
            "Origin": "https://tv.cctv.com",
            "Referer": "https://tv.cctv.com/"
        }
        url = "https://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid={0}".format(source_params['id'])
        jo = requests.get(url, headers=header).json()
        link = jo['hls_url'].strip()
        rsp = requests.get(link, headers=header)
        content = rsp.text.strip()
        arr = content.split('\n')
        urlPrefix = re.search('(http[s]?://[a-zA-z0-9.]+)/', link).group(1)
        subUrl = arr[-1].split('/')
        subUrl[3] = '1200'
        subUrl[-1] = '1200.m3u8'
        hdUrl = urlPrefix + '/'.join(subUrl)
        purl = urlPrefix + arr[-1]
        hdRsp = requests.get(hdUrl, headers=header)
        if hdRsp.status_code == 200:
            purl = hdUrl
        return SpiderPlayURL(purl)


    def search(self, keyword, page=1):
        return []
