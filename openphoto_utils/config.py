#!/usr/bin/env python
import os
from collections import Mapping
from ConfigParser import ConfigParser


class Config(Mapping):

    def __init__(self, filename):
        self.path = os.path.realpath(filename)
        self.filename = os.path.basename(self.path)
        config = ConfigParser()
        config.read(self.path)
        d = dict()
        for k in ("host", "consumer.key", "consumer.secret",
                  "oauth.token", "oauth.secret"):
            d[k] = config.get("api", k)
            if not d[k]:
                raise KeyError("Missing option %s in [api] section" % k)
        self._data = d

    def __getattr__(self, attr):
        try:
            v = self._data[attr]
        except KeyError:
            raise AttributeError(attr)
        else:
            setattr(self, attr, v)
            return v

    def __getitem__(self, item):
        return self._data[item]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return repr(self._data)
