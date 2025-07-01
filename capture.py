import time
import datetime
import yaml
import os
import curses

# --- Global Constants ---
FILENAME = "tasks.yaml"

# --- Helper Functions (Pure functions or functions that operate on passed state/stdscr) ---


def ensure_data_file_exists(filename):
    """Ensures the YAML data file exists, creating it empty if not."""
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            yaml.dump([], f)


def load_tasks(filename, stdscr):
    """Loads tasks from the YAML file."""
    try:
        with open(filename, 'r') as f:
            return yaml.safe_load(f) or []
    except FileNotFoundError:
        return []  # File will be created later if needed
    except yaml.YAMLError as e:
        display_message(stdscr, f"Error loading YAML: {
                        e}. Starting empty.", line=0)
        return []


def save_tasks(filename, tasks, stdscr):
    """Saves tasks to the YAML file."""
    try:
        with open(filename, 'w') as f:
            yaml.dump(tasks, f, default_flow_style=False)
    except Exception as e:
        display_message(stdscr, f"Error saving tasks: {e}", line=0)


def display_message(stdscr, message, line=0):
    """Displays a message on a specific line in the curses window."""
    h, w = stdscr.getmaxyx()
    message_line = 12 + line

    # Ensure message doesn't overwrite command prompt
    if message_line >= h - 1:
        message_line = h - 2

    stdscr.move(message_line, 0)
    stdscr.clrtoeol()  # Clear to end of line
    stdscr.addstr(message_line, 0, message[:w-1])  # Truncate if too long
    stdscr.refresh()


def get_curses_input(stdscr, prompt_line, prompt_col, prompt_text=""):
    """Gets string input from the user via curses."""
    stdscr.move(prompt_line, prompt_col)
    stdscr.clrtoeol()
    stdscr.addstr(prompt_line, prompt_col, prompt_text)
    stdscr.refresh()

    input_str = []
    curses.echo()  # Enable echoing characters to screen
    curses.curs_set(1)  # Show cursor

    current_col = prompt_col + len(prompt_text)
    stdscr.move(prompt_line, current_col)

    while True:
        char_code = stdscr.getch()
        if char_code == curses.KEY_ENTER or char_code in [10, 13]:  # Enter key
            break
        elif char_code == curses.KEY_BACKSPACE or char_code == 127:  # Backspace/Delete key
            if input_str:
                input_str.pop()
                current_col -= 1
                # Delete character from screen
                stdscr.delch(prompt_line, current_col)
        elif 32 <= char_code <= 126:  # Printable ASCII characters
            input_str.append(chr(char_code))
            stdscr.addch(prompt_line, current_col, char_code)
            current_col += 1
        stdscr.refresh()

    curses.noecho()  # Disable echoing
    curses.curs_set(0)  # Hide cursor
    return "".join(input_str)


def is_task_info_valid(task_info):
    """Checks if any part of the current task info is filled."""
    return bool(task_info["type"] or task_info["tag"] or task_info["name"])

# --- Main Application Logic Functions ---


def display_current_status(stdscr, state):
    """Displays the current status of the tracker."""
    stdscr.erase()  # Clear the entire screen

    h, w = stdscr.getmaxyx()

    stdscr.addstr(0, 0, "--- Time Tracker ---")

    current_task = state["current_task_info"]
    stdscr.addstr(2, 0, f"Current Task: Type: {current_task['type'] or 'N/A'}")
    stdscr.addstr(3, 0, f"              Tag:  {current_task['tag'] or 'N/A'}")
    stdscr.addstr(4, 0, f"              Name: {current_task['name'] or 'N/A'}")

    if state["is_stopwatch_running"]:
        elapsed_time = 0
        if state["stopwatch_start_time"] is not None:
            elapsed_time = time.time() - state["stopwatch_start_time"]
        stdscr.addstr(6, 0, f"Stopwatch: RUNNING ({
                      datetime.timedelta(seconds=int(elapsed_time))})")
    else:
        status_text = "STOPPED"
        if state["last_saved_duration"] is not None:
            status_text += f" (Last task: {datetime.timedelta(
                seconds=int(state['last_saved_duration']))})"
        stdscr.addstr(6, 0, f"Stopwatch: {status_text}")

    stdscr.addstr(8, 0, "--------------------")

    stdscr.addstr(
        9, 0, "Commands: i (input task), s (start/stop stopwatch), a (add manual), q (quit)")
    stdscr.addstr(10, 0, "(Type a command key directly, no Enter needed)")

    # Clear message/input area, leaving space for the command prompt at the bottom
    for r in range(12, h - 1):
        stdscr.move(r, 0)
        stdscr.clrtoeol()

    stdscr.addstr(h - 1, 0, "Enter command: ")

    stdscr.refresh()


def prompt_for_task_details(stdscr, state):
    """Prompts the user to input details for the current task."""
    if state["is_stopwatch_running"]:
        display_message(
            stdscr, "Cannot input new task while stopwatch is running. Stop it (s).")
        return

    start_line = 12

    display_message(stdscr, "Enter task details (press Enter after each):")
    state["current_task_info"]["type"] = get_curses_input(
        stdscr, start_line + 1, 0, "Task Type: ").strip()
    state["current_task_info"]["tag"] = get_curses_input(
        stdscr, start_line + 2, 0, "Task Tag: ").strip()
    state["current_task_info"]["name"] = get_curses_input(
        stdscr, start_line + 3, 0, "Task Name: ").strip()

    if not is_task_info_valid(state["current_task_info"]):
        display_message(
            stdscr, "Warning: Task fields empty. Fill for better tracking.", line=4)
    else:
        display_message(stdscr, "Task info updated.", line=4)

    # Clear input prompts
    for i in range(5):
        stdscr.move(start_line + i, 0)
        stdscr.clrtoeol()
    stdscr.refresh()


def handle_stopwatch_toggle(stdscr, state, filename):
    """Starts or stops the stopwatch and records the task."""
    if state["is_stopwatch_running"]:
        end_time = time.time()
        duration = end_time - state["stopwatch_start_time"]

        state["is_stopwatch_running"] = False
        state["stopwatch_start_time"] = None
        state["last_saved_duration"] = duration

        task_entry = {
            "type": state["current_task_info"]["type"],
            "tag": state["current_task_info"]["tag"],
            "name": state["current_task_info"]["name"],
            "start": datetime.datetime.fromtimestamp(end_time - duration).isoformat(timespec='milliseconds'),
            "end": datetime.datetime.fromtimestamp(end_time).isoformat(timespec='milliseconds'),
            "duration": round(duration, 3)
        }
        tasks = load_tasks(filename, stdscr)
        tasks.append(task_entry)
        save_tasks(filename, tasks, stdscr)
        display_message(stdscr, f"Stopwatch stopped. Task '{
                        task_entry['name']}' recorded.")
        # Check if there's space for a second message line
        if stdscr.getmaxyx()[0] > 13:
            display_message(stdscr, f"Duration: {
                            datetime.timedelta(seconds=int(duration))}", line=1)
    else:
        if not is_task_info_valid(state["current_task_info"]):
            display_message(
                stdscr, "Error: Task info empty. Use 'i' first to set a task.")
            return

        state["stopwatch_start_time"] = time.time()
        state["is_stopwatch_running"] = True
        display_message(stdscr, "Stopwatch started.")


def add_manual_entry(stdscr, state, filename):
    """Adds a manual task entry to the data file."""
    if not is_task_info_valid(state["current_task_info"]):
        display_message(
            stdscr, "Error: Task info empty. Use 'i' first to set a task.")
        return
    if state["is_stopwatch_running"]:
        display_message(
            stdscr, "Cannot add manual task while stopwatch is running. Stop it (s).")
        return

    start_line = 12

    display_message(stdscr, "Enter start and end times for the manual task.")
    display_message(
        stdscr, "Format: YYYY-MM-DD HH:MM (e.g., 2023-10-27 09:00)", line=1)
    try:
        start_str = get_curses_input(
            stdscr, start_line + 2, 0, "Start Time: ").strip()
        end_str = get_curses_input(
            stdscr, start_line + 3, 0, "End Time: ").strip()

        fmts = ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"]
        start_dt = None
        end_dt = None
        for fmt in fmts:
            try:
                start_dt = datetime.datetime.strptime(start_str, fmt)
                break
            except ValueError:
                pass  # Try next format
        for fmt in fmts:
            try:
                end_dt = datetime.datetime.strptime(end_str, fmt)
                break
            except ValueError:
                pass  # Try next format

        if start_dt is None or end_dt is None:
            raise ValueError(
                "Invalid time format. Use YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:S.")

        if start_dt >= end_dt:
            raise ValueError("Start time must be before end time.")

        duration = (end_dt - start_dt).total_seconds()

        task_entry = {
            "type": state["current_task_info"]["type"],
            "tag": state["current_task_info"]["tag"],
            "name": state["current_task_info"]["name"],
            "start": start_dt.isoformat(timespec='milliseconds'),
            "end": end_dt.isoformat(timespec='milliseconds'),
            "duration": round(duration, 3)
        }
        tasks = load_tasks(filename, stdscr)
        tasks.append(task_entry)
        save_tasks(filename, tasks, stdscr)
        display_message(stdscr, f"Manual task '{
                        task_entry['name']}' added successfully.", line=4)

    except ValueError as e:
        display_message(stdscr, f"Error: {e}", line=4)
    except Exception as e:
        display_message(stdscr, f"An unexpected error occurred: {e}", line=4)

    # Clear input prompts
    for i in range(5):
        stdscr.move(start_line + i, 0)
        stdscr.clrtoeol()
    stdscr.refresh()


# --- Main Application Loop ---

def run_tracker_app(stdscr):
    """
    The main application loop for the time tracker.
    This function handles curses setup, state management, and user input.
    """
    # Initialize application state
    app_state = {
        "current_task_info": {
            "type": "",
            "tag": "",
            "name": ""
        },
        "is_stopwatch_running": False,
        "stopwatch_start_time": None,
        "last_saved_duration": None,
    }

    # Curses setup for non-blocking input and no cursor
    curses.noecho()      # Don't echo characters typed by user
    curses.cbreak()      # React to keys instantly, no need for Enter
    stdscr.nodelay(True)  # getch() will return -1 if no input is ready
    stdscr.timeout(1000)  # getch() will wait 1 second before returning -1

    # Initial display
    display_current_status(stdscr, app_state)

    while True:
        key = stdscr.getch()  # Get a character (or -1 if timeout/no input)

        if key != -1:  # If a key was pressed
            # Convert key code to lowercase character
            command = chr(key).lower()

            if command == 'i':
                prompt_for_task_details(stdscr, app_state)
            elif command == 's':
                handle_stopwatch_toggle(stdscr, app_state, FILENAME)
            elif command == 'a':
                add_manual_entry(stdscr, app_state, FILENAME)
            elif command == 'q':
                if app_state["is_stopwatch_running"]:
                    display_message(
                        stdscr, "Stopwatch running. Stop it (s) before quitting.")
                else:
                    display_message(
                        stdscr, "Quitting program. Goodbye!", line=0)
                    if stdscr.getmaxyx()[0] > 13:  # Clear extra line if available
                        stdscr.move(13, 0)
                        stdscr.clrtoeol()
                    time.sleep(1)  # Give user a moment to read goodbye message
                    break  # Exit the main loop
            else:
                display_message(stdscr, f"Invalid command '{
                                command}'. Use i, s, a, q.")

        # Always refresh status at the end of each loop iteration
        # This keeps the stopwatch time updated even if no key is pressed
        display_current_status(stdscr, app_state)


# --- Main Entry Point ---

def main():
    """Main function to start the application."""
    ensure_data_file_exists(FILENAME)
    try:
        # curses.wrapper handles curses initialization and deinitialization
        curses.wrapper(run_tracker_app)
    except Exception as e:
        # If an error occurs outside curses.wrapper, ensure terminal is reset
        # before printing the error. curses.endwin() might be called by wrapper
        # on normal exit, but explicit call here for unhandled exceptions.
        # However, curses.wrapper *already* handles this gracefully.
        # This catch is mostly for errors *before* or *after* curses context.
        # But generally, wrapper is robust.
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
