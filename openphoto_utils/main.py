import logging
import socket
import httplib2

log = logging.getLogger(__name__)


def run(config, fun, *args, **kwargs):

    try:
        fun(*args, **kwargs)

    except (OSError,) as e:
        log.critical(e)

    except socket.error as e:
        log.critical("Cannot connect to the remote API at %s: %s", config.api.host, e)

    except httplib2.ServerNotFoundError as e:
        log.critical("Cannot resolve name for remote API at %s: %s", config.api.host, e)

    except Exception as e:
        log.exception("Unknown error [%s]", type(e))

    else:
        return 0

    return 2
