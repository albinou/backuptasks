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
import math
from time import sleep
from datetime import datetime
from datetime import timedelta
from hddfancontrol import Drive
from hddfancontrol import colored_logging

import bt_errors
import tasks

actions_classes = { "snapshot": tasks.Snapshot }

def parse_period(period_str):
    m = re.fullmatch("(\d+)([wdhms])", period_str)
    if m == None:
        raise bt_errors.ConfigError("Invalid period")
    value = int(m.group(1))
    unit = m.group(2)
    if unit == 'w':
        return timedelta(weeks=value)
    elif unit == 'd':
        return timedelta(days=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    else:
        return timedelta(seconds=value)

def parse_tasks(config_file, dry_run=False):
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
            t = actions_classes[a](s, period, drives_filepaths, config_items,
                                   dry_run)
            tasks.append(t)
    return tasks

def run_tasks(tasks, run_datetime):
    for t in tasks:
        if t.run_needed(run_datetime) and not t.drives_sleeping():
            t.run(run_datetime)

def event_loop(tasks):
    gcd = int(tasks[0].get_period().total_seconds())
    for t in tasks[1:]:
        gcd = math.gcd(gcd, int(t.get_period().total_seconds()))
    gcd_period = timedelta(seconds=gcd)

    loop_start = datetime.now()
    i = 0
    while True:
        theorical_time = loop_start + i * gcd_period
        run_tasks(tasks, theorical_time)
        i += 1
        time_to_sleep = theorical_time + gcd_period - datetime.now()
        sleep(time_to_sleep.total_seconds())

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
    arg_parser.add_argument("-n",
                            "--dry-run",
                            action="store_true",
                            dest="dry_run",
                            help="Perform a trial run with no changes made")
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

    tasks = parse_tasks(args.config_file, args.dry_run)
    return event_loop(tasks)

if __name__ == "__main__":
    sys.exit(main())
