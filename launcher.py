import os
import subprocess
import sys


def run_game():
    if getattr(sys, 'frozen', False):
        game_dir = os.path.dirname(sys.executable)
    else:
        game_dir = os.path.dirname(os.path.abspath(__file__))

    os.chdir(game_dir)

    if sys.platform == 'win32':
        subprocess.call(['cmd.exe', '/c', 'python', 'main.py'])
    else: #unix
        subprocess.call(['python3', 'main.py'])


if __name__ == '__main__':
    run_game()
