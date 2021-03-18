# import unittest

# import pyfgc
# import pyfgc_name


# class TestFgcPerformance(unittest.TestCase):

#     def setUp(self):
#         pass


#     def test_get_sync_evt_log(self):

#         with pyfgc.fgc("RFNA.866.*.ETH5", "sync") as fgcs:

#             r = pyfgc.get("LOG.EVT")
#             self.assertEqual(len(fgcs), len(r.keys()))


#     def test_get_async_evt_log(self):

#         with pyfgc.fgc("RFNA.866.*.ETH5", "async") as fgcs:

#             r = pyfgc.get("LOG.EVT")
#             self.assertEqual(len(fgcs), len(r.keys()))


#     def tearDown(self):
#         pass


# if __name__ == '__main__':
#     unittest.main(verbose=2)
