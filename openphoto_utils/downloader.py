#!/usr/bin/env python

import argparse
import logging
import os
import shutil
from openphoto import (Album,
                       Photo,
                       Tag)
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
    try:
        os.mkdir(photo_dir)
    except OSError:
        pass

    if cache:
        cache = populate_cache(cache)
    else:
        cache = {}

    for photo in Photo.all(client):
        if photo.hash in cache:
            shutil.copy(cache[photo.hash], destination)
        else:
            print("Downloading photo %s" % (photo.id))
            photo_path = os.path.join(photo_dir, photo.id)
            if os.path.isfile(photo_path):
                continue
            try:
                photo.download(photo_path)
            except Exception as e:
                print ("Error downloading photo %s: %s" % (photo.id, e))

    for album in Album.all(client):
        album_dir = os.path.join(destination, album.name)
        print("Creating links for album %s" % (album.name))
        try:
            os.mkdir(album_dir)
        except OSError:
            pass

        for photo in album.photos():
            photo_path = os.path.join(photo_dir, photo.id)
            if not os.path.isfile(photo_path):
                continue
            ext = os.path.splitext(photo.filename_original)[-1].lower()
            dest = os.path.join(album_dir, "%s%s" % (photo.id, ext))
            if not os.path.exists(dest):
                os.link(photo_path, dest)

    tags_dir = os.path.join(destination, "tags")
    try:
        os.mkdir(tags_dir)
    except OSError:
        pass

    for tag in Tag.all(client):
        tag_dir = os.path.join(tags_dir, tag.id)
        print("Creating links for tag %s" % (tag.id))
        try:
            os.mkdir(tag_dir)
        except OSError:
            pass

        for photo in tag.photos():
            photo_path = os.path.join(photo_dir, photo.id)
            if not os.path.isfile(photo_path):
                continue
            ext = os.path.splitext(photo.filename_original)[-1]
            dest = os.path.join(tag_dir, "%s%s" % (photo.id, ext))
            if not os.path.exists(dest):
                os.link(photo_path, dest)


if __name__ == '__main__':
    main()
