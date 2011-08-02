import unittest
import mock

from ..base import StorageModel, scsi, multipath
from .. import connectivity
from ..dtypes import HCTL

class MultipathModelImpl(multipath.MultipathFrameworkModel):
    def __init__(self, *args, **kwargs):
        multipath.MultipathFrameworkModel.__init__(self, *args, **kwargs)
        self._devices = []

    def get_all_multipath_devices(self):
        return self._devices

    def filter_non_multipath_scsi_block_devices(self, scsi_devices):
        return scsi_devices

class SCSIMockImpl(scsi.SCSIModel):
    def __init__(self, *args, **kwargs):
        scsi.SCSIModel.__init__(self, *args, **kwargs)
        self._devices = []

    def get_all_scsi_block_devices(self):
        return self._devices

MultipathModel = MultipathModelImpl()
SCSIModel = SCSIMockImpl()

class MockModel(StorageModel):
    def initiate_rescan(self):
        pass

    def _create_native_multipath_model(self):
        return MultipathModel

    def _create_scsi_model(self):
        return SCSIModel

class Disk(object):
    def __init__(self, scsi_serial_number):
        self.scsi_serial_number = scsi_serial_number
        self.called = False
        self.connectivity = False
        self.get_hctl = None

    @property
    def test(self):
        if not self.called:
            self.called = True

class FCConectivityMock(connectivity.FCConnectivity):
    def __init__(self, i_wwn, t_wwn):
        from infi.hbaapi import Port
        i_port = Port()
        t_port = Port()
        i_port.port_wwn = i_wwn
        t_port.port_wwn = t_wwn
        super(FCConectivityMock, self).__init__(None, i_port, t_port)

class PredicateTestCase(unittest.TestCase):
    def true(self):
        return True

    def false(self):
        return False

    def test_getmemmbers(self):
        from inspect import getmembers
        disk = Disk('1')
        self.assertFalse(disk.called)
        _ = getmembers(disk)
        self.assertTrue(disk.called)

    def test_rescan_with_mock_predicate__returns_true(self):
        model = MockModel()
        model.rescan_and_wait_for(self.true)

    def test_rescan_with_mock_predicate__raises_timeout(self):
        from ..base import TimeoutError
        model = MockModel()
        self.assertRaises(TimeoutError, model.rescan_and_wait_for, *(self.false, 1))

    def test__predicate_list(self):
        from . import PredicateList
        self.assertTrue(PredicateList([self.true, self.true])())
        self.assertFalse(PredicateList([self.true, self.false])())
        self.assertFalse(PredicateList([self.false, self.true])())
        self.assertFalse(PredicateList([self.false, self.false])())

    @mock.patch("infi.storagemodel.get_storage_model")
    def test__disk_appeared(self, get_storage_model):
        from . import DiskExists
        get_storage_model.return_value = MockModel()
        self.assertFalse(DiskExists("12345678")())
        SCSIModel._devices = [Disk("12345678")]
        self.assertTrue(DiskExists("12345678")())
        SCSIModel._devices = []
        MultipathModel._devices = [Disk("12345678")]
        self.assertTrue(DiskExists("12345678")())
        MultipathModel._devices = []

    @mock.patch("infi.storagemodel.get_storage_model")
    def test__disk_gone(self, get_storage_model):
        from . import DiskNotExists
        get_storage_model.return_value = MockModel()
        self.assertTrue(DiskNotExists("12345678")())
        SCSIModel._devices = [Disk("12345678")]
        self.assertFalse(DiskNotExists("12345678")())
        SCSIModel._devices = []
        MultipathModel._devices = [Disk("12345678")]
        self.assertFalse(DiskNotExists("12345678")())
        MultipathModel._devices = []
        raise unittest.SkipTest

    @mock.patch("infi.storagemodel.get_storage_model")
    def test__fc_mapping_appeared(self, get_storage_model):
        from . import LunExists
        i_wwn = ":".join(["01"] * 8)
        t_wwn = ":".join(["02"] * 8)
        get_storage_model.return_value = MockModel()
        self.assertFalse(LunExists.by_fc(i_wwn, t_wwn, 1)())
        SCSIModel._devices = [Disk("1")]
        SCSIModel._devices[0].connectivity = FCConectivityMock(i_wwn, t_wwn)
        SCSIModel._devices[0].get_hctl = HCTL(*(1, 0, 0, 1))
        self.assertTrue(LunExists.by_fc(i_wwn, t_wwn, 1)())
        SCSIModel._devices = []

    @mock.patch("infi.storagemodel.get_storage_model")
    def test_fc_mapping_gone(self, get_storage_model):
        from . import LunNotExists
        i_wwn = ":".join(["01"] * 8)
        t_wwn = ":".join(["02"] * 8)
        get_storage_model.return_value = MockModel()
        SCSIModel._devices = [Disk("1")]
        SCSIModel._devices[0].connectivity = FCConectivityMock(i_wwn, t_wwn)
        SCSIModel._devices[0].get_hctl = HCTL(*(1, 0, 0, 1))
        self.assertFalse(LunNotExists.by_fc(i_wwn, t_wwn, 1)())
        SCSIModel._devices = []
        self.assertTrue(LunNotExists.by_fc(i_wwn, t_wwn, 1)())
