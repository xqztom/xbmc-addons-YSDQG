import json
import xbmcvfs
import xbmcaddon
import os

_ADDON = xbmcaddon.Addon()

favorite_record_path = xbmcvfs.translatePath(
    os.path.join(_ADDON.getAddonInfo('path'), 'favorite_record.json'))


def FavoriteRecord(spider_class, item):
    return {
        'spider_class': spider_class,
        'item': item,
    }


def get_favorite_records():
    if os.path.exists(favorite_record_path):
        with open(favorite_record_path, 'r') as f:
            return json.loads(f.read())
    return []


def add_favorite_record(new_record):
    old_favorite_records = get_favorite_records()
    new_favorite_records = []
    for old_record in old_favorite_records:
        if old_record['spider_class'] == new_record[
                'spider_class'] and old_record['item']['id'] == new_record[
                    'item']['id']:
            continue
        new_favorite_records.append(old_record)

    new_favorite_records.insert(0, new_record)

    with open(favorite_record_path, 'w') as f:
        f.write(json.dumps(new_favorite_records))


def delete_favorite_record(record):
    old_favorite_records = get_favorite_records()
    new_favorite_records = []
    for old_record in old_favorite_records:
        if old_record['spider_class'] == record['spider_class'] and old_record[
                'item']['id'] == record['item']['id']:
            continue
        new_favorite_records.append(old_record)

    with open(favorite_record_path, 'w') as f:
        f.write(json.dumps(new_favorite_records))
