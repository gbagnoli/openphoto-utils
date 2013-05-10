#!/usr/bin/env python

import argparse
import logging
import sys
from openphoto import (Album,
                       Photo,
                       Tag)
from .config import Config

log = logging.getLogger(__name__)
SHELLS = ("ipython", "bpython", "default", "auto")


class ShellNotFound(Exception):
    pass


def main():
    parser = argparse.ArgumentParser(
        description="Drop a shell with a configured client"
    )
    config = Config("shell", parser)
    config.add_argument("--shell", help="Shell to use (defaults to auto)",
                        choices=SHELLS, default="auto")

    config.parse_args()
    return select_shell(config, config.shell.shell)


def get_env(config):
    env = dict(
        client = config.client,
        config = config
    )
    return env


def run_ipython(env):
    try:
        from IPython.frontend.terminal.embed import (
            InteractiveShellEmbed)

    except ImportError:
        raise ShellNotFound("ipython")

    return InteractiveShellEmbed(banner2=""+ '\n', user_ns=env)()


def run_bpython(env):
    try:
        from bpython import embed

    except ImportError:
        raise ShellNotFound("bpython")

    return embed(locals_=env, banner="" + '\n')


def run_default(env):
    from code import interact
    cprt = 'Type "help" for more information.'
    banner = "Python %s on %s\n%s" % (sys.version, sys.platform, cprt)
    banner += '\n\n' + "" + '\n'
    return interact(banner, local=env)


def run_shell(config, shell):
    env = get_env(config)
    if shell == "ipython":
        return run_ipython(env)
    elif shell == "bpython":
        return run_bpython(env)
    else:
        return run_default(env)


def select_shell(config, shell):
    if shell == "auto":
        for shell in SHELLS[:-1]:  # skip auto :)
            try:
                return run_shell(config, shell)

            except ShellNotFound:
                pass
    else:
        return run_shell(config, shell)
