import logging
import json
import subprocess

class LVMError(Exception):

    def __init__(self, message):
        self.__message = message

    def __str__(self):
        return self.__message

class LV:

    __run_cmd_err_txt = ("%s failed with error code %i. Check that the script "
                         "is run as root.")

    def __init__(self, vg_name, lv_name, dry_run=False):
        self.__vg_name = vg_name
        self.__lv_name = lv_name
        self.__dry_run = dry_run
        self.__logger = logging.getLogger(str(self))

    def __str__(self):
        return "LV %s-%s" % (self.__vg_name, self.__lv_name)

    def get_vg_name(self):
        return self.__vg_name

    def get_lv_name(self):
        return self.__lv_name

    def __run_cmd(self, lvcmd):
        self.__logger.info("run: %s" % (" ".join(lvcmd)))
        with subprocess.Popen(lvcmd) as p:
            lvm_ret = p.wait()
        if lvm_ret != 0:
            raise LVMError(self.__run_cmd_err_txt % (lvcmd[0], lvm_ret))

    def create_snapshot(self, snapshot_lv_name, snapshot_size, chunksize=None):
        lvcmd = ["lvcreate",
                 "--name", snapshot_lv_name,
                 "--size", snapshot_size,
                 "--snapshot",
                 "%s/%s" % (self.__vg_name, self.__lv_name)]
        if chunksize:
            lvcmd.insert(-1, "--chunksize")
            lvcmd.insert(-1, chunksize)
        if self.__dry_run:
            lvcmd.insert(-1, "--test")
        self.__run_cmd(lvcmd)

    def remove_snapshot(self, snapshot_lv_name):
        lvcmd = ["lvremove",
                 "--select", "lv_name=%s,origin=%s" % (snapshot_lv_name, self.__lv_name),
                 "--yes",
                 self.__vg_name]
        if self.__dry_run:
            lvcmd.insert(-1, "--test")
        self.__run_cmd(lvcmd)

    def snapshots(self):
        lvcmd = ["lvs",
                 "--option", "lv_name",
                 "--select", "origin=%s" % (self.__lv_name),
                 "--reportformat", "json",
                 self.__vg_name]
        with subprocess.Popen(lvcmd,
                              stdout=subprocess.PIPE,
                              universal_newlines=True) as p:
            lvs_results = json.load(p.stdout)
            lvs_ret = p.wait()
        if lvs_ret != 0:
            raise LVMError(self.__run_cmd_err_txt % ("lvs", lvs_ret))
        return lvs_results["report"][0]["lv"]
