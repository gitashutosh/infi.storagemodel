'''
Created on Jul 11, 2014
@author: aviad@infinidat.com
'''

import sys


def print_device_details(device):
    from infi.storagemodel.base.multipath import MultipathDevice
    sys.stdout.write("%-16s\t" % device.get_display_name())
    sys.stdout.write(":%-9s\t" % device.get_scsi_vendor_id())
    sys.stdout.write(":%-16s\t" % device.get_scsi_product_id())
    sys.stdout.write(":%-6s\t" % device.get_scsi_revision())
    sys.stdout.write(":%-32s\t" % device.get_scsi_serial_number())
    sys.stdout.write(":%-16s\t" % str(long(device.get_size_in_bytes()) /1024) )
    if isinstance(device, MultipathDevice):
        sys.stdout.write(":%s\t\n" % len(device.get_paths()))
    else:
        sys.stdout.write(":1\t\n")


def main():
    from infi.storagemodel import get_storage_model

    print("\nPython Inquiry utility, Version V0.1 (using storagemodel by INFINIDAT)\n")
    print("-----------------------------------------------------------------------------------------------------------------------------------------------")
    print("DEVICE          \t:VEND     \t:PROD            \t:REV   \t:SER NUM                         \t:CAP(kb)            \t:PATHS")
    print("-----------------------------------------------------------------------------------------------------------------------------------------------")

    model = get_storage_model()
    scsi = model.get_scsi()
    mpio = model.get_native_multipath()
    mpaths = mpio.get_all_multipath_block_devices()
    block_devices = scsi.get_all_scsi_block_devices()
    non_mp_disks = mpio.filter_non_multipath_scsi_block_devices(block_devices)

    all_devices = non_mp_disks + mpaths

    for device in all_devices:
        try:
            print_device_details(device)
        except:
            pass


if __name__ == '__main__':
    main()
