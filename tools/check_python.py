"""Check the interpreter without PowerShell native-command quoting hazards."""

import struct
import sys
import sysconfig

assert sys.platform == "win32", sys.platform
assert struct.calcsize("P") == 8, "64-bit Python is required"
assert sysconfig.get_platform() == "win-amd64", sysconfig.get_platform()
assert ".".join(map(str, sys.version_info[:3])) == sys.argv[1], sys.version
assert not sysconfig.get_config_var("Py_GIL_DISABLED"), "Free-threaded Python is not supported"
