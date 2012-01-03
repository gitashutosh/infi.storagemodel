
from infi.pyutils.lazy import cached_method, cached_property, clear_cache, LazyImmutableDict
from ..base import StorageModel, scsi, multipath, disk, mount, partition, filesystem
from contextlib import contextmanager

# pylint: disable=W0212,E1002

from infi.diskmanagement import Disk

class WindowsDiskDrive(disk.DiskDrive):
    def __init__(self, storage_device):
        super(WindowsDiskDrive, self).__init__()
        self._storage_device = storage_device
        self._disk_object = Disk(self._storage_device.get_physical_drive_number())

    @cached_method
    def get_storage_device(self):
        disk.DiskDrive.get_storage_device(self)

    @cached_method
    def get_block_access_path(self):
        self._disk_object._path

    def is_empty(self):
        return len(self._disk_object.get_partitions()) == 0

    def get_partition_table(self):
        from .partition import WindowsMBRPartitionTable, WindowsGPTPartitionTable
        if self._disk_object.is_gpt():
            return WindowsGPTPartitionTable(self)
        return WindowsMBRPartitionTable(self)

    def delete_partition_table(self):
        self._disk_object.destroy_partition_table()

    def create_mbr_partition_table(self):
        from .partition import WindowsMBRPartitionTable
        return WindowsMBRPartitionTable.create_partition_table(self)

    def create_gpt_partition_table(self):
        from .partition import WindowsGPTPartitionTable
        return WindowsGPTPartitionTable.create_partition_table(self)

class WindowsDiskModel(disk.DiskModel):
    def find_disk_drive_by_block_access_path(self, path):
        from infi.storagemodel import get_storage_model
        scsi = get_storage_model().get_scsi()
        multipath = get_storage_model().get_native_multipath()
        storage_device = filter(lambda device: device.get_block_access_path() == path,
                                scsi.get_all_scsi_block_devices() + multipath.get_all_multipath_devices())[0]
        return WindowsDiskDrive(storage_device, path)

# TODO
# mount manager
# mount repository