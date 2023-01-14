from spider_config import spiders
from spider import SpiderItem, SpiderItemType
from proxy import get_qrcode_url, get_web_url
from spider_aliyundrive import SpiderAliyunDrive
from cache import get_cache, set_cache, del_cache
from danmaku import set_danmaku_url_cache, del_danmaku_url_cache
from playback_record import get_playback_records, add_playback_record, delete_playback_record, PlaybackRecord
from favorite_record import get_favorite_records, add_favorite_record, delete_favorite_record, FavoriteRecord
import re
import sys
import json
import time
import urllib3
import requests
import traceback
import concurrent.futures
from urllib.parse import urlencode, parse_qsl
from utils import get_image_path
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_URL = sys.argv[0]
_HANDLE = int(sys.argv[1])
_ADDON = xbmcaddon.Addon()


def get_url(**kwargs):
    return '{}?{}'.format(_URL, urlencode(kwargs))


def action_homepage():
    xbmcplugin.setPluginCategory(_HANDLE, '数据源')
    list_item = xbmcgui.ListItem(label='插件设置')
    list_item.setArt({'icon': get_image_path('setting.png')})
    xbmcplugin.addDirectoryItem(
        _HANDLE,
        get_url(action='setting'),
        list_item,
        True,
    )

    list_item = xbmcgui.ListItem(label='聚合搜索（全匹配）')
    list_item.setArt({'icon': get_image_path('search.png')})
    xbmcplugin.addDirectoryItem(
        _HANDLE,
        get_url(action='search'),
        list_item,
        True,
    )

    list_item = xbmcgui.ListItem(label='聚合搜索（首字母）')
    list_item.setArt({'icon': get_image_path('search.png')})
    xbmcplugin.addDirectoryItem(
        _HANDLE,
        get_url(action='fuzzy_search'),
        list_item,
        True,
    )

    list_item = xbmcgui.ListItem(label='播放记录')
    list_item.setArt({'icon': get_image_path('playback_records.png')})
    xbmcplugin.addDirectoryItem(
        _HANDLE,
        get_url(action='playback_records'),
        list_item,
        True,
    )

    list_item = xbmcgui.ListItem(label='收藏夹')
    list_item.setArt({'icon': get_image_path('favorite_records.png')})
    xbmcplugin.addDirectoryItem(
        _HANDLE,
        get_url(action='favorite_records'),
        list_item,
        True,
    )

    list_item = xbmcgui.ListItem(label='播放阿里云盘分享链接')
    list_item.setInfo(
        'video', {
            'plot':
            '使用说明:\n1. 扫描二维码或用浏览器访问:\n{}\n2. 提交阿里云盘分享链接\n3. 点击KODI中的播放阿里云分享链接按钮'
            .format(get_web_url()),
        })
    list_item.setArt({'icon': get_qrcode_url('ali')})
    xbmcplugin.addDirectoryItem(
        _HANDLE,
        get_url(action='aliyundrive_share_url'),
        list_item,
        True,
    )

    for spider_class in spiders:
        spider = spiders[spider_class]
        if spider.hide():
            continue
        list_item = xbmcgui.ListItem(label=spider.name())
        list_item = xbmcgui.ListItem(label='数据源:{}'.format(spider.name()))
        list_item.setArt({
            'icon': spider.logo(),
        })
        url = get_url(
            action='list_items',
            spider_class=spider_class,
        )
        is_folder = True
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)

    xbmcplugin.endOfDirectory(_HANDLE)


def action_list_items(spider_class, parent_item=None, page=1):
    spider = spiders[spider_class]
    if parent_item is None:
        xbmcplugin.setPluginCategory(_HANDLE, spider.name())
        if spider.is_searchable():
            list_item = xbmcgui.ListItem(label='搜索（全匹配）')
            list_item.setArt({'icon': get_image_path('search.png')})
            xbmcplugin.addDirectoryItem(
                _HANDLE,
                get_url(action='search', spider_class=spider_class),
                list_item,
                True,
            )
            list_item = xbmcgui.ListItem(label='搜索（首字母）')
            list_item.setArt({'icon': get_image_path('search.png')})
            xbmcplugin.addDirectoryItem(
                _HANDLE,
                get_url(action='fuzzy_search', spider_class=spider_class),
                list_item,
                True,
            )
    else:
        xbmcplugin.setPluginCategory(_HANDLE, parent_item['name'])
        list_item = xbmcgui.ListItem(label='添加到收藏夹')
        list_item.setArt({'icon': get_image_path('add_favorite_record.png')})
        xbmcplugin.addDirectoryItem(
            _HANDLE,
            get_url(
                action='add_favorite_record',
                spider_class=spider_class,
                item=json.dumps(parent_item),
            ),
            list_item,
            False,
        )
    items, has_next_page = spider.list_items(parent_item, page)
    for item in items:
        list_item = xbmcgui.ListItem(label=item['name'])
        list_item.setInfo(
            'video', {
                'title': item['name'],
                'plot': item['description'],
                'cast': item['cast'],
                'director': item['director'],
                'country': item['area'],
                'year': item['year'],
                'mediatype': 'video'
            })
        if item['type'] == SpiderItemType.File:
            list_item.setProperty('IsPlayable', 'true')
            list_item.setArt({
                'icon' : item['cover']
                if len(item['cover']) > 0 else get_image_path('picture.png'),})
            url = get_url(
                action='resolve_play_url',
                spider_class=spider_class,
                parent_item=json.dumps(parent_item),
                item=json.dumps(item),
            )
            is_folder = False
        elif item['type'] == SpiderItemType.Search:
            list_item.setArt({
                'icon' : item['cover']
                if len(item['cover']) > 0 else get_image_path('folder.png'),})
            url = get_url(
                action='search',
                spider_class=spider_class,
                keyword=item['name'].split('/', 1)[-1],
            )
            is_folder = True
        else:
            list_item.setArt({
                'icon' : item['cover']
                if len(item['cover']) > 0 else get_image_path('folder.png'),})
            url = get_url(
                action='list_items',
                spider_class=spider_class,
                parent_item=json.dumps(item),
            )
            is_folder = True
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    if has_next_page and len(items) > 0:
        list_item = xbmcgui.ListItem(label='下一页')
        list_item.setArt({'icon': get_image_path('folder.png')})
        xbmcplugin.addDirectoryItem(
            _HANDLE,
            get_url(
                action='list_items',
                spider_class=spider_class,
                parent_item=json.dumps(parent_item),
                page=page + 1,
            ),
            list_item,
            True,
        )
    xbmcplugin.endOfDirectory(_HANDLE)


def action_resolve_play_url(spider_class, parent_item, item):
    spider = spiders[spider_class]
    if len(item['sources']) > 1 and _ADDON.getSettingBool('source_dialog_switch'):
        names = []
        if 'params' in item and 'speedtest' in item['params'] and str(item['params']['speedtest']) != '0':
            i = 0
            contents = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=item['params']['thlimit']) as executor:
                checkPurl = []
                try:
                    for source in item['sources']:
                        future = executor.submit(spider.checkPurl, source['params'], str(i))
                        checkPurl.append(future)
                        i = i + 1
                    for future in concurrent.futures.as_completed(checkPurl, timeout=10):
                        contents.append(future.result())
                except Exception:
                    executor.shutdown(wait=False)
            item_sources = []
            for content in contents:
                if content == None:
                    continue
                if len(content) == 2:
                    strnum = list(content[0].keys())[0]
                    speed = content[0][strnum]
                    url = content[1]
                else:
                    strnum = list(content.keys())[0]
                    speed = content[strnum]
                    url = ''
                name = '速度：{:.1f} MB/s'.format(speed / 1024 ** 2)
                spLimtnum = re.search(r'\d+', item['params']['speedtest']).group(0)
                spLend = item['params']['speedtest'].replace(spLimtnum, '').lower()
                if 'k' in spLend:
                    speedLimit = int(spLimtnum) * 1024
                elif 'm' in spLend:
                    speedLimit = int(spLimtnum) * 1024 ** 2
                elif 'g' in spLend:
                    speedLimit = int(spLimtnum) * 1024 ** 3
                else:
                    speedLimit = 0
                if speed >= speedLimit:
                    item['sources'][int(strnum)]['name'] = name
                    item['sources'][int(strnum)]['params'].update({'speed': speed})
                    if url != '':
                        item['sources'][int(strnum)]['params']['url'] = url
                    item_sources.append(item['sources'][int(strnum)])
            item['sources'] = item_sources
            item['sources'].sort(key=lambda i: i['params']['speed'], reverse=True)
            for source in item['sources']:
                names.append(source['name'])
        else:
            for source in item['sources']:
                names.append(source['name'])
        if len(item['sources']) > 1:
            ret = xbmcgui.Dialog().select('请选择播放源', names, preselect=0)
            if ret >= 0:
                source = item['sources'][ret]
            else:
                source = item['sources'][0]
        else:
            if len(item['sources']) == 0:
                xbmcgui.Dialog().ok('提示', '该资源无可播放源，或资源播放速度低于{}'.format(item['params']['speedtest']))
                return
            source = item['sources'][0]
    else:
        if 'params' in item and 'speedtest' in item['params'] and str(item['params']['speedtest']) != '0':
            content = spider.checkPurl(item['sources'][0]['params'], '0')
            if len(content) == 2:
                speed = content[0]['0']
                url = content[1]
            else:
                speed = content['0']
                url = ''
            spLimtnum = re.search(r'\d+', item['params']['speedtest']).group(0)
            spLend = item['params']['speedtest'].replace(spLimtnum, '').lower()
            if 'k' in spLend:
                speedLimit = int(spLimtnum) * 1024
            elif 'm' in spLend:
                speedLimit = int(spLimtnum) * 1024 ** 2
            elif 'g' in spLend:
                speedLimit = int(spLimtnum) * 1024 ** 3
            else:
                speedLimit = 0
            item_sources = []
            if speed >= speedLimit:
                item['sources'][0]['params'].update({'speed': speed})
                if url != '':
                    item['sources'][0]['params']['url'] = url
                item_sources.append(item['sources'][0])
            if len(item['sources']) == 0:
                xbmcgui.Dialog().ok('提示', '该资源无可播放源，或资源播放速度低于{}'.format(item['params']['speedtest']))
                return
        source = item['sources'][0]
    danmakus = item['danmakus']
    subtitles = item['subtitles']
    play_url = spider.resolve_play_url(source['params'])
    if len(play_url['danmakus']) > 0:
        danmakus = play_url['danmakus']
    if len(play_url['subtitles']) > 0:
        danmakus = play_url['subtitles']
    play_item = xbmcgui.ListItem(path=play_url['url'])
    if len(danmakus) > 0 and _ADDON.getSettingBool('danmaku_switch'):
        danmaku = None
        if len(danmakus) > 1 and _ADDON.getSettingBool('danmaku_dialog_switch'):
            names = []
            for danmaku in danmakus:
                names.append(danmaku['name'])
            ret = xbmcgui.Dialog().select('请选择弹幕或取消', names, preselect=0)
            if ret >= 0:
                danmaku = danmakus[ret]
        else:
            danmaku = danmakus[0]
        if danmaku:
            if 'bilibilidanmu' in danmaku['url']:
                oid = danmaku['url'].split('bilibilidanmu')[1]
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    try:
                        executor.submit(spider.getDanm, oid).result(timeout=10)
                    except Exception:
                        executor.shutdown(wait=False)
            set_danmaku_url_cache(danmaku['url'])
        else:
            del_danmaku_url_cache()
    elif len(subtitles) > 0:
        subtitle = None
        if len(subtitles) > 1:
            names = []
            for subtitle in subtitles:
                names.append(subtitle['name'])
            ret = xbmcgui.Dialog().select('请选择字幕或取消', names)
            if ret >= 0:
                subtitle = subtitles[ret]
        else:
            subtitle = subtitles[0]
        if subtitle:
            if subtitle['url'].startswith('alist@@@'):
                subtitle['url'] = spider.resolve_subtitles(subtitle['url'])
            play_item.setSubtitles([subtitle['url']])
    if parent_item is not None:
        add_playback_record(PlaybackRecord(spider_class, parent_item, item))
    xbmcplugin.setResolvedUrl(_HANDLE, True, listitem=play_item)


def action_search(spider_class='', keyword='', page=1):
    xbmcplugin.setPluginCategory(_HANDLE, '搜索结果')
    if len(keyword) == 0:
        kb = xbmc.Keyboard('', '请输入影片名称')
        kb.doModal()
        if not kb.isConfirmed():
            return
        keyword = kb.getText()
    for cls in spiders:
        if len(spider_class) > 0 and cls != spider_class:
            continue
        spider = spiders[cls]
        if spider.is_searchable() is False:
            continue
        items, has_next_page = spider.search(keyword, page)
        if spider.hide():
            continue
        try:
            for item in items:
                if spider_class:
                    name = item['name']
                else:
                    name = item['name']
                list_item = xbmcgui.ListItem(label=name)
                list_item.setInfo(
                    'video', {
                        'title': name,
                        'plot': item['description'],
                        'cast': item['cast'],
                        'director': item['director'],
                        'country': item['area'],
                        'year': item['year'],
                        'mediatype': 'video'
                    })
                if item['type'] == SpiderItemType.File:
                    list_item.setProperty('IsPlayable', 'true')
                    list_item.setArt({
                        'icon': item['cover']
                        if len(item['cover']) > 0 else get_image_path('picture.png'),})
                    url = get_url(
                        action='resolve_play_url',
                        spider_class=cls,
                        item=json.dumps(item),
                    )
                    is_folder = False
                else:
                    list_item.setArt({
                        'icon': item['cover'] if len(item['cover']) > 0 else get_image_path('folder.png'),})
                    url = get_url(
                        action='list_items',
                        spider_class=cls,
                        parent_item=json.dumps(item),
                    )
                    is_folder = True
                xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
        except Exception:
            print(traceback.format_exc())
        if has_next_page and len(items) > 0:
            list_item = xbmcgui.ListItem(label='下一页')
            list_item.setArt({'icon': get_image_path('folder.png')})
            xbmcplugin.addDirectoryItem(
                _HANDLE,
                get_url(
                    action='search',
                    spider_class=spider_class,
                    keyword=keyword,
                    page=page + 1,
                ),
                list_item,
                True,
            )
    xbmcplugin.endOfDirectory(_HANDLE)


def action_fuzzy_search(spider_class=''):
    xbmcplugin.setPluginCategory(_HANDLE, '热门搜索')
    kb = xbmc.Keyboard('', '请输入影片名称的拼音首字母')
    kb.doModal()
    if not kb.isConfirmed():
        return
    keyword = kb.getText()
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
        'Referer': 'https://www.iqiyi.com/'
    }
    r = requests.get('https://suggest.video.iqiyi.com/', headers=header, params={'key': keyword})
    data = json.loads(r.text)
    if 'data' in data and len(data['data']) > 0:
        data = data['data']
        tag = 'name'
    else:
        r = requests.get('http://s.video.qq.com/smartbox',
                         params={
                             'plat': 2,
                             'ver': 0,
                             'num': 10,
                             'otype': 'json',
                             'query': keyword,
                         })
        data = json.loads(r.text[13:len(r.text) - 1])
        tag = 'word'
        if 'item' in data:
            data = data['item']
        else:
            data = []
    for item in data:
        list_item = xbmcgui.ListItem(label=item[tag])
        url = get_url(
            action='search',
            spider_class=spider_class,
            keyword=item[tag],
        )
        is_folder = True
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_HANDLE)


def action_playback_records():
    xbmcplugin.setPluginCategory(_HANDLE, '播放记录')
    records = get_playback_records()
    for record in records:
        spider = spiders[record['spider_class']]
        parent_item = record['parent_item']
        item = record['item']
        list_item = xbmcgui.ListItem(label='{}:{}:{}'.format(
            spider.name(), parent_item['name'], item['name']))
        list_item.setInfo(
            'video', {
                'title': parent_item['name'],
                'plot': parent_item['description'],
                'cast': parent_item['cast'],
                'director': parent_item['director'],
                'country': parent_item['area'],
                'year': parent_item['year'],
                'mediatype': 'video'
            })
        list_item.setArt({
            'icon':
            parent_item['cover'] if len(parent_item['cover']) > 0 else
            get_image_path('picture.png'),
        })
        url = get_url(
            action='playback_record',
            record=json.dumps(record),
            ts=str(int(time.time())),
        )
        is_folder = True
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_HANDLE)


def action_playback_record(record, ts=0):
    key = 'last_opened_playback_record'
    just_opended = False
    data = get_cache(key)
    if data:
        data = json.loads(data)
        last_record = data['record']
        last_ts = data['ts']
        just_opended = last_record['spider_class'] == record[
            'spider_class'] and last_record['parent_item']['id'] == record[
                'parent_item']['id'] and last_ts == ts
    if not just_opended:
        options = ['打开', '删除']
        ret = xbmcgui.Dialog().select('请选择要执行的操作', options, preselect=0)
        if ret >= 0:
            option = options[ret]
            if option == '删除':
                delete_playback_record(record)
                return
    action_list_items(record['spider_class'], record['parent_item'])
    set_cache(key, json.dumps({'record': record, 'ts': ts}))


def action_setting():
    _ADDON.openSettings()


def action_aliyundrive_share_url():
    aliyundrive_share_url = get_cache('aliyundrive_share_url').strip()
    if aliyundrive_share_url:
        del_cache('aliyundrive_share_url')
    else:
        kb = xbmc.Keyboard('', '请输入阿里云盘分享链接')
        kb.doModal()
        if not kb.isConfirmed():
            return
        aliyundrive_share_url = kb.getText().strip()
    spider_class = SpiderAliyunDrive.__name__
    action_list_items(
        spider_class,
        parent_item=SpiderItem(
            type=SpiderItemType.Directory,
            id=aliyundrive_share_url,
            name=aliyundrive_share_url,
        ),
    )


def action_add_favorite_record(spider_class, item):
    ret = xbmcgui.Dialog().yesno('提示', '是否要添加到收藏夹?')
    if ret:
        add_favorite_record(FavoriteRecord(spider_class, item))


def action_favorite_records():
    xbmcplugin.setPluginCategory(_HANDLE, '收藏夹')

    records = get_favorite_records()
    for record in records:
        spider = spiders[record['spider_class']]
        item = record['item']
        list_item = xbmcgui.ListItem(
            label='{}:{}'.format(spider.name(), item['name']))
        list_item.setInfo(
            'video', {
                'title': item['name'],
                'plot': item['description'],
                'cast': item['cast'],
                'director': item['director'],
                'country': item['area'],
                'year': item['year'],
                'mediatype': 'video'
            })
        list_item.setArt({
            'icon':
            item['cover']
            if len(item['cover']) > 0 else get_image_path('picture.png'),
        })
        url = get_url(action='favorite_record',
                      record=json.dumps(record),
                      ts=str(int(time.time())))
        is_folder = True
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)

    xbmcplugin.endOfDirectory(_HANDLE)


def action_favorite_record(record, ts=0):
    key = 'last_opened_favorite_record'
    just_opended = False
    data = get_cache(key)
    if data:
        data = json.loads(data)
        last_record = data['record']
        last_ts = data['ts']
        just_opended = last_record['spider_class'] == record[
            'spider_class'] and last_record['item']['id'] == record['item'][
                'id'] and last_ts == ts

    if not just_opended:
        options = ['打开', '删除']
        ret = xbmcgui.Dialog().select('请选择要执行的操作', options, preselect=0)
        if ret >= 0:
            option = options[ret]
            if option == '删除':
                delete_favorite_record(record)
                return

    action_list_items(record['spider_class'], record['item'])
    set_cache(key, json.dumps({'record': record, 'ts': ts}))


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'list_items':
            action_list_items(
                params['spider_class'],
                json.loads(params['parent_item'])
                if 'parent_item' in params else None,
                int(params['page']) if 'page' in params else 1,
            )
        elif params['action'] == 'resolve_play_url':
            action_resolve_play_url(
                params['spider_class'],
                json.loads(params['parent_item'])
                if 'parent_item' in params else None,
                json.loads(params['item']),
            )
        elif params['action'] == 'search':
            action_search(
                params['spider_class'] if 'spider_class' in params else '',
                params['keyword'] if 'keyword' in params else '',
                int(params['page']) if 'page' in params else 1,
            )
        elif params['action'] == 'fuzzy_search':
            action_fuzzy_search(params['spider_class'] if 'spider_class' in
                                params else '')
        elif params['action'] == 'playback_records':
            action_playback_records()
        elif params['action'] == 'playback_record':
            action_playback_record(
                json.loads(params['record']),
                int(params['ts'] if 'ts' in params else 0),
            )
        elif params['action'] == 'setting':
            action_setting()
        elif params['action'] == 'aliyundrive_share_url':
            action_aliyundrive_share_url()
        elif params['action'] == 'add_favorite_record':
            action_add_favorite_record(
                params['spider_class'],
                json.loads(params['item']),
            )
        elif params['action'] == 'favorite_records':
            action_favorite_records()
        elif params['action'] == 'favorite_record':
            action_favorite_record(
                json.loads(params['record']),
                int(params['ts'] if 'ts' in params else 0),
            )
        else:
            raise ValueError('Invalid paramstring: {}!'.format(paramstring))
    else:
        action_homepage()


if __name__ == '__main__':
    router(sys.argv[2][1:])

