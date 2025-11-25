import platform


if platform.system() == "Linux":
    from linux import *
elif platform.system() == "Windows":
    from windows import *
else:
    print(f"ERROR: Unrecognized platform {platform.system()}")
    exit(-1)
