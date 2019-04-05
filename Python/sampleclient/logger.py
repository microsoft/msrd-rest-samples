
import logging

logging.basicConfig(
    format='[%(asctime)s] MSRD: %(levelname)s: %(message)s',
    level=logging.WARNING,
)
log = logging.getLogger('msrd')
log.setLevel(logging.INFO)


def set_logging_debug(logger_object):
    logger_object.setLevel(logging.DEBUG)
