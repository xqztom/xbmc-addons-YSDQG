from threading import Thread
from danmaku import get_danmaku_url_cache, set_danmaku_content_cache, get_danmaku_cache_url
import xbmc
import xbmcaddon
import requests

_ADDON = xbmcaddon.Addon()


def skip_opening_and_ending():

    def _skip_opening_and_ending():
        player = xbmc.Player()
        monitor = xbmc.Monitor()

        while not monitor.abortRequested():
            try:
                last_is_playing_video = False
                skip_opening_and_ending_switch = False
                skip_opening_seconds = 0
                skip_ending_seconds = 0

                while not monitor.abortRequested():
                    total_time = 0
                    try:
                        total_time = player.getTotalTime()
                    except:
                        pass
                    is_playing_video = player.isPlayingVideo(
                    ) and total_time > 0
                    if is_playing_video:
                        current_time = player.getTime()
                        if not last_is_playing_video:
                            skip_opening_and_ending_switch = _ADDON.getSettingBool(
                                'skip_opening_and_ending_switch')
                            skip_opening_seconds = _ADDON.getSettingInt(
                                'skip_opening_seconds')
                            skip_ending_seconds = _ADDON.getSettingInt(
                                'skip_ending_seconds')
                            if skip_opening_and_ending_switch and current_time < skip_opening_seconds:
                                player.seekTime(skip_opening_seconds)
                        else:
                            if skip_ending_seconds > 0 and total_time - current_time <= skip_ending_seconds:
                                player.stop()

                    last_is_playing_video = is_playing_video
                    xbmc.sleep(3000)
            except Exception as e:
                print(e)
                pass
            xbmc.sleep(3000)

    thread = Thread(target=_skip_opening_and_ending)
    thread.daemon = True
    thread.start()


def async_load_danmaku():

    def _async_load_danmaku():
        player = xbmc.Player()
        monitor = xbmc.Monitor()

        while not monitor.abortRequested():
            try:
                danmaku_state = 'pending'
                danmaku_cache = None

                while not monitor.abortRequested():
                    is_playing_video = player.isPlayingVideo()
                    if is_playing_video:
                        if danmaku_state == 'pending':
                            danmaku_url = get_danmaku_url_cache()
                            if danmaku_url:
                                danmaku_cache = {'content': ''}

                                def load_danmaku(url, danmaku_cache):
                                    r = requests.get(url)
                                    danmaku_cache['content'] = r.text

                                thread = Thread(target=load_danmaku,
                                                args=(danmaku_url,
                                                      danmaku_cache))
                                thread.daemon = True
                                thread.start()
                                danmaku_state = 'loading'
                            else:
                                danmaku_state = 'empty'
                        elif danmaku_state == 'loading':
                            if danmaku_cache and danmaku_cache['content']:
                                set_danmaku_content_cache(
                                    danmaku_cache['content'])
                                player.setSubtitles(get_danmaku_cache_url())
                                danmaku_state = 'loaded'
                    else:
                        danmaku_state = 'pending'

                    xbmc.sleep(3000)
            except Exception as e:
                print(e)
                pass
            xbmc.sleep(3000)

    thread = Thread(target=_async_load_danmaku())
    thread.daemon = True
    thread.start()
