#!/usr/bin/env python
from collections import Mapping
import logging
import logging.config
import os
import ConfigParser
from openphoto import Client


__all__ = ["Config"]
log = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".config",
                                   "openphoto_utils", "config.ini")


class ChainMap(Mapping):

    def __init__(self, *maps):
        self.maps = list(maps) or []

    def add(self, mapping, pos=None):
        if not pos:
            self.maps.append(mapping)
        else:
            self.maps.insert(pos, mapping)

    def __getitem__(self, item):

        for mapping in self.maps:
            try:
                return mapping[item]
            except:
                pass

        raise KeyError(item)

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(attr)

    def __len__(self):
        return len(set().union(*self.maps))

    def __iter__(self):
        return iter(set().union(*self.maps))

    def __contains__(self, item):
        return any(item in m for m in self.maps)

    def __bool__(self):
        return any(self.maps)

    def __repr__(self):
        return '{0.__class__.__name__}({1})'.format(
                    self, ', '.join(map(repr, self.maps)))


class Section(object):

    def __init__(self, name, group_parser, args_pfx=None, env_pfx=None):
        self.env_pfx = "{}_{}".format(env_pfx, name)
        self.name = name
        self.parser = group_parser
        self.args = {}
        self.envs = {}
        self.map = ChainMap()
        self.args_prefix = args_pfx if not args_pfx is None else "{}_".format(self.name)
        self.required = set()

    def from_config(self, config):
        if not config.has_section(self.name):
            return {}
        res = {}
        for opt in config.options(self.name):
            value = config.get(self.name, opt)
            if not value and opt in self.required:
                continue
            res[opt] = value
        return res

    def add_argument(self, *args, **kwargs):
        env_key = kwargs.pop("env", None)
        required = kwargs.pop("required", False)
        argument = self.parser.add_argument(*args, **kwargs)
        dest = argument.dest
        if self.args_prefix:
            if argument.dest.startswith(self.args_prefix):
                dest = argument.dest.replace(self.args_prefix, "")
        else:
            self.args_prefix = ""

        if not env_key:
            env_key = "{}_{}".format(self.env_pfx, dest).upper()

        self.args[dest] = argument.default
        try:
            self.envs[dest] = os.environ[env_key]
        except KeyError:
            pass
        argument.default = None
        if required:
            self.required.add(dest)
        return argument

    def get_map(self, configs, parsed_args):
        res = {}
        for arg in self.args:
            v = getattr(parsed_args, "{}{}".format(self.args_prefix, arg))
            if v:
                res[arg] = v
        self.map.add(res)
        self.map.add(self.envs)
        for config in configs:
            self.map.add(self.from_config(config))
        res = {}
        for k, v in self.args.items():
            if not v and k in self.required:
                continue
            res[k] = v

        self.map.add(res)
        log.debug(self)
        for arg in self.required:
            self.map[arg]

        return self.map

    def __getitem__(self, item):
        return self.map[item]

    def __getattr__(self, attr):
        return getattr(self.map, attr)

    def __repr__(self):
        return "<Section %s: %s>" % (self.name, self.map)


class Config(object):
    default_dir = os.path.dirname(DEFAULT_CONFIG_PATH)

    def __init__(self, app_name, parser, config_section=None):
        self.parser = parser
        self.sections = []
        self.configs = []
        self.parser.add_argument("config", help="Config file", nargs="?")
        self.app_name = app_name
        section_name = config_section or app_name

        self.add_section("api")
        self.api.add_argument("-H", "--api-host", help="API endpoint",
                              env="openphotoHost", required=True)
        self.api.add_argument("-K", "--api-consumer-key", help="API consumer key",
                              env="consumerKey", required=True)
        self.api.add_argument("-S", "--api-consumer-secret", help="API consumer secret",
                              env="consumerSecret", required=True)
        self.api.add_argument("-T", "--api-oauth-token",
                              help="API oauth token", env="token", required=True)
        self.api.add_argument("-X", "--api-oauth-secret", help="API oauth secret",
                              env="tokenSecret", required=True)
        self.api.add_argument("--api-debug-http", help="Set debug level on httplib")
        self.parse_config(DEFAULT_CONFIG_PATH)
        self.section = self.add_section(section_name, args_pfx="")

    def parse_config(self, filename):
        if not filename:
            return

        self.path = os.path.realpath(filename)
        try:
            logging.config.fileConfig(self.path)
        except:
            pass

        try:
            config = ConfigParser.ConfigParser()
            with open(self.path) as f:
                config.readfp(f)

            self.configs.insert(0, config)

        except:
            log.debug("Cannot parse config file %s", filename)
            return None

        else:
            return self.configs[0]

    def add_section(self, section, args_pfx=None, env_pfx=None, description=None):
        group = self.parser.add_argument_group(section, description)
        sect = Section(section, group, args_pfx, env_pfx)
        setattr(self, section, sect)
        self.sections.append(sect)
        return sect

    def add_argument(self, *args, **kwargs):
        self.section.add_argument(*args, **kwargs)

    def parse_args(self, args=None):
        parsed_args = self.parser.parse_args(args)
        self.parse_config(parsed_args.config)

        for s in self.sections:
            try:
                s.get_map(self.configs, parsed_args)

            except KeyError as e:
                self.parser.error("Missing required argument %s in %s section" % (e, s.name))

        log.debug("Creating client for %s", self.api.host)
        try:
            debug_level = int(self.api.debug_http)
        except (TypeError, ValueError) as e:
            debug_level = None

        self.client = Client(self.api.host,
                             self.api.consumer_key,
                             self.api.consumer_secret,
                             self.api.oauth_token,
                             self.api.oauth_secret,
                             http_debug_level=debug_level)
