#!/usr/bin/env python3

import logging

import lvm

class Task:

    def __init__(self, task_name, period, drives_filepaths):
        """Initialize a task

        Arguments:
        task_name: string
        period: datetime.datetime
        drives_filepaths: array of string (i.e. ["/dev/sda", "/dev/sdb"])
        """
        self.__task_name = task_name
        self.__period = period
        self.__last_run = None
        self.__logger = logging.getLogger(str(self))
        self.__drives = [];
        for dp in drives_filepaths:
            self.__drives.append(Drive(dp, None))

    def __str__(self):
        """ Return a pretty task name. """
        return self.__task_name

    def get_period(self):
        return self.__period

    def drives_sleeping(self):
        for d in self.__drives:
            if d.isSleeping():
                self.__logger.debug("Device %s is sleeping." % d)
                return 1

    def last_run(self):
        return self.__last_run

    def run_needed(self, run_datetime):
        if self.__last_run == None:
            return True
        else:
            return (run_datetime - self.__last_run) >= self.__period

    def run(self, run_datetime):
        self.__logger.info("I should perform the task now!")
        self.__last_run = run_datetime
        return 0

class Snapshot(Task):

    def __init__(self, task_name, period, drives_filepaths, config_items):
        super().__init__(task_name, period, drives_filepaths)
        self.lv = lvm.LV(config_items["lvm_volume_name"])
        self.lvm_snapshot_size = config_items["lvm_snapshot_size"]
