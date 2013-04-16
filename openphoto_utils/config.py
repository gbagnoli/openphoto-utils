#!/usr/bin/env python
import os
from ConfigParser import ConfigParser


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

    def __init__(self, filename):
        super(Config, self).__init__()
        self.path = os.path.realpath(filename)
        self.filename = os.path.basename(self.path)
        config = ConfigParser()
        config.read(self.path)
        self.add("api", Section())
        for k in ("host", "consumer.key", "consumer.secret",
                  "oauth.token", "oauth.secret"):
            v = config.get("api", k)
            if not v:
                raise KeyError("Missing option %s in [api] section" % k)
            self.api.add(k.replace(".", "_"), v)

