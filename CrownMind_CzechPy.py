import copy
import math
import random
import tkinter as tk
from tkinter import ttk

EMPTY = "."
RED = "r"
RED_KING = "R"
BLACK = "b"
BLACK_KING = "B"

BOARD_SIZE = 8
CELL_SIZE = 78

# Difficulty levels
DIFFICULTY_LEVELS = {
    "Beginner": {"depth": 1, "mix": 0.50},
    "Easy": {"depth": 2, "mix": 0.25},
    "Normal": {"depth": 3, "mix": 0.12},
    "Hard": {"depth": 4, "mix": 0.05},
    "Expert": {"depth": 5, "mix": 0.00},
}
DEFAULT_DIFFICULTY = "Normal"
TRANSPOSITION_TABLE = {}


# =================================================
# Core helpers
# =================================================
def make_move(start, path, captured=None):
    return {
        "start": tuple(start),
        "path": [tuple(p) for p in path],
        "captured": [tuple(p) for p in (captured or [])],
    }


def move_end(move):
    return move["path"][-1]


def inside(row, col):
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def is_red(piece):
    return piece in (RED, RED_KING)


def is_black(piece):
    return piece in (BLACK, BLACK_KING)


def is_king(piece):
    return piece in (RED_KING, BLACK_KING)


def directions(piece):
    if piece == RED:
        return [(-1, -1), (-1, 1)]
    if piece == BLACK:
        return [(1, -1), (1, 1)]
    return [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def board_key(board):
    return tuple(tuple(row) for row in board)


def create_board():
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for row in range(3):
        for col in range(BOARD_SIZE):
            if (row + col) % 2 == 1:
                board[row][col] = BLACK
    for row in range(5, 8):
        for col in range(BOARD_SIZE):
            if (row + col) % 2 == 1:
                board[row][col] = RED
    return board


def count_pieces(board):
    red_count = 0
    black_count = 0
    for row in board:
        for piece in row:
            if is_red(piece):
                red_count += 1
            elif is_black(piece):
                black_count += 1
    return red_count, black_count


# =================================================
# Move generation
# =================================================
def simple_moves_for_piece(board, row, col):
    piece = board[row][col]
    if piece == EMPTY:
        return []

    moves = []
    for dr, dc in directions(piece):
        nr, nc = row + dr, col + dc
        if inside(nr, nc) and board[nr][nc] == EMPTY:
            moves.append(make_move((row, col), [(nr, nc)]))
    return moves


def jump_sequences_from(board, row, col, start_pos=None, path=None, captured=None):
    piece = board[row][col]
    if piece == EMPTY:
        return []

    if start_pos is None:
        start_pos = (row, col)
    if path is None:
        path = []
    if captured is None:
        captured = []

    sequences = []
    found_any = False

    for dr, dc in directions(piece):
        mid_r, mid_c = row + dr, col + dc
        land_r, land_c = row + 2 * dr, col + 2 * dc

        if not (inside(mid_r, mid_c) and inside(land_r, land_c)):
            continue
        if board[land_r][land_c] != EMPTY:
            continue

        middle_piece = board[mid_r][mid_c]
        if middle_piece == EMPTY:
            continue

        if is_red(piece) and not is_black(middle_piece):
            continue
        if is_black(piece) and not is_red(middle_piece):
            continue

        found_any = True
        next_board = copy.deepcopy(board)
        next_board[row][col] = EMPTY
        next_board[mid_r][mid_c] = EMPTY

        next_piece = piece
        if piece == RED and land_r == 0:
            next_piece = RED_KING
        elif piece == BLACK and land_r == BOARD_SIZE - 1:
            next_piece = BLACK_KING

        next_board[land_r][land_c] = next_piece
        new_path = path + [(land_r, land_c)]
        new_captured = captured + [(mid_r, mid_c)]

        # Promotion ends the jump sequence.
        if next_piece != piece:
            sequences.append(make_move(start_pos, new_path, new_captured))
            continue

        deeper = jump_sequences_from(
            next_board,
            land_r,
            land_c,
            start_pos=start_pos,
            path=new_path,
            captured=new_captured,
        )

        if deeper:
            sequences.extend(deeper)
        else:
            sequences.append(make_move(start_pos, new_path, new_captured))

    return sequences if found_any else []


def get_all_moves(board, player):
    normal_moves = []
    jump_moves = []

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = board[row][col]
            if piece == EMPTY:
                continue

            if player == "red" and is_red(piece):
                normal_moves.extend(simple_moves_for_piece(board, row, col))
                jump_moves.extend(jump_sequences_from(board, row, col))
            elif player == "black" and is_black(piece):
                normal_moves.extend(simple_moves_for_piece(board, row, col))
                jump_moves.extend(jump_sequences_from(board, row, col))

    return jump_moves if jump_moves else normal_moves


def legal_starts(board, player):
    return {move["start"] for move in get_all_moves(board, player)}


# =================================================
# Apply move / winner
# =================================================
def apply_move(board, move):
    new_board = copy.deepcopy(board)
    if move is None:
        return new_board

    start_r, start_c = move["start"]
    end_r, end_c = move_end(move)
    piece = new_board[start_r][start_c]

    new_board[start_r][start_c] = EMPTY
    for cap_r, cap_c in move["captured"]:
        new_board[cap_r][cap_c] = EMPTY

    if piece == RED and end_r == 0:
        piece = RED_KING
    elif piece == BLACK and end_r == BOARD_SIZE - 1:
        piece = BLACK_KING

    new_board[end_r][end_c] = piece
    return new_board


def get_winner(board):
    red_count, black_count = count_pieces(board)
    red_moves = len(get_all_moves(board, "red"))
    black_moves = len(get_all_moves(board, "black"))

    if red_count == 0 and black_count == 0:
        return "draw"
    if red_count == 0:
        return "black"
    if black_count == 0:
        return "red"
    if red_moves == 0 and black_moves == 0:
        return "draw"
    if red_moves == 0:
        return "black"
    if black_moves == 0:
        return "red"
    return None


def game_over(board):
    return get_winner(board) is not None


# =================================================
# Evaluation / AI
# =================================================
def evaluate(board):
    # Positive = black advantage, Negative = red advantage
    score = 0.0

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = board[r][c]
            if piece == EMPTY:
                continue

            center_bonus = 1.0 - (abs(3.5 - c) / 3.5)
            advance_bonus = (r / 7.0) if piece in (BLACK, BLACK_KING) else ((7 - r) / 7.0)

            if piece == BLACK:
                score += 1.0 + 0.20 * advance_bonus + 0.08 * center_bonus
            elif piece == BLACK_KING:
                score += 2.15 + 0.10 * center_bonus
            elif piece == RED:
                score -= 1.0 + 0.20 * advance_bonus + 0.08 * center_bonus
            elif piece == RED_KING:
                score -= 2.15 + 0.10 * center_bonus

    score += 0.03 * (len(get_all_moves(board, "black")) - len(get_all_moves(board, "red")))
    return score


def move_heuristic(board, move):
    start_r, start_c = move["start"]
    end_r, end_c = move_end(move)
    piece = board[start_r][start_c]

    capture_bonus = 100 * len(move["captured"])
    promotion_bonus = 25 if ((piece == BLACK and end_r == BOARD_SIZE - 1) or (piece == RED and end_r == 0)) else 0
    center_bonus = 4 - abs(3.5 - end_c)
    progress_bonus = 0.5 if ((piece in (BLACK, BLACK_KING) and end_r > start_r) or (piece in (RED, RED_KING) and end_r < start_r)) else 0.0

    return capture_bonus + promotion_bonus + center_bonus + progress_bonus


def alpha_beta(board, depth, alpha, beta, maximizing):
    key = (board_key(board), depth, maximizing)
    if key in TRANSPOSITION_TABLE:
        return TRANSPOSITION_TABLE[key]

    winner = get_winner(board)
    if depth == 0 or winner is not None:
        result = (evaluate(board), None)
        TRANSPOSITION_TABLE[key] = result
        return result

    player = "black" if maximizing else "red"
    moves = get_all_moves(board, player)
    if not moves:
        result = (evaluate(board), None)
        TRANSPOSITION_TABLE[key] = result
        return result

    moves.sort(key=lambda m: move_heuristic(board, m), reverse=True)

    best_move = moves[0]
    if maximizing:
        best_value = -math.inf
        for move in moves:
            value, _ = alpha_beta(apply_move(board, move), depth - 1, alpha, beta, False)
            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, best_value)
            if beta <= alpha:
                break
    else:
        best_value = math.inf
        for move in moves:
            value, _ = alpha_beta(apply_move(board, move), depth - 1, alpha, beta, True)
            if value < best_value:
                best_value = value
                best_move = move
            beta = min(beta, best_value)
            if beta <= alpha:
                break

    result = (best_value, best_move)
    TRANSPOSITION_TABLE[key] = result
    return result


def alpha_beta_root_moves(board, depth):
    moves = get_all_moves(board, "black")
    if not moves:
        return []

    moves.sort(key=lambda m: move_heuristic(board, m), reverse=True)
    scored = []
    for move in moves:
        value, _ = alpha_beta(apply_move(board, move), depth - 1, -math.inf, math.inf, False)
        scored.append((value, move))

    scored.sort(key=lambda item: item[0], reverse=True)
    return scored


def choose_move_by_difficulty(scored_moves, difficulty_name):
    if not scored_moves:
        return None, None

    meta = DIFFICULTY_LEVELS[difficulty_name]
    mix = meta["mix"]

    # Expert: always pick the best move.
    if difficulty_name == "Expert" or mix == 0:
        return scored_moves[0]

    # Pick among the top moves, but bias toward the best one.
    if difficulty_name == "Hard":
        pool = scored_moves[:min(3, len(scored_moves))]
        weights = [0.78, 0.16, 0.06][:len(pool)]
        return random.choices(pool, weights=weights, k=1)[0]

    if difficulty_name == "Normal":
        pool = scored_moves[:min(4, len(scored_moves))]
        weights = [0.52, 0.24, 0.16, 0.08][:len(pool)]
        return random.choices(pool, weights=weights, k=1)[0]

    if difficulty_name == "Easy":
        pool = scored_moves[:min(5, len(scored_moves))]
        weights = [0.34, 0.24, 0.18, 0.14, 0.10][:len(pool)]
        return random.choices(pool, weights=weights, k=1)[0]

    # Beginner: intentionally weaker, with a wider spread.
    pool = scored_moves[:min(6, len(scored_moves))]
    weights = [0.24, 0.20, 0.18, 0.15, 0.13, 0.10][:len(pool)]
    return random.choices(pool, weights=weights, k=1)[0]


def score_to_bar_value(score):
    return max(0, min(100, 50 + score * 10))


# =================================================
# GUI
# =================================================
class CheckersGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CrownMind CzechPy")
        self.root.geometry("1320x860")
        self.root.minsize(1220, 780)
        self.root.configure(bg="#0B1220")

        self.board = create_board()
        self.turn = "red"
        self.selected = None
        self.valid_moves = []
        self.last_move = None
        self.ai_busy = False
        self.view_flipped = False
        self.thinking_ticks = 0

        self.difficulty_var = tk.StringVar(value=DEFAULT_DIFFICULTY)
        self.status_var = tk.StringVar(value="Your turn.")
        self.score_var = tk.StringVar(value="AI eval: 0.00")
        self.turn_var = tk.StringVar(value="Turn: Human")
        self.depth_text_var = tk.StringVar(value=self._difficulty_label(DEFAULT_DIFFICULTY))
        self.red_count_var = tk.StringVar(value="Red pieces: 12")
        self.black_count_var = tk.StringVar(value="Black pieces: 12")
        self.live_state_var = tk.StringVar(value="READY")

        self._setup_style()
        self._build_layout()
        self.draw_board()
        self.refresh_sidebar(ai_score=0.0)
        self.animate_ui()

    def _difficulty_label(self, name):
        meta = DIFFICULTY_LEVELS[name]
        return f"Difficulty: {name} (Depth {meta['depth']})"

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background="#0B1220")
        style.configure("Card.TFrame", background="#121A28")
        style.configure("Soft.TFrame", background="#0E1623")

        style.configure("Header.TLabel", background="#0B1220", foreground="#F8FAFC", font=("Segoe UI", 25, "bold"))
        style.configure("Sub.TLabel", background="#0B1220", foreground="#8FA3B8", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#121A28", foreground="#F8FAFC", font=("Segoe UI", 12, "bold"))
        style.configure("Info.TLabel", background="#121A28", foreground="#D3DCE6", font=("Segoe UI", 10))
        style.configure("BigInfo.TLabel", background="#121A28", foreground="#EAF1F8", font=("Segoe UI", 11, "bold"))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 10), background="#5FB3FF", foreground="#08111B", borderwidth=0)
        style.map("Accent.TButton", background=[("active", "#7BC2FF")])
        style.configure("Ghost.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 10), background="#1E2A3D", foreground="#E2E8F0", borderwidth=0)
        style.map("Ghost.TButton", background=[("active", "#2A3A52")])
        style.configure("TCombobox", padding=7)
        style.configure("Eval.Horizontal.TProgressbar", troughcolor="#1B2533", background="#5FB3FF", bordercolor="#1B2533", lightcolor="#5FB3FF", darkcolor="#5FB3FF")

    def _build_layout(self):
        wrapper = ttk.Frame(self.root)
        wrapper.pack(fill="both", expand=True, padx=20, pady=18)

        self._build_header(wrapper)

        body = ttk.Frame(wrapper)
        body.pack(fill="both", expand=True)

        self._build_board_area(body)
        self._build_sidebar(body)

    def _build_header(self, parent):
        header = ttk.Frame(parent)
        header.pack(fill="x", pady=(0, 16))

        row = ttk.Frame(header)
        row.pack(fill="x")

        ttk.Label(row, text="CrownMind CzechPy", style="Header.TLabel").pack(side="left")
        tk.Label(row, text="STABLE BUILD", bg="#17324D", fg="#BFE3FF", font=("Segoe UI", 9, "bold"), padx=10, pady=4).pack(side="left", padx=(12, 0), pady=(5, 0))

    def _build_board_area(self, parent):
        left = ttk.Frame(parent)
        left.pack(side="left", fill="both", expand=False)

        shell = tk.Frame(left, bg="#182231", highlightthickness=1, highlightbackground="#29384C")
        shell.pack()

        card = ttk.Frame(shell, style="Card.TFrame", padding=14)
        card.pack()

        board_px = BOARD_SIZE * CELL_SIZE

        self.canvas = tk.Canvas(
    card,
    width=board_px,
    height=board_px,
    bg="#0F1724",
    highlightthickness=0
)
        board_px = BOARD_SIZE * CELL_SIZE

        self.canvas = tk.Canvas(
    card,
    width=board_px,
    height=board_px,
    bg="#0F1724",
    highlightthickness=0
)

        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

    def _build_sidebar(self, parent):
        right = ttk.Frame(parent)
        right.pack(side="right", fill="y", padx=(20, 0))

        sidebar = ttk.Frame(right, style="Card.TFrame", padding=18)
        sidebar.pack(fill="y", expand=True)

        self._build_live_card(sidebar)
        self._build_controls(sidebar)
        self._build_evaluation(sidebar)
        self._build_status(sidebar)
        self._build_match_info(sidebar)

    def _build_live_card(self, parent):
        live_card = ttk.Frame(parent, style="Soft.TFrame", padding=(12, 10))
        live_card.pack(fill="x", pady=(0, 14))

        self.live_dot = tk.Canvas(live_card, width=14, height=14, bg="#0E1623", highlightthickness=0, bd=0)
        self.live_dot.pack(side="left", padx=(0, 10))
        self.live_dot_oval = self.live_dot.create_oval(2, 2, 12, 12, fill="#22C55E", outline="")
        ttk.Label(live_card, textvariable=self.live_state_var, style="BigInfo.TLabel").pack(side="left")

    def _build_controls(self, parent):
        ttk.Label(parent, text="Controls", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Separator(parent).pack(fill="x", pady=10)

        ttk.Label(parent, text="Difficulty", style="Info.TLabel").pack(anchor="w")
        self.depth_combo = ttk.Combobox(parent, values=list(DIFFICULTY_LEVELS.keys()), state="readonly", textvariable=self.difficulty_var, width=14, justify="center")
        self.depth_combo.pack(anchor="w", pady=(6, 14))
        self.depth_combo.bind("<<ComboboxSelected>>", self.on_depth_change)
        self.depth_combo.set(DEFAULT_DIFFICULTY)

        btns = ttk.Frame(parent, style="Card.TFrame")
        btns.pack(fill="x", pady=(0, 12))
        ttk.Button(btns, text="New Game", style="Accent.TButton", command=self.restart_game).pack(side="left", fill="x", expand=True)
        ttk.Button(btns, text="Flip Board", style="Ghost.TButton", command=self.flip_board).pack(side="left", fill="x", expand=True, padx=(10, 0))

    def _build_evaluation(self, parent):
        ttk.Label(parent, text="Evaluation", style="CardTitle.TLabel").pack(anchor="w", pady=(10, 0))
        ttk.Separator(parent).pack(fill="x", pady=10)

        self.eval_bar = ttk.Progressbar(parent, style="Eval.Horizontal.TProgressbar", orient="horizontal", mode="determinate", length=310, maximum=100, value=50)
        self.eval_bar.pack(fill="x")
        ttk.Label(parent, textvariable=self.score_var, style="Info.TLabel").pack(anchor="w", pady=(8, 0))

    def _build_status(self, parent):
        ttk.Label(parent, text="Status", style="CardTitle.TLabel").pack(anchor="w", pady=(16, 0))
        ttk.Separator(parent).pack(fill="x", pady=10)
        ttk.Label(parent, textvariable=self.status_var, style="Info.TLabel", wraplength=310, justify="left").pack(anchor="w", fill="x")
        self.thinking_bar = ttk.Progressbar(parent, mode="indeterminate", length=310)
        self.thinking_bar.pack(fill="x", pady=(12, 0))

    def _build_match_info(self, parent):
        info = ttk.Frame(parent, style="Card.TFrame")
        info.pack(fill="x", pady=(18, 0))
        self.watermark = tk.Label(
    parent,
    text="© 2026 souror. All Rights Reserved.",
    bg="#121A28",
    fg="#FFD700",
    font=("Segoe UI", 12, "bold")
)

        self.watermark.pack(side="bottom", pady=(15, 5))

        ttk.Label(info, text="Match Info", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Label(info, textvariable=self.turn_var, style="Info.TLabel").pack(anchor="w", pady=3)
        ttk.Label(info, textvariable=self.depth_text_var, style="Info.TLabel").pack(anchor="w", pady=3)
        ttk.Label(info, textvariable=self.red_count_var, style="Info.TLabel").pack(anchor="w", pady=3)
        ttk.Label(info, textvariable=self.black_count_var, style="Info.TLabel").pack(anchor="w", pady=3)

    def get_depth(self):
        return DIFFICULTY_LEVELS.get(self.difficulty_var.get(), DIFFICULTY_LEVELS[DEFAULT_DIFFICULTY])["depth"]

    def on_depth_change(self, _event=None):
        difficulty_name = self.difficulty_var.get()
        self.depth_text_var.set(self._difficulty_label(difficulty_name))
        self.status_var.set(f"Difficulty set to {difficulty_name}.")

    def restart_game(self):
        TRANSPOSITION_TABLE.clear()
        self.board = create_board()
        self.turn = "red"
        self.selected = None
        self.valid_moves = []
        self.last_move = None
        self.ai_busy = False
        self.view_flipped = False
        self.thinking_ticks = 0
        self.status_var.set("New game started. Your turn.")
        self.score_var.set("AI eval: 0.00")
        self.eval_bar["value"] = 50
        self.live_state_var.set("READY")
        self.stop_thinking_animation()
        self.draw_board()
        self.refresh_sidebar(ai_score=0.0)

    def flip_board(self):
        self.view_flipped = not self.view_flipped
        self.selected = None
        self.valid_moves = []
        self.status_var.set("Board flipped.")
        self.draw_board()

    def view_to_board(self, view_row, view_col):
        if not self.view_flipped:
            return view_row, view_col
        return BOARD_SIZE - 1 - view_row, BOARD_SIZE - 1 - view_col

    def refresh_sidebar(self, ai_score=None):
        red_count, black_count = count_pieces(self.board)
        self.red_count_var.set(f"Red pieces: {red_count}")
        self.black_count_var.set(f"Black pieces: {black_count}")
        self.turn_var.set(f"Turn: {'Human' if self.turn == 'red' else 'AI' if self.turn == 'black' else 'Game Over'}")

        if ai_score is not None:
            self.score_var.set(f"AI eval: {ai_score:.2f}")
            self.eval_bar["value"] = score_to_bar_value(ai_score)

        if self.ai_busy:
            dots = "." * ((self.thinking_ticks % 3) + 1)
            self.live_state_var.set(f"THINKING{dots}")
        elif self.turn == "red":
            self.live_state_var.set("YOUR TURN")
        elif self.turn == "black":
            self.live_state_var.set("AI TURN")
        else:
            self.live_state_var.set("GAME OVER")

    def start_thinking_animation(self):
        try:
            self.thinking_bar.start(10)
        except Exception:
            pass
        self.live_dot.itemconfigure(self.live_dot_oval, fill="#F59E0B")

    def stop_thinking_animation(self):
        try:
            self.thinking_bar.stop()
        except Exception:
            pass
        self.live_dot.itemconfigure(self.live_dot_oval, fill="#22C55E")

    def animate_ui(self):
        if self.ai_busy and self.turn == "black":
            self.thinking_ticks += 1
            dots = "." * ((self.thinking_ticks % 3) + 1)
            self.status_var.set(f"AI is thinking{dots}")
            self.live_state_var.set(f"THINKING{dots}")
            self.start_thinking_animation()
        else:
            self.stop_thinking_animation()
        self.root.after(250, self.animate_ui)

    def draw_board(self):
        self.canvas.delete("all")
        colors = {
            "bg": "#0F1724",
            "light": "#E7D7BD",
            "dark": "#8B5E3C",
            "grid": "#233244",
            "coord": "#AAB8C8",
            "selected": "#FBBF24",
            "valid": "#22C55E",
            "last_start": "#60A5FA",
            "last_end": "#34D399",
            "movable": "#A78BFA",
        }

        human_movable = legal_starts(self.board, "red") if self.turn == "red" else set()

        self.canvas.create_rectangle(0, 0, BOARD_SIZE * CELL_SIZE, BOARD_SIZE * CELL_SIZE, fill=colors["bg"], outline="#263547", width=2)

        for i in range(BOARD_SIZE):
            label = str(i if not self.view_flipped else BOARD_SIZE - 1 - i)
            self.canvas.create_text(i * CELL_SIZE + CELL_SIZE / 2, 14, text=label, fill=colors["coord"], font=("Segoe UI", 9, "bold"))
            self.canvas.create_text(14, i * CELL_SIZE + CELL_SIZE / 2, text=label, fill=colors["coord"], font=("Segoe UI", 9, "bold"))

        for view_row in range(BOARD_SIZE):
            for view_col in range(BOARD_SIZE):
                board_row, board_col = self.view_to_board(view_row, view_col)
                x1 = view_col * CELL_SIZE
                y1 = view_row * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE

                square_color = colors["light"] if (board_row + board_col) % 2 == 0 else colors["dark"]
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=square_color, outline=colors["grid"], width=1)
                self._draw_move_overlays(board_row, board_col, x1, y1, x2, y2, colors)
                self._draw_piece(board_row, board_col, x1, y1, x2, y2, colors, human_movable)

    def _draw_move_overlays(self, row, col, x1, y1, x2, y2, colors):
        if self.last_move:
            start = self.last_move["start"]
            end = move_end(self.last_move)
            if (row, col) == start:
                self.canvas.create_rectangle(x1 + 5, y1 + 5, x2 - 5, y2 - 5, outline=colors["last_start"], width=3)
            if (row, col) == end:
                self.canvas.create_rectangle(x1 + 5, y1 + 5, x2 - 5, y2 - 5, outline=colors["last_end"], width=3)

        if self.selected == (row, col):
            self.canvas.create_rectangle(x1 + 3, y1 + 3, x2 - 3, y2 - 3, outline=colors["selected"], width=4)

        if any(move_end(move) == (row, col) for move in self.valid_moves):
            self.canvas.create_oval(x1 + CELL_SIZE * 0.39, y1 + CELL_SIZE * 0.39, x1 + CELL_SIZE * 0.61, y1 + CELL_SIZE * 0.61, fill=colors["valid"], outline="")

        if self.last_move and (row, col) in self.last_move.get("captured", []):
            self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text="×", fill="#FACC15", font=("Segoe UI", 24, "bold"))

    def _draw_piece(self, row, col, x1, y1, x2, y2, colors, human_movable):
        piece = self.board[row][col]
        if piece == EMPTY:
            return

        red_piece = is_red(piece)
        fill = "#E5484D" if red_piece else "#1C2433"
        rim = "#8A1F2A" if red_piece else "#0E1725"
        inner = "#FFCCCC" if red_piece else "#C7DCF8"

        self.canvas.create_oval(x1 + 13, y1 + 14, x2 - 9, y2 - 6, fill="#000000", outline="", stipple="gray50")
        self.canvas.create_oval(x1 + 10, y1 + 10, x2 - 10, y2 - 10, fill=fill, outline=rim, width=3)
        self.canvas.create_oval(x1 + 19, y1 + 18, x2 - 19, y2 - 23, outline=inner, width=2)

        if self.turn == "red" and (row, col) in human_movable:
            self.canvas.create_oval(x1 + 6, y1 + 6, x2 - 6, y2 - 6, outline=colors["movable"], width=2)

        if is_king(piece):
            self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2 + 1, text="♛", fill="white", font=("Segoe UI Symbol", 19, "bold"))

    def on_click(self, event):
        if self.turn != "red" or self.ai_busy:
            return

        view_row = event.y // CELL_SIZE
        view_col = event.x // CELL_SIZE
        if not inside(view_row, view_col):
            return

        row, col = self.view_to_board(view_row, view_col)
        piece = self.board[row][col]

        all_red_moves = get_all_moves(self.board, "red")
        movable = {move["start"] for move in all_red_moves}
        has_capture = any(move["captured"] for move in all_red_moves)

        if self.selected is None:
            self._handle_first_click(row, col, piece, all_red_moves, movable, has_capture)
            return

        chosen_move = None
        for move in self.valid_moves:
            if move_end(move) == (row, col):
                chosen_move = move
                break

        if chosen_move is None:
            self._handle_invalid_second_click(row, col, piece, all_red_moves, movable)
            return

        self._perform_human_move(chosen_move)

    def _handle_first_click(self, row, col, piece, all_red_moves, movable, has_capture):
        if not is_red(piece):
            return

        if (row, col) not in movable:
            self.status_var.set("Mandatory capture available with another piece." if has_capture else "That piece has no legal move.")
            return

        self.selected = (row, col)
        self.valid_moves = [move for move in all_red_moves if move["start"] == (row, col)]
        self.status_var.set("Capture available. Choose a highlighted square." if any(m["captured"] for m in self.valid_moves) else "Choose a highlighted square.")
        self.draw_board()

    def _handle_invalid_second_click(self, row, col, piece, all_red_moves, movable):
        if is_red(piece) and (row, col) in movable:
            self.selected = (row, col)
            self.valid_moves = [move for move in all_red_moves if move["start"] == (row, col)]
            self.status_var.set("Piece changed. Choose a highlighted square.")
        else:
            self.selected = None
            self.valid_moves = []
            self.status_var.set("Invalid move. Select a valid glowing piece.")
        self.draw_board()

    def _perform_human_move(self, move):
        self.board = apply_move(self.board, move)
        self.last_move = move
        self.selected = None
        self.valid_moves = []
        self.draw_board()
        self.refresh_sidebar()

        winner = get_winner(self.board)
        if winner is not None:
            self._finish_by_result(winner)
            return

        self.turn = "black"
        self.ai_busy = True
        self.thinking_ticks = 0
        self.status_var.set("AI is thinking...")
        self.refresh_sidebar()
        self.root.after(90, self.ai_turn)

    def ai_turn(self):
        if self.turn != "black":
            self.ai_busy = False
            return

        depth = self.get_depth()
        difficulty = self.difficulty_var.get()
        board_snapshot = copy.deepcopy(self.board)

        TRANSPOSITION_TABLE.clear()
        scored_moves = alpha_beta_root_moves(board_snapshot, depth)
        if not scored_moves:
            score, move = evaluate(board_snapshot), None
        else:
            score, move = choose_move_by_difficulty(scored_moves, difficulty)

        self._apply_ai_result(score, move)

    def _apply_ai_result(self, score, move):
        self.score_var.set(f"AI eval: {score:.2f}")
        self.eval_bar["value"] = score_to_bar_value(score)

        if move is None:
            self.ai_busy = False
            self.stop_thinking_animation()
            winner = get_winner(self.board)
            self._finish_by_result(winner if winner is not None else "red")
            return

        self.board = apply_move(self.board, move)
        self.last_move = move
        self.draw_board()
        self.refresh_sidebar(ai_score=score)

        winner = get_winner(self.board)
        if winner is not None:
            self.ai_busy = False
            self.stop_thinking_animation()
            self._finish_by_result(winner)
            return

        self.turn = "red"
        self.ai_busy = False
        self.stop_thinking_animation()
        self.status_var.set("Your turn.")
        self.refresh_sidebar(ai_score=score)

    def _finish_by_result(self, result):
        if result == "red":
            self.end_game("You win!")
        elif result == "black":
            self.end_game("AI wins!")
        else:
            self.end_game("Draw!")

    def show_game_over_dialog(self, text):
        dialog = tk.Toplevel(self.root)
        dialog.title("Game Over")
        dialog.geometry("460x260")
        dialog.configure(bg="#0B1220")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        def close_and_release():
            try:
                dialog.grab_release()
            except Exception:
                pass
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", close_and_release)

        card = tk.Frame(dialog, bg="#121A28", highlightthickness=1, highlightbackground="#263548")
        card.place(relx=0.5, rely=0.5, anchor="center", width=400, height=210)

        tk.Label(card, text="Game Over", bg="#121A28", fg="#F8FAFC", font=("Segoe UI", 20, "bold")).pack(pady=(24, 10))
        tk.Label(card, text=text, bg="#121A28", fg="#CFD8E3", font=("Segoe UI", 11), wraplength=320, justify="center").pack(pady=(0, 18))

        row = tk.Frame(card, bg="#121A28")
        row.pack()

        tk.Button(
            row,
            text="New Game",
            command=lambda: [close_and_release(), self.restart_game()],
            font=("Segoe UI", 10, "bold"),
            bg="#5FB3FF",
            fg="#08111B",
            activebackground="#7BC2FF",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
        ).pack(side="left", padx=8)

        tk.Button(
            row,
            text="Close",
            command=close_and_release,
            font=("Segoe UI", 10, "bold"),
            bg="#223044",
            fg="#E6EDF5",
            activebackground="#2C415B",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
        ).pack(side="left", padx=8)

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 230
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 140
        dialog.geometry(f"460x260+{x}+{y}")

    def end_game(self, text):
        self.turn = "game_over"
        self.ai_busy = False
        self.selected = None
        self.valid_moves = []
        self.stop_thinking_animation()
        self.status_var.set(text)
        self.refresh_sidebar()
        self.draw_board()
        self.show_game_over_dialog(text)


# =================================================
# Tests
# =================================================
def run_basic_tests():
    board = create_board()
    assert len(get_all_moves(board, "red")) > 0
    assert len(get_all_moves(board, "black")) > 0

    for name in DIFFICULTY_LEVELS:
        assert "depth" in DIFFICULTY_LEVELS[name]
        assert "mix" in DIFFICULTY_LEVELS[name]

    score, move = alpha_beta(board, 2, -math.inf, math.inf, True)
    assert isinstance(score, (int, float))
    assert move is None or isinstance(move, dict)

    empty = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    score2, move2 = alpha_beta(empty, 2, -math.inf, math.inf, True)
    assert isinstance(score2, (int, float))
    assert move2 is None

    blocked = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    blocked[7][0] = BLACK
    blocked[6][1] = RED
    assert get_winner(blocked) == "red"

    blocked2 = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    blocked2[0][1] = RED
    blocked2[1][0] = BLACK
    blocked2[1][2] = BLACK
    assert get_winner(blocked2) == "black"


if __name__ == "__main__":
    run_basic_tests()
    root = tk.Tk()
    app = CheckersGUI(root)
    root.mainloop()
