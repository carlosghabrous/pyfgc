import logging

logger = None

def get_pyfgc_logger(name, severity=logging.WARNING):

    global logger
    logger = logging.getLogger("pyfgc." + name)
    logger.setLevel(severity)

    LOG_FORMAT = "[%(asctime)s] - [%(levelname)8s](%(module)10s): %(message)s"
    formatter = logging.Formatter(LOG_FORMAT)
    nh = logging.NullHandler()
    nh.setLevel(severity)
    nh.setFormatter(formatter)

    logger.addHandler(nh)
    return logger


