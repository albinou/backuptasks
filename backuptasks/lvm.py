#!/usr/bin/env python3

import logging

class LV:

    def __init__(self, lv_name):
        self.lv_name = lv_name
        self.logger = logging.getLogger(str(self))

    def create_snapshot(self, snapshot_size):
        self.logger.info("run: lvcreate -n %i-backup-%s -L 50GB -s -c 256K /dev/mapper/%s" %
                         (self.lv_name, "date", self.lv_name))
