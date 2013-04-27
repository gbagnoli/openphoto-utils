import logging

log = logging.getLogger(__name__)


def run(fun, config,  *args, **kwargs):

    try:
        fun(config, *args, **kwargs)

    except (OSError,) as e:
        log.critical(e)

    except Exception as e:
        log.exception("Unknown error [%s]", type(e))

    else:
        return 0

    return 2
