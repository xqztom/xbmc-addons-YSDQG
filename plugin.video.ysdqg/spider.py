from abc import ABC, abstractmethod
import requests


class Spider(ABC):

    @abstractmethod
    def name(self):
        pass

    def logo(self):
        return ''

    def hide(self):
        return False

    def is_searchable(self):
        return False

    @abstractmethod
    def list_items(self, parent_item=None, page=1):
        pass

    @abstractmethod
    def resolve_play_url(self, source_params):
        pass

    def search(self, keyword, page=1):
        pass

    def proxy(self, ctx, url, headers={}):
        for key in ctx.headers:
            if key.lower() in [
                    'user-agent',
                    'host',
            ]:
                continue
            headers[key] = ctx.headers[key]

        r = requests.get(url, headers=headers, stream=True, verify=False)

        try:
            content_type = r.headers['content-type']
            ctx.send_response(r.status_code)
            for key in r.headers:
                if key.lower() in [
                        'connection',
                        'transfer-encoding',
                ]:
                    continue
                if content_type.lower() in [
                        'application/vnd.apple.mpegurl',
                        'application/x-mpegurl',
                ]:
                    if key.lower() in [
                            'content-length',
                            'content-range',
                            'accept-ranges',
                    ]:
                        continue
                ctx.send_header(key, r.headers[key])
            ctx.end_headers()

            if content_type.lower() in [
                    'application/vnd.apple.mpegurl',
                    'application/x-mpegurl',
            ]:
                for line in r.iter_lines(8192):
                    line = line.decode()
                    if len(line) > 0 and not line.startswith('#'):
                        if not line.startswith('http'):
                            if line.startswith('/'):
                                line = url[:url.index('/', 8)] + line
                            else:
                                line = url[:url.rindex('/') + 1] + line
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


class SpiderItemType(object):
    File = 'file'
    Directory = 'directory'
    Search = 'search'


def SpiderSource(name, params):
    return {
        'name': name,
        'params': params,
    }


def SpiderDanmaku(name, url):
    return {
        'name': name,
        'url': url,
    }


def SpiderSubtitle(name, url):
    return {
        'name': name,
        'url': url,
    }


def SpiderItem(
    type,
    name,
    id='',
    cover='',
    description='',
    director='',
    cast=[],
    area='',
    year=0,
    sources=[],
    danmakus=[],
    subtitles=[],
    params={},
):
    return {
        'type': type,
        'id': str(id).strip(),
        'name': name.strip(),
        'cover': cover,
        'description': description.strip(),
        'cast': cast,
        'director': director,
        'area': area,
        'year': int(year),
        'sources': sources,
        'danmakus': danmakus,
        'subtitles': subtitles,
        'params': params,
    }


def SpiderPlayURL(url, danmakus=[], subtitles=[]):
    return {
        'url': url,
        'danmakus': danmakus,
        'subtitles': subtitles,
    }
