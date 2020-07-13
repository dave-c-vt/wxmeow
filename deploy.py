from os.path import dirname, join, realpath
import subprocess
import sys


venv_name = 'venv'
venv_root = join(dirname(__file__), venv_name)

if sys.platform == 'win32':
    venv_python = join(venv_root, 'Scripts/python3')
else:
    venv_python = join(venv_root, 'bin/python3')


if __name__ == "__main__":
    """creates a virtual environment for and initializes database file"""
    import venv

    venv.create(venv_name, with_pip=True)

    subprocess.check_call([venv_python, "-m", "pip", "install", "-e", "."])
