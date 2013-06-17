#!/usr/bin/env python

import argparse
import logging
import os
from openphoto import (Album,
                       Photo)
from .config import Config
from .main import run

log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
                description="Import photos to openphoto/trovebox")
    config = Config("importer", parser)
    config.add_argument("target", help="Directory or file to upload",
                        required=True, nargs="+")
    config.add_argument("-a", "--album", help="Create album(s)")
    config.add_argument("-r", "--recurse", help="Recurse into subdirectories",
                        action="store_true", default=False)
    config.add_argument("-C", "--create-albums", action="store_true",
                        help="Create albums from directories", default=False)
    config.parse_args()

    if config.importer.album and config.importer.create_albums:
        parser.error("Conflicting options --album and --create-albums")

    if not all(os.path.isdir(t) for t in config.importer.target) and \
       not all(os.path.isfile(t) for t in config.importer.target):
        parser.error("Cannot mix files and directories")

    if os.path.isdir(config.importer.target[0]):
        func = import_directories
        if len(config.importer.target) > 1:
            if config.importer.album:
                parser.error("Cannot set --album with multiple target dirs")
        if config.importer.recurse and not config.importer.create_albums:
            log.warn("--recurse enables --create-albums")

    else:
        func = import_files

    return run(func, config, config.importer.target,
               album=config.importer.album,
               recurse=config.importer.recurse,
               create_albums=config.importer.create_albums)


def import_photo(config, target, album):
    photo = Photo.create(config.client, target)
    if album:
        album.add(photo)


def import_directories(config, targets, album=None, recurse=False,
                       create_albums=False):
    for target in targets:
        for root, dirs, files in target:
            if not recurse:
                del dirs[:]
            if create_albums:
                album = Album.create(config.client,
                                      name=os.path.basename(root).title())
            elif album:
                album = Album.get(config.client, album)

            for file_ in files:
                import_photo(config, os.path.join(root, file_), album=album)

def import_files(config, targets, album=None, recurse=False,
                 create_albums=False):
    if recurse:
        log.warn("recurse ignored with files")
    if create_albums:
        log.warn("create_albums ignored with files")

    if album:
        album = Album.get(config.client, album)

    for file_ in targets:
        file_ = os.path.realpath(file_)
        import_photo(config, file_, album=album)


