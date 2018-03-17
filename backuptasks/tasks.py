import logging
import re

import bt_errors
import lvm

class Task:

    def __init__(self, task_name, period, drives_filepaths):
        """Initialize a task

        Arguments:
        task_name: string
        period: datetime.datetime
        drives_filepaths: list of strings (i.e. ["/dev/sda", "/dev/sdb"])
        """
        self.__task_name = task_name
        self.__period = period
        self.__last_run = None
        self._logger = logging.getLogger(str(self))
        self.__drives = [];
        for dp in drives_filepaths:
            self.__drives.append(Drive(dp, None))

    def __str__(self):
        """ Return a pretty task name. """
        return "Task/" + self.__task_name

    def get_period(self):
        return self.__period

    def drives_sleeping(self):
        for d in self.__drives:
            if d.isSleeping():
                self._logger.debug("Device %s is sleeping." % d)
                return 1

    def last_run(self):
        return self.__last_run

    def run_needed(self, run_datetime):
        if self.__last_run == None:
            return True
        else:
            return (run_datetime - self.__last_run) >= self.__period

    def run(self, run_datetime):
        self._logger.debug("Running task now")
        self.__last_run = run_datetime
        return 0

class Snapshot(Task):

    def __init__(self, task_name, period, drives_filepaths, config_items,
                 dry_run=False):
        super().__init__(task_name, period, drives_filepaths)
        self.__lv = lvm.LV(config_items["lvm_vg_name"],
                           config_items["lvm_lv_name"],
                           dry_run)
        self.__lvm_snapshot_size = config_items["lvm_snapshot_size"]
        if "lvm_snapshot_chunksize" in config_items:
            self.__lvm_snapshot_chunksize = config_items["lvm_snapshot_chunksize"]
        else:
            self.__lvm_snapshot_chunksize = None
        self.__lvm_snapshot_nb = int(config_items["lvm_snapshot_nb"])
        if self.__lvm_snapshot_nb < 1:
            raise bt_errors.ConfigError("Configuration option lvm_snapshot_nb shall be > 1")

    def bt_snapshots(self):
        snapshots = self.__lv.snapshots()
        res = []
        bt_re = re.compile("%s-bt-(\d+)" % self.__lv.get_lv_name())
        for s in snapshots:
            bt_match = bt_re.fullmatch(s["lv_name"])
            if bt_match:
                s["bt_date"] = int(bt_match.group(1))
                res.append(s)
        return res

    def run(self, run_datetime):
        super().run(run_datetime)
        bt_snapshots = self.bt_snapshots()
        lv_snapshot_name = "%s-bt-%s" % (self.__lv.get_lv_name(),
                                         run_datetime.strftime("%Y%m%d"))
        if lv_snapshot_name in [s["lv_name"] for s in bt_snapshots]:
            self._logger.warning("Snapshot %s already exists" %
                                 (lv_snapshot_name))
            return -1
        if len(bt_snapshots) >= self.__lvm_snapshot_nb:
            bt_oldest_snapshot = bt_snapshots[0]
            for s in bt_snapshots[1:]:
                if s["bt_date"] < bt_oldest_snapshot["bt_date"]:
                    bt_oldest_snapshot = s
            self.__lv.remove_snapshot(bt_oldest_snapshot["lv_name"])
        self.__lv.create_snapshot(lv_snapshot_name,
                                  self.__lvm_snapshot_size,
                                  self.__lvm_snapshot_chunksize)
        return 0
