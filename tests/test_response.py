import pytest
import re
from pytest import mark

import hypothesis.strategies as hs
from hypothesis             import assume
from hypothesis             import given

from pyfgc.fgc_response import FgcSingleResponse, FgcResponse, FgcResponseError

# Serial

SCRP_SUCCESS = rb"\$(?!\xff)([\w\W]*)\n;"
RE_SCRP_SUCCESS = re.compile(SCRP_SUCCESS)

SCRP_ERROR = br"\$[\w\W]*\$(\d{1,})([a-zA-Z\s]*)\n!"
RE_SCRP_ERROR = re.compile(SCRP_ERROR)

SCRP_SUCCESS_BIN = br"\$\xff([\x00-\xff]*)\n;$"
RE_SCRP_SUCCESS_BIN = re.compile(SCRP_SUCCESS_BIN)

# Sync & Async
NET_SUCCESS    = br"\$(\d{0,31})\s{1}\.\n(?!\xff)([\w\W]*)\n;"
RE_NET_SUCCESS = re.compile(NET_SUCCESS)

NET_SUCCESS_BIN = rb"\$(\d{0,31})\s{1}\.\n\xff([\x00-\xff]*)\n;$"
RE_NET_SUCCESS_BIN = re.compile(NET_SUCCESS_BIN)

NET_ERROR = rb"\$(\d{0,31})\s{1}!\n(\d{1,})([a-zA-Z\s]*)\n;"
RE_NET_ERROR = re.compile(NET_ERROR)
    
OK_FORMATTED_ERROR = br"\$(\d{0,31})\s{1}!\n([\w\W]*)\n;"
RE_ERROR = re.compile(OK_FORMATTED_ERROR)

FGC_NAME = r"R[A-Za-z]{4}\.\d{1,3}\.\d{1,2}\.eth\d{1}"

# ----- FgcSingleResponse tests ----- #

@pytest.mark.parametrize("protocol", ("serial", "sync", "async"))
@given(hs.text())
def test_fgc_single_response_can_be_built_from_valid_parameters(protocol, raw_rsp):
    fgc_sing_res = FgcSingleResponse(protocol, raw_rsp.encode())


@pytest.mark.parametrize("protocol", ("serial", "sync", "async"))
@given(hs.one_of(hs.text(), hs.integers()))
def test_fgc_single_response_only_accepts_bytes(protocol, raw_rsp):
    with pytest.raises(TypeError):
        fgc_single_rsp = FgcSingleResponse(protocol, raw_rsp)


def test_fgc_single_response_components_should_be_accessible_as_named_attributes():
    fgc_res = FgcSingleResponse("sync")
    assert fgc_res.value == ""
    assert fgc_res.tag   == ""
    assert fgc_res.err_code == ""
    assert fgc_res.err_msg == ""

@given(hs.text(), hs.text(), hs.text(), hs.text())
def test_fgc_single_response_components_should_not_be_settable(new_value, new_tag, new_error_code, new_error_msg):
    fgc_res = FgcSingleResponse("async")
    with pytest.raises(AttributeError):
        fgc_res.value = new_value

    with pytest.raises(AttributeError):
        fgc_res.tag = new_tag

    with pytest.raises(AttributeError):
        fgc_res.err_code = new_error_code

    with pytest.raises(AttributeError):
        fgc_res.err_msg = new_error_msg


@given(hs.from_regex(NET_ERROR))
def test_fgc_single_response_raises_exception_if_it_contains_error_and_user_tries_to_get_value(raw_rsp):
    fgc_res = FgcSingleResponse("sync", raw_rsp)
    with pytest.raises(FgcResponseError):
        fgc_res.value


@given(hs.from_regex(SCRP_SUCCESS))
def test_fgc_single_response_parses_serial_no_err(raw_rsp):
    value = RE_SCRP_SUCCESS.search(raw_rsp).group(1)
    fgc_sing_res = FgcSingleResponse("serial", raw_rsp)
    assert fgc_sing_res.value == value.decode(errors="ignore")


@given(hs.from_regex(SCRP_SUCCESS_BIN))
def test_fgc_single_response_parses_serial_no_err_bin(raw_rsp):
    value = RE_SCRP_SUCCESS_BIN.search(raw_rsp).group(1)
    fgc_sing_res = FgcSingleResponse("serial", raw_rsp)
    assert fgc_sing_res.value == value.decode(errors="ignore")


@given(hs.from_regex(SCRP_ERROR))
def test_fgc_single_response_parses_serial_with_err(raw_rsp):
    err_code, err_msg = RE_SCRP_ERROR.search(raw_rsp).group(1), RE_SCRP_ERROR.search(raw_rsp).group(2)
    fgc_sing_res = FgcSingleResponse("serial", raw_rsp)
    
    assert fgc_sing_res.err_code == err_code.decode(errors="ignore")
    assert fgc_sing_res.err_msg  == err_msg.decode(errors="ignore")


@given(hs.from_regex(NET_SUCCESS))
def test_fgc_single_response_parses_sync_no_err(raw_rsp):
    value = RE_NET_SUCCESS.search(raw_rsp).group(2)
    fgc_sing_res = FgcSingleResponse("sync", raw_rsp)
    assert fgc_sing_res.value == value.decode(errors="ignore")


@given(hs.from_regex(NET_SUCCESS_BIN))
def test_fgc_single_response_parses_sync_no_err_bin(raw_rsp):
    value = RE_NET_SUCCESS_BIN.search(raw_rsp).group(2)
    fgc_sing_res = FgcSingleResponse("sync", raw_rsp)
    assert fgc_sing_res.value == value.decode(errors="ignore")


@given(hs.from_regex(NET_ERROR))
def test_fgc_single_response_parses_sync_with_err(raw_rsp):
    err_code, err_msg = RE_NET_ERROR.search(raw_rsp).group(2), RE_NET_ERROR.search(raw_rsp).group(3)
    fgc_sing_res = FgcSingleResponse("sync", raw_rsp)
    
    assert fgc_sing_res.err_code == err_code.decode(errors="ignore")
    assert fgc_sing_res.err_msg  == err_msg.decode(errors="ignore")


@given(hs.from_regex(NET_SUCCESS))
def test_fgc_single_response_parses_async_no_err(raw_rsp):
    tag, value = RE_NET_SUCCESS.search(raw_rsp).group(1), RE_NET_SUCCESS.search(raw_rsp).group(2)
    fgc_sing_res = FgcSingleResponse("async", raw_rsp)
    assert fgc_sing_res.tag   == tag.decode(errors="ignore")
    assert fgc_sing_res.value == value.decode(errors="ignore")


@given(hs.from_regex(NET_SUCCESS_BIN))
def test_fgc_single_response_parses_async_no_err_bin(raw_rsp):
    tag, value = RE_NET_SUCCESS_BIN.search(raw_rsp).group(1), RE_NET_SUCCESS_BIN.search(raw_rsp).group(2)
    fgc_sing_res = FgcSingleResponse("async", raw_rsp)
    assert fgc_sing_res.tag   == tag.decode(errors="ignore")
    assert fgc_sing_res.value == value.decode(errors="ignore")


@given(hs.from_regex(NET_ERROR))
def test_fgc_single_response_parses_async_with_err(raw_rsp):
    tag      = RE_NET_ERROR.search(raw_rsp).group(1)
    err_code = RE_NET_ERROR.search(raw_rsp).group(2)
    err_msg  = RE_NET_ERROR.search(raw_rsp).group(3)
    
    fgc_sing_res = FgcSingleResponse("async", raw_rsp)
    
    assert fgc_sing_res.tag      == tag.decode(errors="ignore")
    assert fgc_sing_res.err_code == err_code.decode(errors="ignore")
    assert fgc_sing_res.err_msg  == err_msg.decode(errors="ignore")


# ----- FgcResponse tests ----- #
import random

# Just a helper to generate strategies in following tests
@hs.composite
def dict_key_and_value(draw, devices=hs.from_regex(FGC_NAME), dev_resps=hs.from_regex(NET_SUCCESS), max_size=None, errors_only=False):
    if errors_only:
        dev_resps = hs.from_regex(NET_ERROR)
        
    fgc_rsp = draw(hs.dictionaries(devices, dev_resps, min_size=1, max_size=max_size))
    device = list(fgc_rsp.keys())[random.randint(0, len(fgc_rsp.keys()) - 1)]
    return (fgc_rsp, device, fgc_rsp[device])


def test_fgc_response_can_accept_empty_response():
    fgc_rsp = FgcResponse("sync")
    assert fgc_rsp.value    == "" 
    assert fgc_rsp.tag      == ""
    assert fgc_rsp.err_code == ""
    assert fgc_rsp.err_msg  == ""


@given(hs.from_regex(FGC_NAME), hs.from_regex(NET_SUCCESS))
def test_fgc_response_items_are_settable(device, raw_rsp):
    fgc_rsp = FgcResponse("async")
    fgc_rsp[device] = FgcSingleResponse("async", raw_rsp)

    with pytest.raises(TypeError):
        fgc_rsp[device] = b";laksdjfad"


@given(hs.from_regex(FGC_NAME))
def test_fgc_response_is_not_allowed_to_have_different_protocols(device):
        fgc_rsp = FgcResponse("async")
        with pytest.raises(FgcResponseError):
            fgc_rsp[device] = FgcSingleResponse("serial")


@pytest.mark.parametrize("protocol", ("serial", "sync", "async"))
@given(dict_key_and_value())
def test_fgc_response_constructor_with_valid_protocol(protocol, dict_key_and_value):
    raw_rsp, device, _ = dict_key_and_value
    fgc_rsp = FgcResponse(protocol, raw_rsp)

    assert(fgc_rsp is not None)
    

@given(hs.text(), dict_key_and_value())
def test_fgc_response_constructor_throws_exception_if_unknown_protocol(protocol, dict_key_and_value):
    raw_rsp, *_ = dict_key_and_value
    assume(protocol not in ["serial", "sync", "async"])

    with pytest.raises(FgcResponseError):
        fgc_rsp = FgcResponse(protocol, raw_rsp)


@pytest.mark.parametrize("device, some_rsp", (("", "some_rsp"), (" ", "some_rsp")))
def test_fgc_multiple_response_does_not_accept_empty_devices(device, some_rsp):
    with pytest.raises(FgcResponseError):
        fgc_rsp = FgcResponse("sync", {device: some_rsp})
        

@given(dict_key_and_value())
def test_fgc_response_individual_items_are_accessible_by_keys(dict_key_and_value):
    test_rsp, device, _ = dict_key_and_value
    fgc_rsp = FgcResponse("async", test_rsp)

    fgc_rsp_single = fgc_rsp[device]
    assert (isinstance(fgc_rsp_single, FgcSingleResponse))

    value = RE_NET_SUCCESS.search(test_rsp[device]).group(2)
    assert fgc_rsp_single.value == value.decode(errors="ignore")


@given(dict_key_and_value(max_size=1))
def test_fgc_response_is_equivalent_to_indv_rsp_if_one_dev_only(dict_key_and_value):
    test_rsp, device, _ = dict_key_and_value
    fgc_rsp = FgcResponse("async", test_rsp)
    tag = RE_NET_SUCCESS.search(test_rsp[device]).group(1)
    value = RE_NET_SUCCESS.search(test_rsp[device]).group(2)
    assert fgc_rsp.value == value.decode(errors="ignore")


@given(dict_key_and_value(max_size=1, errors_only=True))
def test_fgc_response_is_equivalent_to_indv_rsp_if_one_dev_only_and_errs(dict_key_and_value):
    test_rsp, device, _ = dict_key_and_value
    fgc_rsp = FgcResponse("async", test_rsp)

    tag      = RE_NET_ERROR.search(test_rsp[device]).group(1)
    err_code = RE_NET_ERROR.search(test_rsp[device]).group(2)
    err_msg = RE_NET_ERROR.search(test_rsp[device]).group(3)
    
    assert fgc_rsp.tag == tag.decode(errors="ignore")
    assert fgc_rsp.err_msg  == err_msg.decode(errors="ignore")
    assert fgc_rsp.err_code == err_code.decode(errors="ignore")


@given(dict_key_and_value(max_size=1, errors_only=True))
def test_fgc_response_has_correct_length(dict_key_and_value):
    test_rsp, *_ = dict_key_and_value
    fgc_rsp = FgcResponse("sync", test_rsp)
    assert(len(test_rsp) == len(fgc_rsp))


@given(dict_key_and_value())
def test_fgc_response_is_iterable(dict_key_and_value):
    test_rsp, *_ = dict_key_and_value
    fgc_rsp = FgcResponse("sync", test_rsp)

    for k in fgc_rsp:
        assert fgc_rsp[k].value == RE_NET_SUCCESS.search(test_rsp[k]).group(2).decode(errors="ignore")
        

