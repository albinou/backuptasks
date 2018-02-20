#!/usr/bin/env python3

import logging

import lvm

class Task:

    def __init__(self, task_name, drives_filepaths):
        self.task_name = task_name
        self.logger = logging.getLogger(str(self))
        self.drives = [];
        for dp in drives_filepaths:
            self.drives.append(Drive(dp, None))

    def __str__(self):
        """ Return a pretty task name. """
        return self.task_name

    def run(self):
        for d in self.drives:
            if d.isSleeping():
                self.logger.debug("Aborting task: Device %s is sleeping." % d)
                return 1
        self.logger.info("I should perform the task now!")
        return 0

class Snapshot(Task):

    def __init__(self, task_name, drives_filepaths, config_items):
        super().__init__(task_name, drives_filepaths)
        self.lv = lvm.LV(config_items["lvm_volume_name"])
        self.lvm_snapshot_size = config_items["lvm_snapshot_size"]
        self.lvm_snapshot_freq = config_items["lvm_snapshot_freq"]
