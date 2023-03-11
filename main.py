import time
import tkinter as tk
from tkinter import messagebox
import random
from typing import Callable, Any
from ctypes import windll


class Field:
    empty_cell, cross, circle = range(3)
    cross_win, circle_win, draw, active = range(4)

    def __init__(self) -> None:
        self.field: list[list[int]] = [[Field.empty_cell for x in range(3)] for y in range(3)]

    def put_char(self, row_idx: int, col_idx: int, cross_if_true: bool) -> bool:  # True if placed False otherwise
        # Don't do anything if there's a thing placed here already
        if self.field[row_idx][col_idx] != Field.empty_cell:
            return False

        # Add it to the field array
        self.field[row_idx][col_idx] = Field.cross if cross_if_true else Field.circle

        return True

    def check_state(self) -> int:
        field = self.field

        # Since field stores cells as integers, we will concat lines into 3-digit lines
        crosses_check = int(str(Field.cross) * 3)
        circles_check = int(str(Field.circle) * 3)

        lines = [
            field[0][0] * 100 + field[0][1] * 10 + field[0][2],
            field[1][0] * 100 + field[1][1] * 10 + field[1][2],
            field[2][0] * 100 + field[2][1] * 10 + field[2][2],

            field[0][0] * 100 + field[1][0] * 10 + field[2][0],
            field[0][1] * 100 + field[1][1] * 10 + field[2][1],
            field[0][2] * 100 + field[1][2] * 10 + field[2][2],

            field[0][0] * 100 + field[1][1] * 10 + field[2][2],
            field[0][2] * 100 + field[1][1] * 10 + field[2][0]
        ]

        # Check new game state
        if crosses_check in lines:
            return Field.cross_win
        elif circles_check in lines:
            return Field.circle_win
        # If we ran out of black spaces, a tie happened
        if not (0 in field[0] or 0 in field[1] or 0 in field[2]):
            return Field.draw

        # Or it's just still active lmao
        return Field.active

    # Test comment. No funny little humor text because HNGNNGHGHHHH GIT IS HARD
    def reset(self) -> None:
        self.field = [[Field.empty_cell for x in range(3)] for y in range(3)]

    def copy(self) -> "Field":
        new_field = Field()
        new_field.field = [[self.field[y][x] for x in range(3)] for y in range(3)]
        return new_field

    def all_futures(self) -> list["Field"]:
        # Determine who moves next
        x_count = sum(row.count(Field.cross) for row in self.field)
        o_count = sum(row.count(Field.circle) for row in self.field)

        if x_count == o_count + 1:
            turn = Field.circle
        else:
            turn = Field.cross

        # Generate a list of all future boards (as in the next move)
        futures = []
        for y, x in self.available_moves():
            future = self.copy()
            future.field[y][x] = turn
            futures.append(future)
        return futures

    def debug_print(self) -> None:
        for y in range(3):
            for x in range(3):
                if self.field[y][x] == Field.empty_cell:
                    print('.', end='')
                elif self.field[y][x] == Field.cross:
                    print('X', end='')
                elif self.field[y][x] == Field.circle:
                    print('O', end='')
            print()

    def available_moves(self) -> list[tuple[int, int]]:
        return [(y, x) for y in range(3) for x in range(3) if self.field[y][x] == Field.empty_cell]


class Bot:
    def __init__(self, true_if_first: bool):
        self.next_move: tuple[int, int] = 1, 1
        self.true_if_first: bool = true_if_first

    def gen_move(self, field: Field, turn_counter: int, depth: int = 0) -> int:
        # Minimax algorithm
        if field.check_state() != Field.active:
            return self.score_game(field)

        # Optimisation
        if turn_counter == int(not self.true_if_first):
            if field.field[1][1] == Field.empty_cell:
                self.next_move = (1, 1)
            else:
                self.next_move = random.choice([(0, 0), (2, 0), (0, 2), (2, 2)])
            return 0

        futures = field.all_futures()
        scores = [self.gen_move(future, turn_counter + 1, depth=depth + 1) for future in futures]

        if depth % 2 == 1:
            return min(scores)
        elif depth > 0:
            return max(scores)
        else:
            move_idx = random.choice([idx for idx, score in enumerate(scores) if score == max(scores)])
            t = field.available_moves()[move_idx]
            self.next_move = t
            return 0

    def make_move(self, field: Field, turn_counter: int) -> tuple[int, int]:
        self.gen_move(field, turn_counter)
        return self.next_move

    def score_game(self, field):
        state = field.check_state()

        if state == Field.cross_win:
            return 10 if self.true_if_first else -10
        elif state == Field.circle_win:
            return -10 if self.true_if_first else 10
        elif state == Field.draw:
            return 0


class SuperButton(tk.Label):
    bg = "#000"
    fg = "#FFF"

    active_bg = "#FFF"
    active_fg = "#000"

    def __init__(self, master: tk.Frame, text: str, command: Callable[[], Any]):
        super().__init__(master, text=text, bg=self.bg, fg=self.fg, font=("Consolas", 18))
        self.bind("<ButtonRelease-1>", lambda ev: command())
        self.bind("<Enter>", lambda ev: self.on_hover(ev))
        self.bind("<Leave>", lambda ev: self.on_leave(ev))

    def on_hover(self, event: tk.Event):
        self.configure(bg=self.active_bg, fg=self.active_fg)

    def on_leave(self, event: tk.Event):
        self.configure(bg=self.bg, fg=self.fg)


class Main:
    menu_state, local_state, bot_select_state, bot_state, boss_state, help_state = range(6)

    player_first, bot_first, random = range(3)

    char_size = 100
    offset = 8
    line_width = 12
    cell_size = char_size + offset + line_width
    canvas_size = line_width * 2 + char_size * 3 + offset * 6

    help_string = ("This is an implementation of Tic Tac Toe in tkinter.\n"
                   "The rules are simple:\n\n"
                   "On 3x3 grid you can play as an X or O, \n"
                   "depending on whether you move first or your opponent does.\n"
                   "You and your opponent place corresponding characters in turns, \n"
                   "whoever gets 3 of their characters in a row (row, column, or diagonal) first wins.\n"
                   "If the grid is completely filled but no one won, the game ends in a tie.\n\n"
                   "Have fun!")

    def __init__(self, master):
        self.master: tk.Tk = master
        self.state: int = Main.menu_state  # state variable that determines current menu state

        # Game data
        self.field: Field = Field()
        self.turn_counter: int = 0
        self.vs_bot: bool = False
        self.player_first: bool = True
        self.game_start_time: float = time.perf_counter()
        self.bot: Bot = Bot(False)

        self.cross_img: tk.PhotoImage = tk.PhotoImage(file="cross.png")
        self.circle_img: tk.PhotoImage = tk.PhotoImage(file="circle.png")
        self.vert_img: tk.PhotoImage = tk.PhotoImage(file="vert.png")
        self.horiz_img: tk.PhotoImage = tk.PhotoImage(file="horiz.png")

        # Main menu UI
        main_menu_frame = tk.Frame(master, bg="black")

        title_frame = tk.Frame(main_menu_frame)
        title_label_1 = tk.Label(title_frame, text="TIC ", font=("Comic Sans MS", 45), bg="black", fg="#ED1C24")
        title_label_2 = tk.Label(title_frame, text="TAC ", font=("Comic Sans MS", 45), bg="black", fg="#00A3E8")
        title_label_3 = tk.Label(title_frame, text="TOE", font=("Comic Sans MS", 45), bg="black", fg="#FFF200")

        buttons_frame = tk.Frame(main_menu_frame)

        solo_play_btn = SuperButton(buttons_frame, "Play local", lambda: self.move_to(Main.local_state))
        bot_play_btn = SuperButton(buttons_frame, "Play vs Bot", lambda: self.move_to(Main.bot_select_state))
        help_btn = SuperButton(buttons_frame, "Help", lambda: self.move_to(Main.help_state))
        boss_btn = SuperButton(buttons_frame, "???", lambda: messagebox.showinfo("Leave now", "You are not worthy"))
        quit_btn = SuperButton(buttons_frame, "Quit", master.quit)

        title_label_1.grid(column=0, row=0)
        title_label_2.grid(column=1, row=0)
        title_label_3.grid(column=2, row=0)
        title_frame.pack()
        # ps_label.pack()
        solo_play_btn.grid(row=0, sticky="ew")
        bot_play_btn.grid(row=1, sticky="ew")
        help_btn.grid(row=2, sticky="ew")
        boss_btn.grid(row=3, sticky="ew")
        quit_btn.grid(row=4, sticky="ew")
        buttons_frame.pack()

        main_menu_frame.pack()
        self.main_menu_frame: tk.Frame = main_menu_frame

        # Bot options select UI
        bot_select_frame = tk.Frame(master)

        desc_label = tk.Label(bot_select_frame, text="Choose who moves the first:")

        self.player_first_var: tk.IntVar = tk.IntVar(value=True)
        player_btn = tk.Radiobutton(bot_select_frame, text="Player", variable=self.player_first_var,
                                    value=Main.player_first)
        bot_btn = tk.Radiobutton(bot_select_frame, text="Bot", variable=self.player_first_var, value=Main.bot_first)
        random_btn = tk.Radiobutton(bot_select_frame, text="Random", variable=self.player_first_var, value=Main.random)
        start_btn = tk.Button(bot_select_frame, text="Start the game!", command=lambda: self.move_to(Main.bot_state))

        desc_label.grid(row=0)
        player_btn.grid(row=1)
        bot_btn.grid(row=2)
        random_btn.grid(row=3)
        start_btn.grid(row=4)

        self.bot_select_frame: tk.Frame = bot_select_frame
        # Game UI
        game_frame = tk.Frame(master)
        canvas = tk.Canvas(game_frame, width=self.canvas_size, height=self.canvas_size, bg="white")
        canvas.bind("<Button-1>", lambda event: self.make_move(event.y, event.x, self.vs_bot))
        canvas.pack()

        self.canvas: tk.Canvas = canvas
        self.game_frame: tk.Frame = game_frame

        # Help UI
        help_frame = tk.Frame(master)

        help_label = tk.Label(help_frame, text=Main.help_string, font=("Consolas", 12), justify="left")
        back_btn = tk.Button(help_frame, text="Go back", command=lambda: self.move_to(Main.menu_state))
        help_label.pack()
        back_btn.pack()

        self.help_frame: tk.Frame = help_frame

    def move_to(self, new_state: int) -> None:
        self.state = new_state
        self.main_menu_frame.pack_forget()
        self.game_frame.pack_forget()
        self.bot_select_frame.pack_forget()
        self.help_frame.pack_forget()

        if new_state == Main.menu_state:
            self.main_menu_frame.pack()
        elif new_state == Main.local_state:
            self.vs_bot = False
            self.game_frame.pack()
            self.init_game()
        elif new_state == Main.bot_select_state:
            self.bot_select_frame.pack()
        elif new_state == Main.bot_state:
            self.vs_bot = True
            self.game_frame.pack()
            self.init_game()
        elif new_state == Main.help_state:
            self.help_frame.pack()

    def make_move(self, mouse_y: int, mouse_x: int, vs_bot: bool) -> None:
        # Determine where did we click and put a character in the field
        char_size, offset, line_width, cell_size = Main.char_size, Main.offset, Main.line_width, Main.cell_size
        col_idx, row_idx = min(mouse_x // cell_size, 2), min(mouse_y // cell_size, 2)

        # If we can't place there, don't do anything
        if not self.field.put_char(row_idx, col_idx, self.turn_counter % 2 == 0):
            return

        # Draw it, basically
        x = col_idx * (cell_size + offset) + offset
        y = row_idx * (cell_size + offset) + offset

        img = self.cross_img if self.turn_counter % 2 == 0 else self.circle_img
        self.canvas.create_image(x + char_size / 2, y + char_size / 2, image=img)

        # Update the turn counter
        self.turn_counter += 1

        # Check if anyone won or draw happened
        game_ended = self.check_game()

        # Bot move
        if not game_ended and vs_bot and self.turn_counter % 2 == self.player_first:
            y, x = self.bot.make_move(self.field, self.turn_counter)
            self.make_move(cell_size * y, cell_size * x, vs_bot)

    def init_game(self) -> None:
        # Decide who moves first
        if self.player_first_var.get() == Main.player_first:
            self.player_first = True
            self.bot.true_if_first = False
        elif self.player_first_var.get() == Main.bot_first:
            self.player_first = False
            self.bot.true_if_first = True
        elif self.player_first_var.get() == Main.random:
            self.player_first = bool(random.randint(0, 1))
            self.bot.true_if_first = not self.player_first

        # Time the game
        self.game_start_time = time.perf_counter()

        # Draw the grid
        char_size, offset, line_width, canvas_size = Main.char_size, Main.offset, Main.line_width, Main.canvas_size
        half_width = line_width // 2
        self.canvas.create_image(char_size + offset * 2 + half_width, self.canvas_size / 2, image=self.vert_img)
        self.canvas.create_image(char_size * 2 + offset * 4 + half_width * 3, self.canvas_size / 2, image=self.vert_img)
        self.canvas.create_image(self.canvas_size / 2, char_size + offset * 2 + half_width, image=self.horiz_img)
        self.canvas.create_image(self.canvas_size / 2, char_size * 2 + offset * 4 + half_width * 3,
                                 image=self.horiz_img)

        # Make a move if the bot moves first
        if not self.player_first and self.vs_bot:
            y, x = self.bot.make_move(self.field, self.turn_counter)
            self.make_move(Main.cell_size * y, Main.cell_size * x, True)
            self.turn_counter = 1

    def reset_game(self) -> None:
        self.turn_counter = 0
        self.canvas.delete("all")
        self.field.reset()

    def check_game(self) -> bool:  # Returns true if game ended, false otherwise
        # Get the field's state
        result = self.field.check_state()
        if result == Field.cross_win:
            game_over_message = "Crosses won!"
        elif result == Field.circle_win:
            game_over_message = "Circles won!"
        elif result == Field.draw:
            game_over_message = "Draw!"
        else:
            return False

        # Announce it and redirect to main menu
        game_over_message = f"{game_over_message} Game ended in {time.perf_counter() - self.game_start_time:.2f}s!"
        messagebox.showinfo("Game Over", game_over_message)
        self.reset_game()
        self.move_to(Main.menu_state)

        return True


# Fix blurry text
windll.shcore.SetProcessDpiAwareness(1)

# Run the app
root = tk.Tk()
root.resizable(False, False)
root.title("Tic Tac Toe")
app = Main(root)
root.mainloop()
