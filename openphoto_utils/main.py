import logging
from requests.exceptions import RequestException

log = logging.getLogger(__name__)


def run(fun, config,  *args, **kwargs):

    try:
        fun(config, *args, **kwargs)

    except (OSError, RequestException) as e:
        log.critical(e)

    except Exception as e:
        log.exception("Unknown error [%s]", type(e))

    except KeyboardInterrupt:
        log.info("Terminated.")

    else:
        return 0

    return 2
