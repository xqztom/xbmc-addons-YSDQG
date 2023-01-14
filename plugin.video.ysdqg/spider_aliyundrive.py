from spider import Spider, SpiderItemType, SpiderItem, SpiderSource, SpiderSubtitle, SpiderPlayURL
import re
import time
import json
import requests
from proxy import get_proxy_url
from cache import get_cache, set_cache
from downloader import Downloader
import xbmcgui
import xbmcaddon

_ADDON = xbmcaddon.Addon()

base_headers = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36',
    'Referer': 'https://www.aliyundrive.com/',
}

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

class SpiderAliyunDrive(Spider):
    regex_share_id = re.compile(
        r'www.aliyundrive.com\/s\/([^\/]+)(\/folder\/([^\/]+))?')
    cache = {}

    def name(self):
        return '阿里云盘'

    def hide(self):
        return True

    def list_items(self, parent_item=None, page=1):
        if parent_item is None:
            return [], False
        m = self.regex_share_id.search(parent_item['id'])
        share_id = m.group(1)
        file_id = m.group(3)
        r = requests.post(
            'https://api.aliyundrive.com/adrive/v3/share_link/get_share_by_anonymous',
            json={'share_id': share_id})
        share_info = r.json()
        if len(share_info['file_infos']) == 0:
            return [], False
        file_info = None
        if file_id:
            for fi in share_info['file_infos']:
                if fi['file_id'] == file_id:
                    file_info = fi
                    break
            if file_info is None:
                share_token = self._get_share_token(share_id)
                headers = base_headers.copy()
                headers['x-share-token'] = share_token
                r = requests.post(
                    'https://api.aliyundrive.com/v2/file/get',
                    json={
                        'fields':
                        '*',
                        'file_id':
                        file_id,
                        'image_thumbnail_process':
                        'image/resize,w_400/format,jpeg',
                        'image_url_process':
                        'image/resize,w_375/format,jpeg',
                        'share_id':
                        share_id,
                        'video_thumbnail_process':
                        'video/snapshot,t_1000,f_jpg,ar_auto,w_375',
                    },
                    headers=headers)
                file_info = r.json()
        else:
            if len(share_info['file_infos']) == 0:
                return [], False
            file_info = share_info['file_infos'][0]
            file_id = file_info['file_id']
        parent_file_id = None
        if file_info['type'] == 'folder':
            parent_file_id = file_id
        elif file_info['type'] == 'file' and file_info['category'] == 'video':
            parent_file_id = 'root'
        else:
            return [], False
        dir_infos, video_infos, subtitle_infos = self._list_files(
            share_id,
            parent_file_id,
        )
        items = []
        for dir_info in dir_infos:
            items.append(
                SpiderItem(
                    type=SpiderItemType.Directory,
                    id='https://www.aliyundrive.com/s/{}/folder/{}'.format(
                        share_id, dir_info['file_id']),
                    name=dir_info['name'],
                    cover=share_info['avatar'],
                    params={
                        'type': 'category',
                        'pf': 'ali'
                    }
                ))
        subtitles = []
        subtitle_infos.sort(key=lambda x: x['name'])
        for subtitle_info in subtitle_infos:
            subtitles.append(
                SpiderSubtitle(
                    subtitle_info['name'],
                    get_proxy_url(
                        SpiderAliyunDrive.__name__,
                        self.proxy_download_file.__name__,
                        {
                            'share_id': subtitle_info['share_id'],
                            'file_id': subtitle_info['file_id'],
                            'drive_id': subtitle_info['drive_id'],
                        },
                    )))
        video_infos.sort(key=lambda x: x['name'])
        display_file_size = _ADDON.getSettingBool('aliyundrive_display_file_size_switch')
        # display_file_size = True
        for video_info in video_infos:
            sources = [
                SpiderSource(
                    '原画',
                    {
                        'template_id': '',
                        'share_id': video_info['share_id'],
                        'file_id': video_info['file_id'],
                        'drive_id': video_info['drive_id'],
                        'pf': 'ali'
                    },
                ),
                SpiderSource(
                    '超清',
                    {
                        'template_id': 'FHD',
                        'share_id': video_info['share_id'],
                        'file_id': video_info['file_id'],
                        'drive_id': video_info['drive_id'],
                        'pf': 'ali'
                    },
                ),
                SpiderSource(
                    '高清',
                    {
                        'template_id': 'HD',
                        'share_id': video_info['share_id'],
                        'file_id': video_info['file_id'],
                        'drive_id': video_info['drive_id'],
                        'pf': 'ali'
                    },
                ),
                SpiderSource(
                    '标清',
                    {
                        'template_id': 'SD',
                        'share_id': video_info['share_id'],
                        'file_id': video_info['file_id'],
                        'drive_id': video_info['drive_id'],
                        'pf': 'ali'
                    },
                )
            ]

            if display_file_size:
                name = '[{}]/{}'.format(
                    self._sizeof_fmt(video_info['size']),
                    video_info['name'],
                )
            else:
                name = video_info['name']

            items.append(
                SpiderItem(
                    type=SpiderItemType.File,
                    name=name,
                    sources=sources,
                    cover=share_info['avatar'],
                    description=parent_item['id'],
                    subtitles=subtitles,
                    params={
                        'pf': 'ali'
                    }
                ))
        return items, False

    def resolve_play_url(self, source_params):
        if len(source_params['template_id']) == 0:
            params = source_params.copy()
            params['downloader_switch'] = _ADDON.getSettingBool('downloader_switch')
            # params['downloader_switch'] = False
            return SpiderPlayURL(
                get_proxy_url(
                    spider_class=SpiderAliyunDrive.__name__,
                    func_name=self.proxy_download_file.__name__,
                    params=params,
                ))
        else:
            return SpiderPlayURL(
                get_proxy_url(
                    SpiderAliyunDrive.__name__,
                    self.proxy_preview_m3u8.__name__,
                    source_params,
                ))

    def search(self, keyword, page=1):
        return []

    def _get_refresh_token(self):
        if 'Ali' in jdata and 'token' in jdata['Ali']:
            if jdata['Ali']['token'].startswith('http://') or jdata['Ali']['token'].startswith('https://'):
                token = requests.get(jdata['Ali']['token']).text.strip().strip('\n')
            else:
                token = jdata['Ali']['token'].strip().strip('\n')
        else:
            token = jsonurl
        return token

    def _get_access_token(self):
        key = 'aliyundrive:access_token'
        data = self._get_cache(key)
        if data:
            return data['access_token']

        r = requests.post('https://api.aliyundrive.com/token/refresh',
                          json={
                              'refresh_token': self._get_refresh_token(),
                          })
        data = r.json()

        if 'token_type' not in data:
            xbmcgui.Dialog().ok('提示','请尝试更换阿里云盘Token并重启Kodi\n' + r.text)
            return None

        access_token = '{} {}'.format(data['token_type'], data['access_token'])
        expires_at = int(time.time()) + int(data['expires_in'] / 2)
        self._set_cache(key, {
            'access_token': access_token,
            'expires_at': expires_at
        })
        return access_token

    def _get_share_token(self, share_id, share_pwd=''):
        key = 'aliyundrive:share_token'
        data = self._get_cache(key)
        if data:
            if data['share_id'] == share_id and data['share_pwd'] == share_pwd:
                return data['share_token']

        r = requests.post(
            'https://api.aliyundrive.com/v2/share_link/get_share_token',
            json={
                'share_id': share_id,
                'share_pwd': share_pwd
            })
        data = r.json()

        share_token = data['share_token']
        expires_at = int(time.time()) + int(data['expires_in'] / 2)
        self._set_cache(
            key, {
                'share_token': share_token,
                'expires_at': expires_at,
                'share_id': share_id,
                'share_pwd': share_pwd
            })
        return share_token

    def _list_files(self, share_id, parent_file_id):
        dir_infos = []
        video_infos = []
        subtitle_infos = []

        marker = ''
        share_token = self._get_share_token(share_id)
        headers = base_headers.copy()
        headers['x-share-token'] = share_token
        for page in range(1, 51):
            if page >= 2 and len(marker) == 0:
                break

            r = requests.post(
                'https://api.aliyundrive.com/adrive/v3/file/list',
                json={
                    "image_thumbnail_process":
                    "image/resize,w_160/format,jpeg",
                    "image_url_process": "image/resize,w_1920/format,jpeg",
                    "limit": 200,
                    "order_by": "updated_at",
                    "order_direction": "DESC",
                    "parent_file_id": parent_file_id,
                    "share_id": share_id,
                    "video_thumbnail_process":
                    "video/snapshot,t_1000,f_jpg,ar_auto,w_300",
                    'marker': marker,
                },
                headers=headers)
            data = r.json()

            for item in data['items']:
                if item['type'] == 'folder':
                    dir_infos.append(item)
                elif item['type'] == 'file' and item['category'] == 'video':
                    video_infos.append(item)
                elif item['type'] == 'file' and item['file_extension'] in [
                        'srt', 'ass', 'vtt'
                ]:
                    subtitle_infos.append(item)

            marker = data['next_marker']

        return dir_infos, video_infos, subtitle_infos

    def _get_m3u8_cache(self, share_id, file_id, template_id):
        key = 'aliyundrive:m3u8'
        data = self._get_cache(key)
        if data:
            if data['share_id'] == share_id and data[
                    'file_id'] == file_id and data[
                        'template_id'] == template_id:
                return data['m3u8'], data['media_urls']

        access_token = self._get_access_token()
        share_token = self._get_share_token(share_id)

        headers = base_headers.copy()
        headers['x-share-token'] = share_token
        headers['Authorization'] = access_token
        r = requests.post(
            'https://api.aliyundrive.com/v2/file/get_share_link_video_preview_play_info',
            json={
                'share_id': share_id,
                'category': 'live_transcoding',
                'file_id': file_id,
                'template_id': '',
            },
            headers=headers,
        )

        preview_url = ''
        for t in r.json(
        )['video_preview_play_info']['live_transcoding_task_list']:
            if t['template_id'] == template_id:
                preview_url = t['url']
                break

        r = requests.get(preview_url,
                         headers=base_headers.copy(),
                         allow_redirects=False)
        preview_url = r.headers['Location']

        lines = []
        media_urls = []
        r = requests.get(preview_url, headers=base_headers.copy(), stream=True)
        media_id = 0
        for line in r.iter_lines():
            line = line.decode()
            if 'x-oss-expires' in line:
                media_url = preview_url[:preview_url.rindex('/') + 1] + line
                media_urls.append(media_url)
                line = get_proxy_url(
                    SpiderAliyunDrive.__name__,
                    self.proxy_preview_media.__name__, {
                        'share_id': share_id,
                        'file_id': file_id,
                        'template_id': template_id,
                        'media_id': media_id
                    })
                media_id += 1
            lines.append(line)
        m3u8 = '\n'.join(lines)

        self._set_cache(
            key, {
                'share_id': share_id,
                'file_id': file_id,
                'template_id': template_id,
                'm3u8': m3u8,
                'media_urls': media_urls,
                'expires_at': int(time.time()) + 300,
            })

        return m3u8, media_urls

    def _get_download_url(self, share_id, file_id):
        key = 'aliyundrive:download_url:{}:{}'.format(share_id, file_id)
        data = self._get_cache(key)
        if data:
            return data['download_url']

        access_token = self._get_access_token()
        share_token = self._get_share_token(share_id)

        headers = base_headers.copy()
        headers['x-share-token'] = share_token
        headers['Authorization'] = access_token
        r = requests.post(
            'https://api.aliyundrive.com/v2/file/get_share_link_download_url',
            json={
                'share_id': share_id,
                'file_id': file_id,
                'expires_sec': 7200,
            },
            headers=headers)
        data = r.json()

        r = requests.get(data['download_url'],
                         headers=base_headers.copy(),
                         allow_redirects=False)
        download_url = r.headers['Location']
        self._set_cache(
            key, {
                'download_url': download_url,
                'expires_at': int(time.time()) + 300,
                'share_id': share_id,
                'file_id': file_id,
            })

        return download_url

    def _sizeof_fmt(self, num, suffix="B"):
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if num < 1024.0:
                return f"{num:3.1f} {unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f}Yi{suffix}"

    def _get_cache(self, key):
        if key in self.cache:
            data = self.cache[key]
            if data['expires_at'] >= int(time.time()):
                return data

        data = get_cache(key)
        if data:
            data = json.loads(data)
            if data['expires_at'] >= int(time.time()):
                return data

        return None

    def _set_cache(self, key, value):
        set_cache(key, json.dumps(value))
        self.cache[key] = value

    def proxy_download_file(self, ctx, params):
        share_id = params['share_id']
        file_id = params['file_id']
        downloader_switch = params[
            'downloader_switch'] if 'downloader_switch' in params else None

        if downloader_switch:
            headers = base_headers.copy()
            for key in ctx.headers:
                if key.lower() in [
                        'user-agent',
                        'host',
                ]:
                    continue
                headers[key] = ctx.headers[key]

            def get_url_and_headers():
                return self._get_download_url(share_id,
                                              file_id), headers.copy()

            connection = _ADDON.getSettingInt('downloader_connection')
            # connection = 5
            downloader = Downloader(
                get_url_and_headers=get_url_and_headers,
                headers=headers,
                connection=connection,
            )

            try:
                if 'Range' in ctx.headers:
                    ctx.send_response(206)
                else:
                    ctx.send_response(200)

                res_headers = downloader.start()
                for key in res_headers:
                    if key.lower() in ['connection']:
                        continue
                    value = res_headers[key]
                    ctx.send_header(key, value)
                ctx.end_headers()

                while True:
                    chunk = downloader.read()
                    if chunk is None:
                        break
                    ctx.wfile.write(chunk)
            except Exception as e:
                print(e)
            finally:
                try:
                    downloader.stop()
                except:
                    pass
        else:
            download_url = self._get_download_url(share_id, file_id)
            self.proxy(ctx, download_url, base_headers.copy())

    def proxy_preview_m3u8(self, ctx, params):
        share_id = params['share_id']
        file_id = params['file_id']
        template_id = params['template_id']
        m3u8, _ = self._get_m3u8_cache(share_id, file_id, template_id)

        try:
            ctx.send_response(200)
            ctx.send_header('Content-Type', 'application/vnd.apple.mpegurl')
            ctx.end_headers()
            ctx.wfile.write(m3u8.encode())
        except Exception as e:
            print(e)

    def proxy_preview_media(self, ctx, params):
        share_id = params['share_id']
        file_id = params['file_id']
        template_id = params['template_id']
        media_id = params['media_id']
        _, media_urls = self._get_m3u8_cache(share_id, file_id, template_id)
        media_url = media_urls[media_id]
        self.proxy(ctx, media_url, base_headers.copy())
