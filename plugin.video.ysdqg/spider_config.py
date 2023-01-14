from spider_yingshi import Spideryingshi
from spider_cntv import SpiderCNTV
from spider_bilibili import Spiderbilibili
from spider_zhibo import SpiderZhiBo
from spider_dianshi import SpiderDianShiZhiBo
from spider_aliyundrive import SpiderAliyunDrive
from spider_alist import SpiderAlist

spiders = {
    Spideryingshi.__name__: Spideryingshi(),
    SpiderCNTV.__name__: SpiderCNTV(),
    Spiderbilibili.__name__: Spiderbilibili(),
    SpiderZhiBo.__name__: SpiderZhiBo(),
    SpiderDianShiZhiBo.__name__: SpiderDianShiZhiBo(),
    SpiderAliyunDrive.__name__: SpiderAliyunDrive(),
    SpiderAlist.__name__: SpiderAlist()
}
