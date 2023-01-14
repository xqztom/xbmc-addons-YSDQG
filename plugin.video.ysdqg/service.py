from proxy_server import start_proxy_server
from player import skip_opening_and_ending, async_load_danmaku
import xbmc

if __name__ == "__main__":
    start_proxy_server()
    skip_opening_and_ending()
    async_load_danmaku()

    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        if monitor.waitForAbort(3):
            break
