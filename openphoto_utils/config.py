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

    def __init__(self, name, group_parser, config):
        self.name = name
        self.args = []
        self.parser = group_parser
        self._config = config

    def add_argument(self, *args, **kwargs):
        argument = self.parser.add_argument(*args, **kwargs)
        try:
            default = self._config.get(
                            self.name,
                            argument.dest.replace("%s_" % (self.name), ""))
        except ConfigParser.NoSectionError:
            default = None

        if default and "default" in kwargs:
            raise TypeError("%s default has multiple values" % (argument.dest))
        argument.default = default
        self.args.append(argument.dest)
        return argument

    def __getattr__(self, attr):
        argname = "%s_%s" % (self.name, attr)
        try:
            return getattr(self.parsed_arguments, argname)

        except AttributeError:
            try:
                return getattr(self.parsed_arguments, attr)
            except AttributeError:
                raise AttributeError(attr)


class Config(Section):

    def __init__(self, section_name, parser):
        self.parser = parser
        self.args = []
        self.sections = []
        self.add_config_argument()

        self.add_section("api")
        self.api.add_argument("-H", "--api-host", help="API endpoint")
        self.api.add_argument("-k", "--api-consumer-key", help="API consumer key")
        self.api.add_argument("-s", "--api-consumer-secret", help="API consumer secret")
        self.api.add_argument("-t", "--api-oauth-token", help="API oauth token")
        self.api.add_argument("-S", "--api-oauth-secret", help="API oauth secret")

        self.add_section(section_name)

    def parse(self, filename=None):
        if not filename:
            filename = os.path.join(os.path.expanduser("~"), ".config",
                                    "openphoto-utils", "config.ini")
        self.path = os.path.realpath(filename)
        logging.config.fileConfig(self.path)
        self.filename = os.path.basename(self.path)
        config = ConfigParser.ConfigParser()
        with open(self.path) as f:
            config.readfp(f)

        self._config = config

    def add_config_argument(self):
        def parse(string):
            try:
                self.parse(string)
                return string

            except Exception as e:
                raise argparse.ArgumentTypeError(str(e))

        kw = dict(help="Config file", type=parse)
        try:
            kw["default"] = self.parse()
            kw['nargs'] = "?"

        except:
            kw['required'] = True

        self.parser.add_argument("config", **kw)

    def add_section(self, section, description=None):
        group = self.parser.add_argument_group(section, description)
        sect = Section(section, group, self._config)
        setattr(self, section, sect)
        self.sections.append(sect)
        return sect

    def add_argument(self, *args, **kwargs):
        section = kwargs.pop("section", None)
        if section:
            self.sections[section].add_argument(*args, **kwargs)
        else:
            self.parser.add_argument(*args, **kwargs)

    def parse_args(self, args=None):
        parsed_args = self.parser.parse_args(args)
        for s in self.sections:
            s.parsed_arguments = parsed_args

        log.debug("Creating client for %s", self.api.host)
        self.client = OpenPhoto(self.api.host,
                                self.api.consumer_key, self.api.consumer_secret,
                                self.api.oauth_token,self.api.oauth_secret)
