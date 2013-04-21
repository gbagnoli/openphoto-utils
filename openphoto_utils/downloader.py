#!/usr/bin/env python

import argparse
import logging
import os
import shutil
from .config import Config
from .main import run

log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Download photos from openphoto/trovebox")
    config = Config("downloader", parser)
    config.add_argument("-d", "--photo-directory", help="Photo directory", required=True)
    config.add_argument("-c", "--photo-cache-directory",
                        help="Search for photo in this directory before downloading")
    config.parse_args()
    if config.downloader.photo_cache_directory:
        cache = os.path.realpath(config.downloader.photo_cache_directory)
    else:
        cache = None

    return run(download_photos, config,
               os.path.realpath(config.downloader.photo_directory),
               cache)


def populate_cache(directory):
    # TODO
    return {}


def download_photos(config, destination, cache=None):

    client = config.client
    if not os.path.isdir(destination):
        raise OSError("No such directory '%s'" % (destination))

    photo_dir = os.path.join(destination, ".photos")
    if cache:
        cache = populate_cache(cache)
    else:
        cache = {}

    photos = client.photos.list()
    urls = []
    for photo in photos:
        if photo.hash in cache:
            shutil.copy(cache[photo.hash], destination)
        else:
            urls.append(photo.pathDownload)

    failed = set()
    for u in urls:

        if r.status_code != 200:
            failed.add(r)
        else:
            print(r)

    print failed



if __name__ == '__main__':
    main()
