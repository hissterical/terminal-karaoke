import curses
import os
import time

class UI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.visible_lines = 7
        self.progress_bar_width = 50
        self.dancing_cat_frames = self.create_dancing_cat_frames()
        self.cat_frame_idx = 0
        self.last_cat_update = time.time()
        self.cat_update_interval = 0.15
        self.setup_colors()

    def setup_colors(self):
        curses.start_color()
        curses.use_default_colors()
        try:
            curses.init_pair(1, curses.COLOR_CYAN, -1)
            curses.init_pair(2, curses.COLOR_YELLOW, -1)
            curses.init_pair(3, curses.COLOR_GREEN, -1)
            curses.init_pair(4, curses.COLOR_RED, -1)
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)
            curses.init_pair(6, 8, -1)
            curses.init_pair(7, curses.COLOR_WHITE, -1)
        except:
            curses.init_pair(1, curses.COLOR_CYAN, -1)
            curses.init_pair(2, curses.COLOR_YELLOW, -1)
            curses.init_pair(3, curses.COLOR_GREEN, -1)
            curses.init_pair(4, curses.COLOR_RED, -1)
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)
            curses.init_pair(6, curses.COLOR_BLACK, -1)
            curses.init_pair(7, curses.COLOR_WHITE, -1)

    def create_dancing_cat_frames(self):
        frames = [
            [
                "  /\\_/\\  ",
                " ( o.o ) ",
                "  > ^ <  "
            ],
            [
                "  /\\_/\\  ",
                " ( o.o ) ",
                "   ^_^   "
            ],
            [
                "  /\\_/\\  ",
                " ( -.- ) ",
                "  > ^ <  "
            ],
            [
                "  /\\_/\\  ",
                " ( -.- ) ",
                "   ^_^   "
            ],
            [
                "  /\\_/\\  ",
                " ( o.o ) ",
                "  \\_^_/  "
            ],
            [
                "  /\\_/\\  ",
                " ( '.o ) ",
                "  > ^ <  "
            ]
        ]
        formatted_frames = []
        for frame in frames:
            max_len = max(len(line) for line in frame)
            padded_frame = [line.center(max_len) for line in frame]
            formatted_frames.append("\n".join(padded_frame))
        return formatted_frames

    def update_animation(self, current_time):
        if current_time - self.last_cat_update > self.cat_update_interval:
            self.cat_frame_idx = (self.cat_frame_idx + 1) % len(self.dancing_cat_frames)
            self.last_cat_update = current_time

    def get_visible_lines(self, player):
        if not player.lyrics:
            return [], 0, 0
        start_idx = max(0, player.current_line_idx - (self.visible_lines // 2))
        end_idx = min(len(player.lyrics), start_idx + self.visible_lines)
        if end_idx - start_idx < self.visible_lines and start_idx > 0:
            start_idx = max(0, end_idx - self.visible_lines)
        visible = player.lyrics[start_idx:end_idx]
        current_visible_idx = player.current_line_idx - start_idx
        return visible, start_idx, current_visible_idx

    def draw_progress_bar(self, y, x, width, current_time, total_time):
        progress = min(1.0, max(0.0, current_time / total_time)) if total_time > 0 else 0
        filled = int(width * progress)
        bar = "█" * filled + "░" * (width - filled)
        self.stdscr.addstr(y, x, f"[{bar}]", curses.color_pair(3))
        
        time_text = f"{self.format_time(current_time)}/{self.format_time(total_time)}"
        time_y = y - 1
        time_x = x + (width // 2) - (len(time_text) // 2)
        if time_y > 0:
            self.stdscr.addstr(time_y, time_x, time_text, curses.color_pair(7))

    def format_time(self, seconds):
        if seconds is None:
            return "00:00"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def draw_current_line_progress(self, line_text, y, x, current_time, current_line_time, next_line_time):
        if not line_text:
            return
        line_duration = next_line_time - current_line_time
        if line_duration <= 0:
            line_progress = 1.0
        else:
            line_progress = min(1.0, max(0.0, (current_time - current_line_time) / line_duration))
        num_colored = int(len(line_text) * line_progress)
        colored_text = line_text[:num_colored]
        remaining_text = line_text[num_colored:]
        self.stdscr.addstr(y, x, colored_text, curses.color_pair(2))
        self.stdscr.addstr(remaining_text, curses.color_pair(6))

    def draw(self, player):
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Get current time once for consistency
        current_time = player.current_time()
        
        title = " TERMINAL KARAOKE "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(0, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
        if player.song_path:
            song_name = os.path.basename(player.song_path)
            self.stdscr.addstr(1, 2, f"Song: {song_name}", curses.color_pair(7))
        
        if time.time() < player.status_timer and player.status_message:
            status_x = (width - len(player.status_message)) // 2
            self.stdscr.addstr(2, status_x, player.status_message, curses.color_pair(4))
        
        if player.lyrics:
            visible_lines, start_idx, current_visible_idx = self.get_visible_lines(player)
            lyrics_start_y = (height - len(visible_lines)) // 2
            
            for i, (timestamp, line) in enumerate(visible_lines[:current_visible_idx]):
                y = lyrics_start_y + i
                if 0 < y < height - 5:
                    x = (width - len(line)) // 2
                    self.stdscr.addstr(y, x, line, curses.color_pair(6))
            
            if current_visible_idx < len(visible_lines):
                _, current_line = visible_lines[current_visible_idx]
                y = lyrics_start_y + current_visible_idx
                if 0 < y < height - 5:
                    x = (width - len(current_line)) // 2
                    # Calculate line progress
                    current_line_time = player.lyrics[player.current_line_idx][0]
                    next_line_time = (
                        player.lyrics[player.current_line_idx + 1][0] 
                        if player.current_line_idx < len(player.lyrics) - 1 
                        else player.total_time
                    )
                    self.draw_current_line_progress(
                        current_line, y, x, 
                        current_time, current_line_time, next_line_time
                    )
            
            for i, (timestamp, line) in enumerate(visible_lines[current_visible_idx+1:]):
                y = lyrics_start_y + current_visible_idx + 1 + i
                if 0 < y < height - 5:
                    x = (width - len(line)) // 2
                    self.stdscr.addstr(y, x, line, curses.color_pair(6))
            
            cat_y = lyrics_start_y - 4
            cat_frame = self.dancing_cat_frames[self.cat_frame_idx]
            cat_lines = cat_frame.split('\n')
            for i, line in enumerate(cat_lines):
                if 0 < cat_y + i < height - 5:
                    cat_x = (width - max(len(l) for l in cat_lines)) // 2
                    self.stdscr.addstr(cat_y + i, cat_x, line, curses.color_pair(5))
        else:
            msg = "Load .mp3 and .lrc files to start"
            x = (width - len(msg)) // 2
            self.stdscr.addstr(height//2, x, msg, curses.color_pair(6))
        
        if player.total_time > 0:
            bar_y = height - 3
            bar_x = (width - self.progress_bar_width) // 2
            self.draw_progress_bar(bar_y, bar_x, self.progress_bar_width, current_time, player.total_time)
        
        controls = " | ".join([f"<{k}> {v}" for k, v in player.controls.items()])
        controls_x = (width - len(controls)) // 2
        self.stdscr.addstr(height - 1, controls_x, controls, curses.color_pair(5))
        
        self.stdscr.refresh()

    def get_input(self, y, x):
        user_input = ""
        while True:
            self.stdscr.addstr(y, x, " " * 30)
            self.stdscr.addstr(y, x, user_input + "_", curses.color_pair(2))
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key == 10:
                break
            elif key in [127, 8, 263]:  # Backspace
                user_input = user_input[:-1]
            elif 32 <= key <= 126:
                user_input += chr(key)
        return user_input

    def show_file_loader(self, player):
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        title = " LOAD SONG AND LYRICS "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(2, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
        instructions = [
            "Enter paths to your .mp3 and .lrc files",
            "Press ENTER after each path",
            "",
            "Song file (.mp3): ",
            "Lyrics file (.lrc): "
        ]
        for i, text in enumerate(instructions):
            y = 5 + i
            x = (width - len(text)) // 2
            if y < height - 2:
                self.stdscr.addstr(y, x, text, curses.color_pair(7))
        
        song_path = self.get_input(8, (width//2) - 10)
        lrc_path = self.get_input(9, (width//2) - 10)
        
        if player.load_song(song_path, lrc_path):
            player.seek_to(0.0)
            player.set_status("Now playing!", 2)
        return True