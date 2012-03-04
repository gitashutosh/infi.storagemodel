
from infi.storagemodel.errors import DeviceDisappeared
from infi.exceptools import InfiException, chain
from infi.pyutils.lazy import cached_method
from infi.asi import AsiCheckConditionError
from infi.asi.errors import AsiOSError
import binascii
from infi.instruct import SBInt64
from logging import getLogger
logger = getLogger()

DEFAULT_PORT = 80

class JSONInquiryException(InfiException):
    pass

class DeviceIdentificationPage(object):
    def __init__(self, page):
        self._page = page

    def is_designator_vendor_specific(self, designator):
        from infi.asi.cdb.inquiry.vpd_pages.device_identification.designators import VendorSpecificDesignator
        return isinstance(designator, VendorSpecificDesignator)

    def filter_vendor_specific_designators(self):
        return filter(self.is_designator_vendor_specific, self._page.designators_list)

    @cached_method
    def get_vendor_specific_dict(self):
        result = dict()
        for designator in self.filter_vendor_specific_designators():
            key, value = [item.strip() for item in designator.vendor_specific_identifier.split('=', 1)]
            result[key] = value
        return result

    @cached_method
    def get_naa(self):
        from infi.asi.cdb.inquiry.vpd_pages.device_identification import designators
        naa = designators.NAA_IEEE_Registered_Extended_Designator
        from ...naa import InfinidatNAA
        for designator in self._page.designators_list:
            if isinstance(designator, naa):
                return InfinidatNAA(designator)

    @cached_method
    def get_target_port_group(self):
        """:returns: the target port group
        :rtype: int"""
        from infi.asi.cdb.inquiry.vpd_pages.device_identification.designators import TargetPortGroupDesignator
        for designator in self._page.designators_list:
            if isinstance(designator, TargetPortGroupDesignator):
                return designator.target_port_group

    @cached_method
    def get_relative_target_port_group(self):
        """:returns: the relative target port group
        :rtype: int"""
        from infi.asi.cdb.inquiry.vpd_pages.device_identification.designators import RelativeTargetPortDesignator
        for designator in self._page.designators_list:
            if isinstance(designator, RelativeTargetPortDesignator):
                return designator.relative_target_port_identifier


def translate_hex_repr_string(hex_repr):
    binary_string = binascii.unhexlify(hex_repr)
    return SBInt64.create_from_string(binary_string)

class InfiniBoxInquiryMixin(object):

    @cached_method
    def get_device_identification_page(self):
        raw = self.device.get_scsi_inquiry_pages()[0x83]
        return DeviceIdentificationPage(raw)

    @cached_method
    def get_management_address(self):
        """:returns: the management IPv4 address of the InfiniBox
        :rtype: string"""
        return self.get_device_identification_page().get_vendor_specific_dict()['ip']

    @cached_method
    def get_management_port(self):
        """:returns: the management IPv4 port of the InfiniBox
        :rtype: string"""
        vendor_specific_dict = self.get_device_identification_page().get_vendor_specific_dict()
        return int(vendor_specific_dict.get('port', str(DEFAULT_PORT)))

    @cached_method
    def get_host_id(self):
        """:returns: the host id within the InfiniBox
        :rtype: int"""
        vendor_specific_dict = self.get_device_identification_page().get_vendor_specific_dict()
        return translate_hex_repr_string(vendor_specific_dict['host'])

    @cached_method
    def get_naa(self):
        """:returns: the infinidat naa
        :rtype: :class:`.InfinidatNAA`"""
        return self.get_device_identification_page().get_naa()

    @cached_method
    def get_target_port_group(self):
        """:returns: the target port group
        :rtype: int"""
        return self.get_device_identification_page().get_target_port_group()

    @cached_method
    def get_relative_target_port_group(self):
        """:returns: the relative target port group
        :rtype: int"""
        return self.get_device_identification_page().get_relative_target_port_group()

    @cached_method
    def get_fc_port(self):
        """:rtype: :class:`.InfinidatFiberChannelPort`"""
        from ...fc_port import InfinidatFiberChannelPort
        return InfinidatFiberChannelPort(self.get_relative_target_port_group(),
                                         self.get_target_port_group())

    def _send_and_receive_json_inquiry_page_command(self):
        from infi.asi.coroutines.sync_adapter import sync_wait
        from ...json_page import JSONInquiryPageCommand
        try:
            with self.device.asi_context() as asi:
                inquiry_command = JSONInquiryPageCommand()
                return sync_wait(inquiry_command.execute(asi))
        except (IOError, OSError, AsiOSError), error:
            msg = "device {!r} disappeared during inquiry Infinidat C5 INQIURY"
            raise chain(DeviceDisappeared(msg.format(self.device)))

    def _get_json_inquiry_page(self):
        try:
            return self._send_and_receive_json_inquiry_page_command()
        except AsiCheckConditionError, error:
            if _is_exception_of_unsupported_inquiry_page(error):
                raise chain(JSONInquiryException("JSON Inquiry command error"))

    def _get_json_inquiry_data(self):
        return self._get_json_inquiry_page().json_serialized_data

    @cached_method
    def get_json_data(self):
        """:returns: the json inquiry data from the system
        :rtype: dict"""
        from json import loads
        raw_data = self._get_json_inquiry_data()
        try:
            logger.debug("Got JSON Inquiry data: {}".format(raw_data))
            return loads(raw_data)
        except ValueError:
            logger.debug("Inquiry response is invalid JSON format")
            raise chain(JSONInquiryException("ValueError"))

