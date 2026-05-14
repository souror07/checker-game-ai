# Introducing myself
Hello! I'm a beginner programmer, and this is my first complete project.  
I built this Checkers game to practice Python, game logic, and basic AI development.

I'm continuously learning and improving, and this project represents an important step in my journey.

---
# Checker Game

A polished desktop **Checkers game with AI** built in Python using `tkinter`.  
This project provides a clean graphical interface, mandatory capture rules, king promotion, board flipping, multiple AI difficulty levels, and a smooth gameplay experience for both casual and more advanced players.

---

## Features

- Full checkers gameplay on an 8×8 board
- Human vs AI mode
- Multiple difficulty levels:
  - Beginner
  - Easy
  - Normal
  - Hard
  - Expert
- Mandatory capture enforcement
- Multi-jump capture support
- King promotion for both sides
- Turn tracking and game-over detection
- Move highlighting and visual feedback
- Board flip option for better viewing
- Evaluation bar showing AI advantage
- Modern-looking Tkinter interface

---

## How to Run

### Option 1: Run the EXE file
If you downloaded the compiled version, simply open the `.exe` file.

### Option 2: Run from Python source
If you have the source code:

```bash
python project_of_the_year.py
```

Make sure you have Python installed on your system.

---

## Requirements

- Python 3.x
- `tkinter` (usually included with Python)
- No extra third-party packages are required

---

## Gameplay Rules

- Red is the human player.
- Black is controlled by the AI.
- Captures are mandatory when available.
- Pieces move diagonally.
- Normal pieces move forward only.
- Kings can move diagonally in all directions.
- A piece becomes a king when it reaches the opposite end of the board.

---

## AI Difficulty

The AI supports several difficulty levels:

- **Beginner**: weaker and more random
- **Easy**: simple but still challenging
- **Normal**: balanced difficulty
- **Hard**: stronger and more strategic
- **Expert**: best available move selection

The AI uses an alpha-beta search strategy with move ordering and evaluation heuristics.

---

## Project Structure

```text
Checker Game/
├── project_of_the_year.py
├── README.md
└── (optional build files or exe)
```

---

## Notes

- This project was designed to be playable, visually clear, and stable.
- The interface includes move highlighting, turn indicators, and game-over dialogs.
- The compiled `.exe` version is suitable for direct use on Windows.

---

## Screenshots

You can add screenshots here later if you want to showcase the game interface.

---
## Future Improvements

- Add sound effects
- Improve AI performance
- Add multiplayer mode
- Enhance UI/UX

## License

This project is currently released without a specific license.

---

## Author

Created by **[souror07]**
