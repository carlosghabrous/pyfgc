# import pytest

# import pyfgc_name
# from pyfgc import channel_manager

# import asyncio
# import threading
# import time

# pyfgc_name.read_name_file()

# FGC1  = "RPAGM.866.21.ETH1"
# FGC2  = "RPZES.866.15.ETH1"
# RETH1 = "cfc-866-reth1"

# FGC3 = "RFNA.866.01.ETH1"
# FGC4 = "RFNA.866.01.ETH2"
# RETH2 = "cfc-866-reth2"

# CHANNEL_TYPES = ("serial", "monitor", "terminal")

# def test_get_channel_from_unknown_type_raises_exception():
#     with pytest.raises(NotImplementedError):
#         _ = channel_manager.get_channel(FGC1, "unknown channel type", "")

# @pytest.mark.parametrize("channel_type", CHANNEL_TYPES)
# def test_get_channel_can_be_called_using_channel_type_and_fgc(channel_type):
#     channel = channel_manager.get_channel(FGC1, channel_type, RETH1)
#     assert channel is not None
#     channel_manager.free_channel(FGC1, channel_type, RETH1)

# @pytest.mark.parametrize("channel_type", CHANNEL_TYPES)
# def test_get_channel_data_throws_exception_if_channel_not_initialized_first(channel_type):
#     with pytest.raises(KeyError):
#         _ = channel_manager.get_channel_data(FGC1, channel_type, RETH1)

# @pytest.mark.parametrize("channel_type", CHANNEL_TYPES)
# def test_channel_is_acquired_and_freed(channel_type):
#     channel = channel_manager.get_channel(FGC1, channel_type, RETH1)
#     assert channel is not None
#     channel_manager.free_channel(FGC1, channel_type, RETH1)

#     with pytest.raises(KeyError):
#         _ = channel_manager.get_channel_data(FGC1, channel_type, RETH1)
    
# @pytest.mark.parametrize("channel_type", CHANNEL_TYPES)
# def test_get_channel_data_makes_sense(channel_type):
#     _ = channel_manager.get_channel(FGC1, channel_type, RETH1)
#     channel_data = channel_manager.get_channel_data(FGC1, channel_type, RETH1)
#     assert channel_data.clients             == 1
#     assert channel_data.channel_ref_count   == 1
#     assert channel_data.channel is not None
#     channel_manager.free_channel(FGC1, channel_type, RETH1)

# @pytest.mark.parametrize("channel_type", CHANNEL_TYPES)
# def test_reference_count_general(channel_type):
#     _ = channel_manager.get_channel(FGC1, channel_type, RETH1)
#     fgc1_channel_data = channel_manager.get_channel_data(FGC1, channel_type, RETH1)
#     assert fgc1_channel_data.channel_ref_count == 1
#     assert fgc1_channel_data.clients           == 1

#     _ = channel_manager.get_channel(FGC2, channel_type, RETH1)
#     fgc2_channel_data = channel_manager.get_channel_data(FGC2, channel_type, RETH1)
    
#     expected = 2 if channel_type == "async" else 1
#     assert fgc2_channel_data.channel_ref_count == expected
#     fgc1_channel_data = channel_manager.get_channel_data(FGC1, channel_type, RETH1)
#     assert fgc1_channel_data.channel_ref_count == expected
#     assert fgc1_channel_data.clients           == 1
#     assert fgc2_channel_data.clients           == 1

#     channel_manager.free_channel(FGC1, channel_type, RETH1)
#     fgc2_channel_data = channel_manager.get_channel_data(FGC2, channel_type, RETH1)
#     assert fgc2_channel_data.channel_ref_count == 1

#     channel_manager.free_channel(FGC2, channel_type, RETH1)
#     with pytest.raises(KeyError):
#         fgc2_channel_data = channel_manager.get_channel_data(FGC2, channel_type, RETH1)

# @pytest.mark.parametrize("channel_type", CHANNEL_TYPES)
# def test_reference_count_multiple_reference_same_device(channel_type):
#     _ = channel_manager.get_channel(FGC1, channel_type, RETH1)
#     fgc1_channel_data = channel_manager.get_channel_data(FGC1, channel_type, RETH1)
#     assert fgc1_channel_data.channel_ref_count == 1
#     assert fgc1_channel_data.clients           == 1
    
#     _ = channel_manager.get_channel(FGC1, channel_type, RETH1)
#     fgc1_channel_data = channel_manager.get_channel_data(FGC1, channel_type, RETH1)
#     assert fgc1_channel_data.channel_ref_count == 1
#     assert fgc1_channel_data.clients == 2

#     channel_manager.free_channel(FGC1, channel_type, RETH1)
#     channel_manager.free_channel(FGC1, channel_type, RETH1)
    
# def test_sync_channel_is_shared_different_threads():
#     def get_channel_from_manager(fgc, gw, res):
#         channel = channel_manager.get_channel(fgc, "sync", gw)
#         results[fgc] = id(channel)

#     results = dict()
#     t1 = threading.Thread(target=get_channel_from_manager, args=(FGC1, RETH1, results))
#     t2 = threading.Thread(target=get_channel_from_manager, args=(FGC2, RETH1, results))

#     t1.start()
#     t2.start()
#     t1.join()
#     t2.join()
#     assert len(set(results.values())) == 1

# def test_reference_count_random_configuration():
#     # Two async clients for FGC1
#     _ = channel_manager.get_channel(FGC1, "async", RETH1)
#     _ = channel_manager.get_channel(FGC1, "async", RETH1)
#     fgc1_channel_data = channel_manager.get_channel_data(FGC1, "async", RETH1)
#     assert fgc1_channel_data.channel_ref_count == 1
#     assert fgc1_channel_data.clients           == 2
    
#     # Three clients for FGC2
#     _ = channel_manager.get_channel(FGC2, "async", RETH1)
#     _ = channel_manager.get_channel(FGC2, "terminal", RETH1)
#     _ = channel_manager.get_channel(FGC2, "monitor", RETH1)
#     fgc1_channel_data     = channel_manager.get_channel_data(FGC1, "async", RETH1)
#     fgc2_channel_data_asy = channel_manager.get_channel_data(FGC2, "async", RETH1)
#     fgc2_channel_data_ter = channel_manager.get_channel_data(FGC2, "terminal", RETH1)
#     fgc2_channel_data_mon = channel_manager.get_channel_data(FGC2, "monitor", RETH1)
    
#     # Make sure same resource is used for FGC1 and FGC2 in async
#     assert fgc1_channel_data.channel == fgc2_channel_data_asy.channel

#     assert fgc1_channel_data.channel_ref_count == fgc2_channel_data_asy.channel_ref_count
#     assert fgc2_channel_data_ter.channel_ref_count == 1
#     assert fgc2_channel_data_ter.clients           == 1
#     assert fgc2_channel_data_mon.channel_ref_count == 1
#     assert fgc2_channel_data_mon.clients           == 1

#     # Two async clients for FGC3
#     _ = channel_manager.get_channel(FGC3, "async", RETH1)
#     _ = channel_manager.get_channel(FGC3, "async", RETH1)
#     fgc3_channel_data = channel_manager.get_channel_data(FGC3, "async", RETH1)
#     assert fgc3_channel_data.channel == fgc1_channel_data.channel
#     assert fgc3_channel_data.channel_ref_count == 3
#     assert fgc3_channel_data.clients == 2
    
# #     # Monitor clients for FGC4/RETH2
# #     _ = channel_manager.get_channel(FGC4, "monitor", RETH2)
# #     _ = channel_manager.get_channel(FGC4, "monitor", RETH2)
# #     fgc4_channel_data = channel_manager.get_channel_data(FGC4, "monitor", RETH2)
# #     assert fgc4_channel_data.channel_ref_count == 1
# #     assert fgc4_channel_data.clients           == 2
    
# #     # FGC3 and FGC2 async clients go away
# #     _ = channel_manager.free_channel(FGC3, "async", RETH1)
# #     _ = channel_manager.free_channel(FGC2, "async", RETH1)
# #     fgc3_channel_data = channel_manager.get_channel_data(FGC3, "async", RETH1)
# #     assert fgc3_channel_data.channel_ref_count == 2
    
# #     fgc2_channel_data_ter = channel_manager.get_channel_data(FGC2, "terminal", RETH1)
# #     fgc2_channel_data_mon = channel_manager.get_channel_data(FGC2, "monitor", RETH1)
# #     assert fgc2_channel_data_ter.channel_ref_count == 1
# #     assert fgc2_channel_data_mon.channel_ref_count == 1

#     # FGC1 clients go away. Then FGC3's
#     # _ = channel_manager.free_channel(FGC1, "async", RETH1)
#     # _ = channel_manager.free_channel(FGC1, "async", RETH1)
#     # fgc3_channel_data_asy = channel_manager.get_channel_data(FGC3, "async", RETH1)
#     # assert fgc3_channel_data_asy.channel_ref_count == 1

#     # _ = channel_manager.free_channel(FGC3, "async", RETH1)
#     # with pytest.raises(KeyError):
#     #     fgc3_channel_data_asy = channel_manager.get_channel_data(FGC3, "async", RETH1)


# def test_create_destroy_async_channel():
#     el = asyncio.get_event_loop()
#     ac = channel_manager.get_channel(FGC1, "async", RETH1)
    
#     el.run_until_complete(ac.create())
#     assert ac.reader is not None
#     assert ac.writer is not None

#     ac.destroy()
#     el.close()
#     # el.run_until_complete(ac.destroy())



