from queue import Queue
import requests
import re
import threading
import time


class Downloader(object):

    def __init__(
            self,
            url='',
            headers={},
            get_url_and_headers=None,
            chunk_size=1024 * 1024,
            buffer_size=1024 * 64,
            prefetch_size=1024 * 256,
            max_buffered_chunk=100,
            #chunk_size=4,
            #buffer_size=2,
            #prefetch_size=8,
            connection=30,
            timeout=10):
        self.url = url
        self.headers = headers
        self.get_url_and_headers = get_url_and_headers
        self.chunk_size = chunk_size
        self.buffer_size = buffer_size
        self.prefetch_size = prefetch_size
        self.max_buffered_chunk = max_buffered_chunk
        self.connection = connection
        self.timeout = timeout
        self.running = False
        self.file_size = -1
        self.content_length = -1
        self.start_offset = -1
        self.end_offset = -1
        self.current_offset = -1
        self.pending_chunk_queue = Queue()
        self.ready_chunk_queue = Queue()
        self.current_chunk = None
        self.last_read = -1
        self.lock = threading.Lock()
        self.session = requests.session()
        self.id = time.time()

    def start(self):
        if 'Range' not in self.headers:
            self.headers['Range'] = 'bytes=0-'
        m = re.search(r'bytes=(\d+)-(\d+)?', self.headers['Range'])
        self.start_offset = int(m.group(1))
        if m.group(2):
            self.end_offset = int(m.group(2))
            content_length = self.end_offset - self.start_offset + 1
            if self.prefetch_size > content_length:
                self.prefetch_size = content_length

        if self.get_url_and_headers:
            url, headers = self.get_url_and_headers()
            headers.update(self.headers)
        else:
            url = self.url
            headers = self.headers

        r = self.session.get(url, headers=headers, verify=False, stream=True)

        datas = []
        prefetch_size = 0
        for data in r.iter_content(self.buffer_size):
            datas.append(data)
            prefetch_size += len(data)
            if prefetch_size >= self.prefetch_size:
                break
        self.prefetch_size = prefetch_size
        r.close()

        chunk = Chunk(self.start_offset,
                      self.start_offset + self.prefetch_size - 1)
        for data in datas:
            chunk.queue.put(data)
        self.ready_chunk_queue.put(chunk)

        m = re.search(r'.*/(\d+)', r.headers['content-range'])
        self.file_size = int(m.group(1))
        if self.end_offset < 0:
            self.end_offset = self.file_size - 1
        self.content_length = self.end_offset - self.start_offset + 1

        self.current_offset = self.start_offset
        return r.headers

    def monitor(self):
        while self.running:
            if time.time() - self.last_read >= self.timeout:
                self.running = False
                return

    def worker(self):
        while self.running:
            chunk = None
            try:
                self.lock.acquire()
                if not self.pending_chunk_queue.empty():
                    chunk = self.pending_chunk_queue.get()
                    self.ready_chunk_queue.put(chunk)
            except Exception as e:
                print(e)
            finally:
                self.lock.release()

            if chunk is None:
                self.running = False
                break

            while self.running:
                if chunk.start_offset - self.current_offset >= self.chunk_size * self.max_buffered_chunk:
                    time.sleep(1)
                    continue
                else:
                    break

            if not self.running:
                break

            current_offset = chunk.start_offset
            while self.running and current_offset <= chunk.end_offset:
                try:
                    if self.get_url_and_headers:
                        url, headers = self.get_url_and_headers()
                        headers = headers.copy()
                    else:
                        url = self.url
                        headers = self.headers.copy()

                    headers['Range'] = 'bytes={}-{}'.format(
                        current_offset, chunk.end_offset)
                    r = self.session.get(url,
                                         headers=headers,
                                         stream=True,
                                         verify=False)
                    for data in r.iter_content(self.buffer_size):
                        chunk.queue.put(data)
                        current_offset += len(data)
                    break
                except Exception as e:
                    print(e)
                    time.sleep(1)

    def read(self):
        self.last_read = time.time()
        if self.current_offset > self.end_offset:
            self.running = False
            return None

        if not self.running and self.current_offset > self.start_offset and self.current_chunk is None:
            self.running = True
            for i in range(
                    int((self.content_length - self.prefetch_size - 1) /
                        self.chunk_size) + 1):
                start_offset = self.start_offset + self.prefetch_size + i * self.chunk_size
                end_offset = start_offset + self.chunk_size - 1
                if end_offset > self.end_offset:
                    end_offset = self.end_offset
                chunk = Chunk(start_offset, end_offset)
                self.pending_chunk_queue.put(chunk)
            for _ in range(self.connection):
                threading.Thread(target=self.worker).start()
            threading.Thread(target=self.monitor).start()

        if self.current_chunk == None:
            self.current_chunk = self.ready_chunk_queue.get(True, self.timeout)

        data = self.current_chunk.read(self.timeout)
        self.current_offset += len(data)
        if self.current_chunk.eof():
            self.current_chunk = None
        return data

    def stop(self):
        self.running = False


class Chunk(object):

    def __init__(self, start_offset=-1, end_offset=-1):
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.chunk_size = end_offset - start_offset + 1
        self.read_size = 0
        self.queue = Queue()

    def read(self, timeout=10):
        data = self.queue.get(True, timeout)
        self.queue.task_done()
        self.read_size += len(data)
        return data

    def eof(self):
        return self.read_size >= self.chunk_size


if __name__ == '__main__':
    d = Downloader(
        #'http://test.coco.com/test.txt',
        'http://10.10.1.1:9988/%E8%B1%86%E7%93%A39.1%E5%88%86.%E6%97%A5%E6%BC%AB%E3%80%8A%E5%A6%84%E6%83%B3%E4%BB%A3%E7%90%86%E4%BA%BA%E3%80%8B%20%282004%29/%5BParanoia%20Agent%5D%5BVol.01%5D%5BSP02%5D%5BPromotion%20Video%5D%5BBDRIP%5D%5B1440x810%5D%5BH264%28Hi10P%29_FLAC%5D.mkv',
        #'http://10.10.1.1:9988/%E9%BE%99%E7%8F%A0/%E4%B8%83%E9%BE%99%E7%8F%A0TV%281986%29%20%5B%E8%BE%BD%E8%89%BA%E5%9B%BD%E8%AF%AD%E8%93%9D%E5%85%89%E7%89%88%5D/%E4%B8%83%E9%BE%99%E7%8F%A0%20005%20%E5%BC%BA%E5%A4%A7%E9%82%AA%E6%81%B6%E7%9A%84%E6%B2%99%E6%BC%A0.BD.%E8%BE%BD%E8%89%BA%E5%9B%BD%E8%AF%AD.%40aliang.mp4',
        #'https://bj29-enet.cn-beijing.data.alicloudccp.com/M5tKydVL%2F114819%2F622988313f5d3aae13194bc28711f9d976f047d8%2F622988319ebe1b1785474fe18d3736c0fb6a9fb5?callback=eyJjYWxsYmFja1VybCI6Imh0dHA6Ly9wZHNhcGkuYWxpeXVuZHJpdmUuY29tL3YyL2ZpbGUvZG93bmxvYWRfY2FsbGJhY2siLCJjYWxsYmFja0JvZHkiOiJodHRwSGVhZGVyLnJhbmdlPSR7aHR0cEhlYWRlci5yYW5nZX1cdTAwMjZidWNrZXQ9JHtidWNrZXR9XHUwMDI2b2JqZWN0PSR7b2JqZWN0fVx1MDAyNmRvbWFpbl9pZD0ke3g6ZG9tYWluX2lkfVx1MDAyNnVzZXJfaWQ9JHt4OnVzZXJfaWR9XHUwMDI2ZHJpdmVfaWQ9JHt4OmRyaXZlX2lkfVx1MDAyNmZpbGVfaWQ9JHt4OmZpbGVfaWR9IiwiY2FsbGJhY2tCb2R5VHlwZSI6ImFwcGxpY2F0aW9uL3gtd3d3LWZvcm0tdXJsZW5jb2RlZCIsImNhbGxiYWNrU3RhZ2UiOiJiZWZvcmUtZXhlY3V0ZSIsImNhbGxiYWNrRmFpbHVyZUFjdGlvbiI6Imlnbm9yZSJ9&callback-var=eyJ4OmRvbWFpbl9pZCI6ImJqMjkiLCJ4OnVzZXJfaWQiOiJjNWNhMGUyZDU2ZDU0YzdlYmFkZDRiMjc4YjkwOGNhYyIsIng6ZHJpdmVfaWQiOiIzMzgxMDYiLCJ4OmZpbGVfaWQiOiI2MzM2OGE3NzIzNGQzOTI1NzQ0YjQ2ZWM5YTBlN2JjM2Y4YmFkMTAyIn0%3D&di=bj29&dr=338106&f=63368a77234d3925744b46ec9a0e7bc3f8bad102&response-content-disposition=attachment%3B%20filename%2A%3DUTF-8%27%27The.Green.Planet.S01E01.1080p.BluRay.x264-KLWNH.mkv&security-token=CAIS%2BgF1q6Ft5B2yfSjIr5fEPtLzlK9t%2F6C4aBP%2Fnm4kNcUeor3ujDz2IHFPeHJrBeAYt%2FoxmW1X5vwSlq5rR4QAXlDfNRDnCimEqVHPWZHInuDox55m4cTXNAr%2BIhr%2F29CoEIedZdjBe%2FCrRknZnytou9XTfimjWFrXWv%2Fgy%2BQQDLItUxK%2FcCBNCfpPOwJms7V6D3bKMuu3OROY6Qi5TmgQ41Uh1jgjtPzkkpfFtkGF1GeXkLFF%2B97DRbG%2FdNRpMZtFVNO44fd7bKKp0lQLukMWr%2Fwq3PIdp2ma447NWQlLnzyCMvvJ9OVDFyN0aKEnH7J%2Bq%2FzxhTPrMnpkSlacGoABRYlQpz%2BCxE%2B2VhJ2n8szVkBIhG35J6tkPE4T8j9j9lIcThBq%2BCaFxdUHxDWw0evIpIQ9mrN6XldXPHv3vLo1rndrsDYq1q6VcW3yItTbdQf5MOORWsvVVbL2lfGbI%2BG%2FGpVgfSMrnmthkb9HuGox5%2FYuJd%2BaJZLTiQRfvgQSROw%3D&sl=ivhAJM1voss&u=c5ca0e2d56d54c7ebadd4b278b908cac&x-oss-access-key-id=STS.NTquhGypLHbSj5Nznq9J2MxEn&x-oss-additional-headers=referer&x-oss-expires=1665157964&x-oss-signature=zztmBwEgbKYZ2ABV15JSVEV4gYBVr6r8YGP3SG2AitM%3D&x-oss-signature-version=OSS2',
        headers={
            'Range': 'bytes=0-',
            'Referer': 'https://www.aliyundrive.com/',
        })

    headers = d.start()
    with open('/tmp/a.mkv', 'wb') as f:
        while True:
            data = d.read()
            if data is None:
                print('eof')
                break
            print(len(data), '?')
            f.write(data)
    """
    print(headers)
    while True:
        chunk = d.read()
        if chunk is None:
            print('eof')
            break
        print(len(chunk))
    """
