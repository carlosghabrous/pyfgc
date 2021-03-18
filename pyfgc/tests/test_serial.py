# import os
# import pytest

# import pyfgc

# SERIAL_PORT = "/dev/tty.usbserial-FGCV31v10"
# if os.name == "nt":
# 	SERIAL_PORT = "COM3"

	
# def test_serial_connect_disconnect():
# 	with pyfgc.fgc(SERIAL_PORT, protocol="serial") as _:
# 		pass

# def test_serial_get():
# 	with pyfgc.fgc(SERIAL_PORT, protocol="serial") as fgc_session:
# 		r = fgc_session.get("DEVICE.NAME")

# 	assert r.value == "STANDALONE"

# def test_serial_get_ppm():
# 	with pyfgc.fgc(SERIAL_PORT, protocol="serial") as fgc_session:
# 		r_0 = fgc_session.get("REF.FUNC.PLAY(0)")

# 	assert r_0.value == "DISABLED"

# def test_serial_get_array():
# 	limits_i_rate = pyfgc.get(SERIAL_PORT, "LIMITS.I.RATE", protocol="serial")
# 	assert len(limits_i_rate.value.split(",")) != 0


# def test_serial_set():
# 	import random

# 	with pyfgc.fgc(SERIAL_PORT, protocol="serial") as fgc_session:
# 		random_limits_i_rate = random.randint(1,10)
# 		fgc_session.set("LIMITS.I.RATE[0]", random_limits_i_rate)
# 		limits_i_rate = fgc_session.get("LIMITS.I.RATE[0]")

# 		assert limits_i_rate.value == random_limits_i_rate
