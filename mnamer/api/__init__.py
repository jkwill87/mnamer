import logging

__all__ = ["log"]

log = logging.getLogger(__name__)
log.addHandler((logging.StreamHandler()))
log.setLevel(logging.FATAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)
