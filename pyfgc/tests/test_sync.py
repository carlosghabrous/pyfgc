# import struct
# import threading

# import pytest
# import pyfgc_name
# import pyfgc

# gateway_1 = "CFC-866-RETH1"
# gateway_2 = "CFC-866-RETH2"
# device_1 = "RFNA.866.06.ETH1"
# device_2 = "RFNA.866.01.ETH2"

# pyfgc_name.read_name_file()


# def test_sync_get_single():
#     """
#     Gets property from device.

#     """
#     prop = "DEVICE.NAME"

#     r = pyfgc.get(device_1, prop)
#     try:
#         assert r.value == device_1

#     except pyfgc.FgcResponseError:
#         # Just in case the device was not operational
#         print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")


# def test_sync_get_single_option():
#     """
#     Gets a property from a single device, specifying an option.
    
#     """

#     prop = "LIMITS.I.EARTH"

#     r = pyfgc.get(device_1, prop, get_option="HEX")
#     try:
#         int(r.value, 16)

#     except ValueError:
#         print(f"Property {prop} from device {device_1} is not a valid hex value: {r.value}!")
#         assert False

#     except pyfgc.FgcResponseError:
#         print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")


# def test_sync_get_single_binary():
#     """
#     Gets a property in binary format.
#     """
#     r = pyfgc.get(device_1, "LOG.PM.SPY.IEARTH", get_option="bin")
#     try:
#         length_header_decoded = struct.unpack("!L", r.value[0:4])[0]
#         actual_length = len(r.value[4:])
#         assert len(length_header_decoded) == actual_length
    
#     except pyfgc.FgcResponseError:
#         print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")

# def test_sync_get_single_parent():
#     """
#     Gets a parent property from a single device.
#     """

#     prop = "BARCODE"
#     r = pyfgc.get(device_1, prop)
#     try:
#         assert isinstance(r.value, str)

#     except pyfgc.FgcResponseError:
#         print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")

# def test_sync_set_single():
#     """
#     Sends a set command to a single device.
    
#     Runs a get command to verify that the set command took place.        
#     """
    
#     prop = "LIMITS.I.EARTH"
#     value = 1e-2

#     with pyfgc.fgc(device_1) as fgc:
#         r = fgc.set(prop, value)

#         r = fgc.get(prop)

#         try:
#             assert pytest.approx(float(r.value)) == value
#         except pyfgc.FgcResponseError:
#             print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")

# def test_two_threads():
#     def get_device_name(device_name, results):
#         r = pyfgc.get(device_name, "DEVICE.NAME")
#         results[device_name] = r.value

#     thread_list = list()
#     results     = dict()
    
#     devices_names = pyfgc_name.build_device_set(".*866.*ETH1")
#     for dev in devices_names:
#         t = threading.Thread(target=get_device_name, args=(dev, results))
#         thread_list.append(t)
#         t.start()

#     for t in thread_list:
#         t.join()

#     for k, v in results.items():
#         assert k == v

