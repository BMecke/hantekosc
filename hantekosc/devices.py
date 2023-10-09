import hantekosc.py_ht6022.LibUsbScope


def list_connected_hantek_devices():
    """
    List all connected oscilloscopes from hantek.

    Returns:
        list(dict): A list containing a dict containing 'Manufacturer', 'Model' and 'Serial Number' for each device
    """
    scope = hantekosc.PyHT6022.LibUsbScope.Oscilloscope()
    usb_device_list = scope.context.getDeviceList(skip_on_error=True)
    device_list = []

    for device in usb_device_list:
        # Hantek 6022BE
        if (device.getVendorID() == scope.FIRMWARE_PRESENT_VENDOR_ID or device.getVendorID() ==
                scope.NO_FIRMWARE_VENDOR_ID) and device.getProductID() == scope.PRODUCT_ID_BE:
            hantek_6022be = hantekosc.PyHT6022.LibUsbScope.Oscilloscope(device.getVendorID(), device.getProductID())
            hantek_6022be.setup()
            if not  hantek_6022be.open_handle():
                sys.exit(-1)

            if (not  hantek_6022be.is_device_firmware_present):
                print('upload firmware...')
                hantek_6022be.flash_firmware()
            resource_info = {'Manufacturer': 'Hantek', 'Model': '6022BE',
                             'Serial Number': hantek_6022be.get_serial_number_string()}
            device_list.append(resource_info)
            device.close()
        # Hantek 6022BL
        if (device.getVendorID() == scope.FIRMWARE_PRESENT_VENDOR_ID or device.getVendorID() ==
                scope.NO_FIRMWARE_VENDOR_ID) and device.getProductID() == scope.PRODUCT_ID_BL:
            hantek_6022be = hantekosc.PyHT6022.LibUsbScope.Oscilloscope(device.getVendorID(), device.getProductID())
            hantek_6022be.setup()
            if not hantek_6022be.open_handle():
                sys.exit(-1)

            if (not hantek_6022be.is_device_firmware_present):
                print('upload firmware...')
                hantek_6022be.flash_firmware()
            resource_info = {'Manufacturer': 'Hantek', 'Model': '6022BL',
                             'Serial Number': hantek_6022be.get_serial_number_string()}
            device_list.append(resource_info)
            device.close()
        # Hantek 6021
        if (device.getVendorID() == scope.FIRMWARE_PRESENT_VENDOR_ID or device.getVendorID() ==
                scope.NO_FIRMWARE_VENDOR_ID) and device.getProductID() == scope.PRODUCT_ID_21:
            hantek_6022be = hantekosc.PyHT6022.LibUsbScope.Oscilloscope(device.getVendorID(), device.getProductID())
            hantek_6022be.setup()
            if not hantek_6022be.open_handle():
                sys.exit(-1)

            if (not hantek_6022be.is_device_firmware_present):
                print('upload firmware...')
                hantek_6022be.flash_firmware()
            resource_info = {'Manufacturer': 'Hantek', 'Model': '6021',
                             'Serial Number': hantek_6022be.get_serial_number_string()}
            device_list.append(resource_info)
            device.close()
    return device_list
