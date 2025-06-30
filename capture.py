import time
import datetime
import yaml
import os
import curses


class TimeTracker:
    def __init__(self, filename="tasks.yaml"):
        self.filename = filename
        self.current_task_info = {
            "type": "",
            "tag": "",
            "name": ""
        }
        self.is_stopwatch_running = False
        self.stopwatch_start_time = None
        self.last_saved_duration = None
        self.stdscr = None

        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                yaml.dump([], f)

    def _load_tasks(self):
        try:
            with open(self.filename, 'r') as f:
                return yaml.safe_load(f) or []
        except FileNotFoundError:
            return []
        except yaml.YAMLError as e:
            self._display_message(f"Error loading YAML: {
                                  e}. Starting empty.", line=0)
            return []

    def _save_tasks(self, tasks):
        try:
            with open(self.filename, 'w') as f:
                yaml.dump(tasks, f, default_flow_style=False)
        except Exception as e:
            self._display_message(f"Error saving tasks: {e}", line=0)

    def display_status(self):
        if not self.stdscr:
            return

        self.stdscr.erase()

        h, w = self.stdscr.getmaxyx()

        self.stdscr.addstr(0, 0, "--- Time Tracker ---")

        self.stdscr.addstr(2, 0, f"Current Task: Type: {
                           self.current_task_info['type'] or 'N/A'}")
        self.stdscr.addstr(3, 0, f"              Tag:  {
                           self.current_task_info['tag'] or 'N/A'}")
        self.stdscr.addstr(4, 0, f"              Name: {
                           self.current_task_info['name'] or 'N/A'}")

        if self.is_stopwatch_running:
            elapsed_time = 0
            if self.stopwatch_start_time is not None:
                elapsed_time = time.time() - self.stopwatch_start_time
            self.stdscr.addstr(6, 0, f"Stopwatch: RUNNING ({
                               datetime.timedelta(seconds=int(elapsed_time))})")
        else:
            status_text = "STOPPED"
            if self.last_saved_duration is not None:
                status_text += f" (Last task: {datetime.timedelta(
                    seconds=int(self.last_saved_duration))})"
            self.stdscr.addstr(6, 0, f"Stopwatch: {status_text}")

        self.stdscr.addstr(8, 0, "--------------------")

        self.stdscr.addstr(
            9, 0, "Commands: i (input task), s (start/stop stopwatch), a (add manual), q (quit)")
        self.stdscr.addstr(
            10, 0, "(Type a command key directly, no Enter needed)")

        # Clear message/input area, leaving space for the command prompt at the bottom
        for r in range(12, h - 1):
            self.stdscr.move(r, 0)
            self.stdscr.clrtoeol()

        self.stdscr.addstr(h - 1, 0, "Enter command: ")

        self.stdscr.refresh()

    def _display_message(self, message, line=0):
        h, w = self.stdscr.getmaxyx()
        message_line = 12 + line

        if message_line >= h - 1:
            message_line = h - 2

        self.stdscr.move(message_line, 0)
        self.stdscr.clrtoeol()
        self.stdscr.addstr(message_line, 0, message[:w-1])
        self.stdscr.refresh()

    def _get_curses_input(self, prompt_line, prompt_col, prompt_text=""):
        self.stdscr.move(prompt_line, prompt_col)
        self.stdscr.clrtoeol()
        self.stdscr.addstr(prompt_line, prompt_col, prompt_text)
        self.stdscr.refresh()

        input_str = []
        curses.echo()
        curses.curs_set(1)

        current_col = prompt_col + len(prompt_text)
        self.stdscr.move(prompt_line, current_col)

        while True:
            char_code = self.stdscr.getch()
            if char_code == curses.KEY_ENTER or char_code in [10, 13]:
                break
            elif char_code == curses.KEY_BACKSPACE or char_code == 127:
                if input_str:
                    input_str.pop()
                    current_col -= 1
                    self.stdscr.delch(prompt_line, current_col)
            elif 32 <= char_code <= 126:
                input_str.append(chr(char_code))
                self.stdscr.addch(prompt_line, current_col, char_code)
                current_col += 1
            self.stdscr.refresh()

        curses.noecho()
        curses.curs_set(0)
        return "".join(input_str)

    def input_task(self):
        if self.is_stopwatch_running:
            self._display_message(
                "Cannot input new task while stopwatch is running. Stop it (s).")
            return

        h, w = self.stdscr.getmaxyx()
        start_line = 12

        self._display_message("Enter task details (press Enter after each):")
        self.current_task_info["type"] = self._get_curses_input(
            start_line + 1, 0, "Task Type: ").strip()
        self.current_task_info["tag"] = self._get_curses_input(
            start_line + 2, 0, "Task Tag: ").strip()
        self.current_task_info["name"] = self._get_curses_input(
            start_line + 3, 0, "Task Name: ").strip()

        if not self._is_task_info_valid():
            self._display_message(
                "Warning: Task fields empty. Fill for better tracking.", line=4)
        else:
            self._display_message("Task info updated.", line=4)

        for i in range(5):
            self.stdscr.move(start_line + i, 0)
            self.stdscr.clrtoeol()
        self.stdscr.refresh()

    def _is_task_info_valid(self):
        return bool(self.current_task_info["type"] or self.current_task_info["tag"] or self.current_task_info["name"])

    def start_stop_stopwatch(self):
        if self.is_stopwatch_running:
            end_time = time.time()
            duration = end_time - self.stopwatch_start_time
            self.is_stopwatch_running = False
            self.stopwatch_start_time = None
            self.last_saved_duration = duration

            task_entry = {
                "type": self.current_task_info["type"],
                "tag": self.current_task_info["tag"],
                "name": self.current_task_info["name"],
                "start": datetime.datetime.fromtimestamp(end_time - duration).isoformat(timespec='milliseconds'),
                "end": datetime.datetime.fromtimestamp(end_time).isoformat(timespec='milliseconds'),
                "duration": round(duration, 3)
            }
            tasks = self._load_tasks()
            tasks.append(task_entry)
            self._save_tasks(tasks)
            self._display_message(f"Stopwatch stopped. Task '{
                                  task_entry['name']}' recorded.")
            if self.stdscr.getmaxyx()[0] > 13:
                self._display_message(
                    f"Duration: {datetime.timedelta(seconds=int(duration))}", line=1)
        else:
            if not self._is_task_info_valid():
                self._display_message("Error: Task info null. Use 'i' first.")
                return

            self.stopwatch_start_time = time.time()
            self.is_stopwatch_running = True
            self._display_message("Stopwatch started.")

    def add_manual_task(self):
        if not self._is_task_info_valid():
            self._display_message("Error: Task info null. Use 'i' first.")
            return
        if self.is_stopwatch_running:
            self._display_message(
                "Cannot add manual task while stopwatch is running. Stop it (s).")
            return

        h, w = self.stdscr.getmaxyx()
        start_line = 12

        self._display_message("Enter start and end times for the manual task.")
        self._display_message(
            "Format: YYYY-MM-DD HH:MM (e.g., 2023-10-27 09:00)", line=1)
        try:
            start_str = self._get_curses_input(
                start_line + 2, 0, "Start Time: ").strip()
            end_str = self._get_curses_input(
                start_line + 3, 0, "End Time: ").strip()

            fmts = ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"]
            start_dt = None
            end_dt = None
            for fmt in fmts:
                try:
                    start_dt = datetime.datetime.strptime(start_str, fmt)
                    break
                except ValueError:
                    pass
            for fmt in fmts:
                try:
                    end_dt = datetime.datetime.strptime(end_str, fmt)
                    break
                except ValueError:
                    pass

            if start_dt is None or end_dt is None:
                raise ValueError(
                    "Invalid time format. Use YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:S.")

            if start_dt >= end_dt:
                raise ValueError("Start time must be before end time.")

            duration = (end_dt - start_dt).total_seconds()

            task_entry = {
                "type": self.current_task_info["type"],
                "tag": self.current_task_info["tag"],
                "name": self.current_task_info["name"],
                "start": start_dt.isoformat(timespec='milliseconds'),
                "end": end_dt.isoformat(timespec='milliseconds'),
                "duration": round(duration, 3)
            }
            tasks = self._load_tasks()
            tasks.append(task_entry)
            self._save_tasks(tasks)
            self._display_message(
                f"Manual task '{task_entry['name']}' added successfully.", line=4)

        except ValueError as e:
            self._display_message(f"Error: {e}", line=4)
        except Exception as e:
            self._display_message(f"An unexpected error occurred: {e}", line=4)

        for i in range(5):
            self.stdscr.move(start_line + i, 0)
            self.stdscr.clrtoeol()
        self.stdscr.refresh()

    def _main_loop(self, stdscr):
        self.stdscr = stdscr

        curses.noecho()
        curses.cbreak()
        stdscr.nodelay(True)
        stdscr.timeout(1000)

        self.display_status()

        while True:
            key = stdscr.getch()

            if key != -1:
                command = chr(key).lower()

                if command == 'i':
                    self.input_task()
                elif command == 's':
                    self.start_stop_stopwatch()
                elif command == 'a':
                    self.add_manual_task()
                elif command == 'q':
                    if self.is_stopwatch_running:
                        self._display_message(
                            "Stopwatch running. Stop it (s) before quitting.")
                    else:
                        self._display_message(
                            "Quitting program. Goodbye!", line=0)
                        if self.stdscr.getmaxyx()[0] > 13:
                            self.stdscr.move(13, 0)
                            self.stdscr.clrtoeol()
                        time.sleep(1)
                        break
                else:
                    self._display_message(f"Invalid command '{
                                          command}'. Use i, s, a, q.")

            self.display_status()


def main():
    tracker = TimeTracker()
    try:
        curses.wrapper(tracker._main_loop)
    except Exception as e:
        curses.endwin()
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
