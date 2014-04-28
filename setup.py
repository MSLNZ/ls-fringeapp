import cx_Freeze
import sys
import matplotlib
base = None
if sys.platform == "win32":
	base = "Win32GUI"

packages = []


for dbmodule in ['dbhash', 'gdbm', 'dbm', 'dumbdbm']:
    try:
        __import__(dbmodule)
    except ImportError:
        pass
    else:
        # If we found the module, ensure it's copied to the build directory.
        packages.append(dbmodule)

executables = [cx_Freeze.Executable("fringe_app_03.py", base = base),]

build_exe_options = {"includes":["matplotlib.backends.backend_tkagg"],
					 "include_files":[(matplotlib.get_data_path(), "mpl-data")],
                     "excludes":["PyQt4","scipy"],
					 "packages":packages}
cx_Freeze.setup(
	name = "script",
	options = {"build_exe": build_exe_options},
	version = "3.0",
	description = "Hilger Interferometer Image Processing",
	executables = executables)
