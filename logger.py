#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# logger.py
#
# usage:
#
#   @logger('/var/log/foo.log')
#   def your_func():
#     logging.info('hello world')
#     logging.info('bye')
#     pass
#
# stdout
#   09-07 09:46 root   INFO   [your_func] hello world
#   09-07 09:46 root   INFO   [your_func] bye
#
# /var/log/foo.log (If no file exists, it creates automatically.)
#   09-07 09:46 root   INFO   [your_func] hello world
#   09-07 09:46 root   INFO   [your_func] bye
#

import logging
from general.config import Config


def logger(log_file_path=None, level=Config.LOG_LEVEL):
    def decorator(f):
        def wrapper(*args, **kwargs):
            # write log as batch.log and stdout
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)
            if log_file_path:
                logging.basicConfig(
                    handlers=[logging.FileHandler(log_file_path, 'a', 'utf-8')],
                    level=level,
                    format='%(asctime)s %(name)-6s %(levelname)-6s [{}] %(message)s'.
                           format(f.__name__),
                    datefmt='%m-%d %H:%M')
            else:
                logging.basicConfig(
                    handlers=[],
                    level=level,
                    format='%(asctime)s %(name)-6s %(levelname)-6s [{}] %(message)s'.
                           format(f.__name__),
                    datefmt='%m-%d %H:%M')
            return f(*args, **kwargs)
        return wrapper
    return decorator
