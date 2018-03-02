#!/usr/bin/env python3

__version__ = "0.1.0"
__author__ = "Albin Kauffmann"
__license__ = "GPLv3"

""" Run configurable backup tasks """

import argparse
import logging
import configparser
import sys
import re
from datetime import timedelta
from hddfancontrol import Drive
from hddfancontrol import colored_logging

import tasks

actions_classes = { "snapshot": tasks.Snapshot }

class ConfigError(Exception):

    def __init__(self, message):
        self.__message = message

    def __str__(self):
        return self.__message

def parse_period(period_str):
    m = re.search("(\d+)d", period_str)
    if m == None:
        raise ConfigError("Invalid period")
    return timedelta(days=int(m.group(1)))

def parse_tasks(config_file):
    tasks = []
    f = open(config_file, 'r')
    config = configparser.ConfigParser()
    config.read_file(f)
    f.close()
    for s in config.sections():
        actions = config.get(s, "actions")
        for a in actions.split(","):
            a = a.strip(" []{}")
            config_items = dict(config.items(s))
            period = parse_period(config_items["period"])
            drives_filepaths = []
            t = actions_classes[a](s, period, drives_filepaths, config_items)
            tasks.append(t)
    return tasks

def tasks_loop(tasks):
    pass

def main():
    # parse args
    arg_parser = argparse.ArgumentParser(description="Configurable backup tasks v%s.%s" % (__version__, __doc__),
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-c",
                            "--config",
                            required=True,
                            dest="config_file",
                            help="Tasks configuration file")
    arg_parser.add_argument("-v",
                            "--verbosity",
                            choices=("warning", "normal", "debug"),
                            default="normal",
                            dest="verbosity",
                            help="Level of logging output")
    arg_parser.add_argument("-b",
                            "--background",
                            action="store_true",
                            dest="daemonize",
                            help="Daemonize process")
    args = arg_parser.parse_args()

    # setup logger
    logging_level = {"warning": logging.WARNING,
                     "normal": logging.INFO,
                     "debug": logging.DEBUG}
    logging.getLogger().setLevel(logging_level[args.verbosity])
    logging_fmt_long = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    logging_fmt_short = "%(levelname)s [%(name)s] %(message)s"
    if args.daemonize:
        if args.log_filepath is not None:
            # log to file
            logging_fmt = logging_fmt_long
            logging_handler = logging.handlers.WatchedFileHandler(args.log_filepath)
        else:
            # log to syslog
            logging_fmt = logging_fmt_short
            logging_handler = LoggingSysLogHandler(syslog.LOG_DAEMON)
        logging_formatter = logging.Formatter(fmt=logging_fmt)
    else:
        # log to stderr
        if sys.stderr.isatty():
            logging_formatter = colored_logging.ColoredFormatter(fmt=logging_fmt_long)
        else:
            # assume systemd service in 'simple' mode
            logging_formatter = logging.Formatter(fmt=logging_fmt_short)
        logging_handler = logging.StreamHandler()
    logging_handler.setFormatter(logging_formatter)
    logging.getLogger().addHandler(logging_handler)

    tasks = parse_tasks(args.config_file)
    return tasks_loop(tasks)

if __name__ == "__main__":
    sys.exit(main())
