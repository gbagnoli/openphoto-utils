#!/usr/bin/env python
import os
import argparse
import logging
import logging.config
from openphoto import OpenPhoto
import ConfigParser


__all__ = ["Config"]
log = logging.getLogger(__name__)


class Section(object):

    def __init__(self):
        self.keys = []

    def add(self, item, value):
        object.__setattr__(self, item, value)
        self.keys.append(item)

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(item)

    def __iter__(self):
        return iter(self.keys)


class Config(Section):

    def __init__(self, filename=None):
        super(Config, self).__init__()
        if not filename:
            filename = os.path.join(os.path.expanduser("~"), ".config",
                                    "openphoto-utils", "config.ini")
        self.path = os.path.realpath(filename)
        logging.config.fileConfig(self.path)
        self.filename = os.path.basename(self.path)
        config = ConfigParser.ConfigParser()
        config.read(self.path)
        self.add("api", Section())
        for k in ("host", "consumer_key", "consumer_secret",
                  "oauth_token", "oauth_secret"):
            try:
                v = config.get("api", k)
            except ConfigParser.NoSectionError:
                raise IOError("Cannot parse %s" % (self.path))

            if not v:
                raise KeyError("Missing option %s in [api] section" % (k))

            self.api.add(k.replace(".", "_"), v)

    @property
    def client(self):
        if hasattr(self, "_client"):
            return self._client
        else:
            log.debug("Creating client for %s", self.api.host)
            self._client = OpenPhoto(self.api.host,
                                     self.api.consumer_key, self.api.consumer_secret,
                                     self.api.oauth_token,self.api.oauth_secret)
            return self._client

    @classmethod
    def add_argument_to(cls, parser, as_option=False):
        def convert_config(string):
            try:
                return cls(string)
            except Exception as e:
                raise argparse.ArgumentTypeError(str(e))

        kw = dict(help="Config file", type=convert_config)
        try:
            kw["default"] = Config()
            if not as_option:
                kw['nargs'] = "?"
        except:
            if as_option:
                kw['required'] = True

        if not as_option:
            parser.add_argument("config", **kw)
        else:
            parser.add_argument("--config", "-c", **kw)
