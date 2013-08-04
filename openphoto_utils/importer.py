#!/usr/bin/env python

import argparse
from requests.exceptions import HTTPError
import logging
import os
from openphoto import (Album,
                       Photo)
from openphoto.utils import hash_
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
    config.add_argument("-c", "--hashes", action="store_true",
                        help="Compare hashes before uploading", default=False)
    config.add_argument("-t", "--tag", action="append",
                        help="Add tags to photos (can be \
                        specified multiple times)")
    config.add_argument("-R", "--remove-tag", action="append",
                        help="Remove tags from photos (can be \
                        specified multiple times)")
    config.add_argument("--public", action="store_true",
                        default=False, help="Make photos public")
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
               create_albums=config.importer.create_albums,
               compare_hash=config.importer.hashes,
               tags=config.importer.tag, public=config.importer.public,
               remove_tags=config.importer.remove_tags)


def init_hashes(config):
    log.info("Getting remote hashes")
    return {p.hash: p for p in Photo.all(config.client)}


def import_photo(config, target, albums=None, hashes=None,
                 raise_errors=False, tags=None, public=False,
                 remove_tags=None):
    photo = None
    private = not public
    if hashes:
        photo = hashes.get(hash_(target))
        if photo:
            log.info("%s hash found, skipping upload, updating info", target)
            photo.update(tags=tags, tags_action="add",
                         private=private, albums=albums)
            if remove_tags:
                photo.update(tags=remove_tags, action="remove")
            return photo


    try:
        photo = Photo.create(config.client, target, albums=albums,
                             tags=tags, private=private)

    except HTTPError as e:
        if e.response.status_code == 409:
            log.debug("Photo hash already exists, skipping")
        else:
            if raise_errors:
                raise e
            else:
                log.critical("Error while uploading %s to %s",
                             target, albums)
    return photo


def import_directories(config, targets, album=None, recurse=False,
                       create_albums=False, compare_hash=False,
                       tags=None, public=False, remove_tags=None):
    if album:
        album = Album.create(config.client, name=album,
                                return_existing=True)

    tags = tags or []
    remove_tags = remove_tags or []

    hashes = None
    if compare_hash:
        hashes = init_hashes(config)

    for target in targets:
        for root, dirs, files in os.walk(target):
            if not recurse:
                del dirs[:]
            if create_albums:
                album_name = os.path.basename(root[:-1]).title()
                album = Album.create(config.client,
                                     name=album_name,
                                     return_existing=True)

                log.info("Uploading to album %s", album)

            for file_ in files:
                import_photo(config, os.path.join(root, file_), albums=album,
                             hashes=hashes, tags=tags,
                             public=public, remove_tags=remove_tags)


def import_files(config, targets, album=None, recurse=False,
                 create_albums=False, compare_hash=False,
                 tags=None, public=False,
                 remove_tags=None):
    if recurse:
        log.warn("recurse ignored with files")
    if create_albums:
        log.warn("create_albums ignored with files")

    hashes = None
    if compare_hash:
        hashes = init_hashes(config)

    if album:
        album = Album.create(config.client, album, True)
        log.info("Uploading to album %s", album)

    tags = tags or []
    remove_tags = remove_tags or []

    for file_ in targets:
        file_ = os.path.realpath(file_)
        import_photo(config, file_, albums=album,
                     hashes=hashes, tags=tags,
                     public=public, remove_tags=remove_tags)


