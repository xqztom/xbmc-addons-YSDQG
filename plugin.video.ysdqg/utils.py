import xbmcaddon
import os

_ADDON = xbmcaddon.Addon()


def get_image_path(image_filename):
    return os.path.join(_ADDON.getAddonInfo('path'), 'resources', 'images',
                        image_filename)


def remove_html_tags(text):
    """Remove html tags from a string"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)
