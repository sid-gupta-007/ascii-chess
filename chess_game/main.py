import sys
from .utils import clear_screen
from .ui import InteractiveGame, ClassicGame

def main():
    clear_screen()
    print()
    print('  ╔═══════════════════════════════════════════════════╗')
    print('  ║                                                   ║')
    print('  ║             ░█▀▀░█░█░█▀▀░█▀▀░█▀▀                  ║')
    print('  ║             ░█░░░█▀█░█▀▀░▀▀█░▀▀█                  ║')
    print('  ║             ░▀▀▀░▀░▀░▀▀▀░▀▀▀░▀▀▀                  ║')
    print('  ║                                                   ║')
    print('  ║          A S C I I   C H E S S                    ║')
    print('  ║            Terminal Edition v2.0                  ║')
    print('  ║              Two-Player Game                      ║')
    print('  ║                                                   ║')
    print('  ╠═══════════════════════════════════════════════════╣')
    print('  ║                                                   ║')
    print('  ║   SELECT YOUR MODE:                               ║')
    print('  ║                                                   ║')
    print('  ║     [1]  Classic Mode                             ║')
    print('  ║          Type moves like "e2 e4"                  ║')
    print('  ║          Simple and straightforward               ║')
    print('  ║                                                   ║')
    print('  ║     [2]  Interactive Mode  ★ RECOMMENDED          ║')
    print('  ║          Use arrow keys + Enter to play           ║')
    print('  ║          Legal moves glow on the board!           ║')
    print('  ║          Just navigate, select, and move!         ║')
    print('  ║                                                   ║')
    print('  ╚═══════════════════════════════════════════════════╝')
    print()

    while True:
        try:
            choice = input('  Enter mode (1 or 2): ').strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice == '1':
            ClassicGame().run()
            break
        elif choice == '2':
            InteractiveGame().run()
            break
        else:
            print('  Please enter 1 or 2!')

    print()
    print('  Thanks for playing! Now go crush that teacher! ;)')
    print()

