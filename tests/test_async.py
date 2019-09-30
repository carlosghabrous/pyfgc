import pytest
import pyfgc_name
import pyfgc

device_1 = "RFNA.866.06.ETH1"
device_2 = "RFNA.866.01.ETH2"
device_3 = "RFNA.866.02.ETH3"
devs_list = [device_1, device_3, "RFNA.866.01.ETH3"]
devs_regex = "^RFNA\.866\.d{1,}\.ETH\d$"


pyfgc_name.read_name_file()


def test_async_get_single():
    """
    Gets property from device.

    """

    prop = "DEVICE.NAME"

    r = pyfgc.get(device_1, prop, protocol="async")
    try:
        assert(r.value == device_1)
    except pyfgc.FgcResponseError:
        print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")
        assert True


def test_async_get_multiple():

    prop = "DEVICE.NAME"

    r = pyfgc.get("RFNA.866.*.ETH3", prop, protocol="async")
    for fgc in r:
        try:
            assert(fgc == r[fgc].value)
        except pyfgc.FgcResponseError:
            print(f"Error, device {fgc}, err_code {r[fgc].err_code}, err_msg {r[fgc].err_msg}")
            assert True


def test_async_set_single():

    value = 0.03
    with pyfgc.fgcs("RFNA.866.06.ETH1", protocol="async") as fgcs:
        r = fgcs.set("LIMITS.I.EARTH", value)
        get_rsp = fgcs.get("LIMITS.I.EARTH")
        try:
            assert (value == get_rsp.value)
        except pyfgc.FgcResponseError:
            print(f"Error, device {'RFNA.866.06.ETH1'}, err_code {r.err_code}, err_msg {r.err_msg}")
            assert True


def test_async_set_multiple():

    value = -0.23
    with pyfgc.fgcs("RFNA.866.*.ETH3", "async") as fgcs:
        r = fgcs.set("LIMITS.I.EARTH", value)
        r = fgcs.get("LIMITS.I.EARTH")

        for k in r:
            try:
                assert (value == r[k].value)
            except pyfgc.FgcResponseError:
                print(f"Error, device {'RFNA.866.06.ETH1'}, err_code {r[k].err_code}, err_msg {r[k].err_msg}")
                assert True
