import pyuac
import os, sys


# argument should be 1 to install, 0 to uninstall
def main():
    if not pyuac.isUserAdmin():
        pyuac.runAsAdmin()

    start = int(sys.argv[1])

    user = os.environ.get("USERNAME")
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    start_path = f"C:/Users/{user}/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/headsup.bat"
    run_cmd = f"py -3.12 {script_dir}/main.py"

    if start:
        print("Installing startup...")
        with open(start_path, "w") as f:
            f.write(run_cmd)
    else:
        print("Uninstalling startup...")
        try:
            os.remove(start_path)
        except:
            pass


if __name__ == "__main__":
    main()

