import curses
import time
from .player import KaraokePlayer

def main(stdscr):
    curses.curs_set(0)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    player = KaraokePlayer(stdscr)
    try:
        player.run()
    finally:
        player.cleanup()

def run():
    print("Terminal Karaoke - Loading...")
    print("Controls:")
    print("  p: Pause/Play")
    print("  ←: Back 5s")
    print("  →: Forward 5s")
    print("  q: Quit")
    print("\nStarting in 2 seconds...")
    time.sleep(2)
    curses.wrapper(main)

if __name__ == "__main__":
    run()