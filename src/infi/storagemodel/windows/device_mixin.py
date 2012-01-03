
from infi.pyutils.lazy import cached_method
from contextlib import contextmanager

# pylint: disable=W0212,E1002

class WindowsDeviceMixin(object):
    @cached_method
    def get_pdo(self):
        return self._device_object.psuedo_device_object

    @contextmanager
    def asi_context(self):
        from infi.asi.win32 import OSFile
        from infi.asi import create_platform_command_executer
        handle = OSFile(self.get_pdo())
        executer = create_platform_command_executer(handle)
        try:
            yield executer
        finally:
            handle.close()

    @cached_method
    def get_ioctl_interface(self):
        from infi.devicemanager.ioctl import DeviceIoControl
        return DeviceIoControl(self.get_pdo())

    @cached_method
    def get_instance_id(self):
        return self._device_object._instance_id

    @cached_method
    def get_hctl(self):
        from infi.dtypes.hctl import HCTL
        return HCTL(*self.get_ioctl_interface().scsi_get_address())

    @cached_method
    def get_parent(self):
        return self._device_object.parent

class WindowsDiskDeviceMixin(object):
    @cached_method
    def get_size_in_bytes(self):
        return self.get_ioctl_interface().disk_get_drive_geometry_ex()

    @cached_method
    def get_physical_drive_number(self):
        """returns the drive number of the disk.
        if the disk is hidden (i.e. part of MPIODisk), it returns -1
        """
        number = self.get_ioctl_interface().storage_get_device_number()
        return -1 if number == 0xffffffff else number

    @cached_method
    def get_display_name(self):
        return "PHYSICALDRIVE%s" % self.get_physical_drive_number()