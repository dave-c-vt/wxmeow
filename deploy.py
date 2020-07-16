from os.path import dirname, join, realpath
import subprocess
import sys
from time import sleep


venv_name = 'venv'
venv_root = join(dirname(__file__), venv_name)

if sys.platform == 'win32':
    venv_python = join(venv_root, 'Scripts/python3')
    venv_activate = join(venv_root, 'Scripts/activate')
else:
    venv_python = join(venv_root, 'bin/python3')
    venv_activate = "source " + join(venv_root, 'bin/activate')

print(venv_python)
print(venv_activate)

if __name__ == "__main__":
    """creates a virtual environment for and initializes database file"""
    import venv

    venv.create(venv_name, with_pip=True)

    subprocess.check_call([venv_python, "-m", "pip", "install", "-e", "."])
    subprocess.check_call([venv_python, "-m", "flask", "run"])
#    subprocess.check_call([venv_activate])
#    subprocess.check_call(["flask", "run"])
