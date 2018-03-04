#!/usr/bin/env python3

import logging
import json
import subprocess

class LVMError(Exception):

    def __init__(self, message):
        self.__message = message

    def __str__(self):
        return self.__message

class LV:

    def __init__(self, vg_name, lv_name):
        self.__vg_name = vg_name
        self.__lv_name = lv_name
        self.__logger = logging.getLogger(str(self))

    def __str__(self):
        return "LV %s-%s" % (self.__vg_name, self.__lv_name)

    def create_snapshot(self, snapshot_size):
        lv_full_name = "%s-%s" % (self.__vg_name, self.__lv_name)
        self.__logger.info("run: lvcreate -n %i-backup-%s -L 50GB -s -c 256K /dev/mapper/%s" %
                           (lv_full_name, "date", lv_full_name))

    def snapshots(self):
        with subprocess.Popen(["lvs",
                               "--option", "lv_name",
                               "--select", "origin=%s" % (self.__lv_name),
                               "--reportformat", "json",
                               self.__vg_name],
                              stdout=subprocess.PIPE,
                              universal_newlines=True) as p:
            lvs_results = json.load(p.stdout)
            lvs_ret = p.wait()
        if lvs_ret != 0:
            raise LVMError("LVM failed with error code %i. Check that the script is run as root." % (lvs_ret))
        return lvs_results["report"][0]["lv"]
