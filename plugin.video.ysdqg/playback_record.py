import json
import xbmcvfs
import xbmcaddon
import os

_ADDON = xbmcaddon.Addon()

playback_record_path = xbmcvfs.translatePath(
    os.path.join(_ADDON.getAddonInfo('path'), 'playback_record.json'))


def PlaybackRecord(spider_class, parent_item, item):
    return {
        'spider_class': spider_class,
        'parent_item': parent_item,
        'item': item,
    }


def get_playback_records():
    if os.path.exists(playback_record_path):
        with open(playback_record_path, 'r') as f:
            return json.loads(f.read())
    return []


def add_playback_record(new_record):
    old_playback_records = get_playback_records()
    new_playback_records = []
    for old_record in old_playback_records:
        if old_record['spider_class'] == new_record[
                'spider_class'] and old_record['parent_item'][
                    'id'] == new_record['parent_item']['id']:
            continue
        new_playback_records.append(old_record)

    new_playback_records.insert(0, new_record)

    max_playback_records = _ADDON.getSettingInt('max_playback_records')
    if len(new_playback_records) > max_playback_records:
        new_playback_records = new_playback_records[:max_playback_records]

    with open(playback_record_path, 'w') as f:
        f.write(json.dumps(new_playback_records))


def delete_playback_record(record):
    old_playback_records = get_playback_records()
    new_playback_records = []
    for old_record in old_playback_records:
        if old_record['spider_class'] == record['spider_class'] and old_record[
                'parent_item']['id'] == record['parent_item']['id']:
            continue
        new_playback_records.append(old_record)

    with open(playback_record_path, 'w') as f:
        f.write(json.dumps(new_playback_records))
