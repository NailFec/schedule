import os
import curses
import yaml
import hashlib
import math

FILENAME = "progress-data.yaml"


def ensure_data_file_exists(filename):
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            yaml.dump([], f)


def load_tasks(filename, stdscr):
    try:
        with open(filename, 'r') as f:
            return yaml.safe_load(f) or []
    except FileNotFoundError:
        return []
    except yaml.YAMLError as e:
        display_message(stdscr, f"Error loading YAML: {e}. Starting empty.")
        return []


def save_tasks(filename, tasks, stdscr):
    try:
        with open(filename, 'w') as f:
            yaml.dump(tasks, f, default_flow_style=False)
    except Exception as e:
        display_message(stdscr, f"Error saving tasks: {e}")


def display_message(stdscr, message):
    h, w = stdscr.getmaxyx()
    message_line = h - 5
    stdscr.move(message_line, 0)
    stdscr.clrtoeol()
    stdscr.addstr(message_line, 0, message[:w-1])
    stdscr.refresh()


def get_curses_input(stdscr, prompt_line, prompt_col, prompt_text=""):
    stdscr.move(prompt_line, prompt_col)
    stdscr.clrtoeol()
    stdscr.addstr(prompt_line, prompt_col, prompt_text)
    stdscr.refresh()

    input_str = []
    curses.echo()
    curses.curs_set(1)

    current_col = prompt_col + len(prompt_text)
    stdscr.move(prompt_line, current_col)

    while True:
        char_code = stdscr.getch()
        if char_code == curses.KEY_ENTER or char_code in [10, 13]:
            break
        elif char_code == curses.KEY_BACKSPACE or char_code == 127:
            if input_str:
                input_str.pop()
                current_col -= 1
                stdscr.delch(prompt_line, current_col)
        elif 32 <= char_code <= 126:
            if current_col < stdscr.getmaxyx()[1] - 1:
                input_str.append(chr(char_code))
                stdscr.addch(prompt_line, current_col, char_code)
                current_col += 1
        stdscr.refresh()

    curses.noecho()
    curses.curs_set(0)
    return "".join(input_str)


def generate_task_hash(task_type, task_tag, task_name):
    combined_string = f"{task_type}{task_tag}{task_name}"
    hash_object = hashlib.md5(combined_string.encode())
    hex_digest = hash_object.hexdigest()
    numeric_hash = int(hex_digest, 16) % 1_000_000
    return f"{numeric_hash:06d}"


def draw_progress_bar(stdscr, current, total, display_width):
    if total == 0:
        percentage = 0
    else:
        percentage = (current / total) * 100

    fill_char = "="
    empty_char = "-"
    fixed_text_space = 25

    bar_length = display_width - fixed_text_space
    if bar_length < 10:
        bar_length = 10

    filled_length = math.floor(bar_length * percentage / 100)
    bar = fill_char * filled_length
    if filled_length < bar_length:
        bar += ">"
    bar = bar[:bar_length]
    bar += empty_char * (bar_length - len(bar))

    progress_text = f"{current}/{total} ({percentage:.0f}%)"
    display_str = f"[{bar}] {progress_text}"

    return display_str[:display_width]


def display_tasks(stdscr, tasks):
    h, w = stdscr.getmaxyx()

    for r in range(0, h):
        stdscr.move(r, 0)
        stdscr.clrtoeol()

    stdscr.addstr(0, 0, "--- Task Progress Tracker ---")
    stdscr.addstr(1, 0, "Hash      Type        Tag         Name")
    stdscr.addstr(
        2, 0, "--------------------------------------------------------------------")

    start_line = 3
    max_tasks_display = (h - start_line - 6) // 2

    for i, task in enumerate(tasks):
        if i >= max_tasks_display:
            break
        task_line = start_line + i * 2
        progress_line = task_line + 1

        fixed_info_width = 6 + 1 + 12 + 1 + 12 + 1
        task_info = f"{task['hash']:<6} {task['type']:<12} {
            task['tag']:<12} {task['name'][:w-fixed_info_width-1]}"
        stdscr.addstr(task_line, 0, task_info)

        progress_str = draw_progress_bar(
            stdscr, task['current_progress'], task['total_digit'], w)
        stdscr.addstr(progress_line, 0, progress_str)

    stdscr.addstr(h - 3, 0, "--------------------")
    stdscr.addstr(
        h - 2, 0, "Commands: [i]nsert, [a]dd progress, [d]elete, [q]quit")
    stdscr.addstr(h - 1, 0, "Enter command: ")

    stdscr.move(h - 1, len("Enter command: "))
    stdscr.refresh()


def find_task_by_hash_prefix(tasks, hash_prefix):
    matches = []
    for task in tasks:
        if task['hash'].startswith(hash_prefix):
            matches.append(task)

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        return matches
    else:
        return None


def clear_input_area(stdscr):
    h, w = stdscr.getmaxyx()
    for i in range(h - 6, h):
        stdscr.move(i, 0)
        stdscr.clrtoeol()


def handle_insert_task(stdscr, app_state):
    h, w = stdscr.getmaxyx()
    clear_input_area(stdscr)

    stdscr.addstr(h - 6, 0, "Enter task details (press Enter after each):")
    stdscr.refresh()

    task_type = get_curses_input(stdscr, h - 5, 0, "Task Type: ").strip()
    task_tag = get_curses_input(stdscr, h - 4, 0, "Task Tag: ").strip()
    task_name = get_curses_input(stdscr, h - 3, 0, "Task Name: ").strip()
    task_digit_str = get_curses_input(
        stdscr, h - 2, 0, "Total Digit (e.g., 100): ").strip()
    if not (task_type and task_tag and task_name and task_digit_str):
        display_message(stdscr, "Error: All task fields must be filled.")
        curses.napms(1500)
        return

    try:
        total_digit = int(task_digit_str)
        if total_digit <= 0:
            display_message(
                stdscr, "Error: Total Digit must be a positive integer.")
            curses.napms(1500)
            return
    except ValueError:
        display_message(stdscr, "Error: Total Digit must be an integer.")
        curses.napms(1500)
        return

    new_hash = generate_task_hash(task_type, task_tag, task_name)
    for task in app_state["tasks"]:
        if task["hash"] == new_hash:
            display_message(
                stdscr, f"Warning: A task with identical details already exists (Hash: {new_hash}).")
            curses.napms(1500)
            return

    new_task = {
        "hash": new_hash,
        "type": task_type,
        "tag": task_tag,
        "name": task_name,
        "total_digit": total_digit,
        "current_progress": 0
    }
    app_state["tasks"].append(new_task)
    save_tasks(FILENAME, app_state["tasks"], stdscr)
    display_message(stdscr, f"Task '{task_name}' added with hash {new_hash}.")
    curses.napms(1500)


def handle_add_progress(stdscr, app_state):
    h, w = stdscr.getmaxyx()
    clear_input_area(stdscr)

    hash_input = get_curses_input(
        stdscr, h - 3, 0, "Enter task hash (partial allowed): ").strip()
    change_str = get_curses_input(
        stdscr, h - 2, 0, "Enter change (+N, -N): ").strip()

    if not (hash_input and change_str):
        display_message(
            stdscr, "Error: Hash and change value cannot be empty.")
        curses.napms(1500)
        return

    matched_task = find_task_by_hash_prefix(app_state["tasks"], hash_input)

    if matched_task is None:
        display_message(stdscr, f"No task found for hash '{hash_input}'.")
        curses.napms(1500)
        return
    elif isinstance(matched_task, list):
        display_message(stdscr, f"Ambiguous hash '{
                        hash_input}'. Matches multiple tasks. Be more specific.")
        curses.napms(1500)
        return

    try:
        change_amount = int(change_str)
    except ValueError:
        display_message(
            stdscr, "Error: Change amount must be an integer (e.g., +5, -2).")
        curses.napms(1500)
        return

    matched_task['current_progress'] += change_amount
    if matched_task['current_progress'] < 0:
        matched_task['current_progress'] = 0
    if matched_task['current_progress'] > matched_task['total_digit']:
        matched_task['current_progress'] = matched_task['total_digit']

    save_tasks(FILENAME, app_state["tasks"], stdscr)
    display_message(stdscr, f"Progress updated for '{
                    matched_task['name']}' (Hash: {matched_task['hash']}).")
    curses.napms(1500)


def handle_delete_task(stdscr, app_state):
    h, w = stdscr.getmaxyx()
    clear_input_area(stdscr)

    hash_input = get_curses_input(
        stdscr, h - 2, 0, "Enter task hash to delete (partial allowed): ").strip()

    if not hash_input:
        display_message(stdscr, "Error: Hash cannot be empty.")
        curses.napms(1500)
        return

    matched_task = find_task_by_hash_prefix(app_state["tasks"], hash_input)

    if matched_task is None:
        display_message(stdscr, f"No task found for hash '{hash_input}'.")
        curses.napms(1500)
        return
    elif isinstance(matched_task, list):
        display_message(stdscr, f"Ambiguous hash '{
                        hash_input}'. Matches multiple tasks. Be more specific.")
        curses.napms(1500)
        return

    app_state["tasks"] = [t for t in app_state["tasks"]
                          if t["hash"] != matched_task["hash"]]
    save_tasks(FILENAME, app_state["tasks"], stdscr)
    display_message(stdscr, f"Task '{matched_task['name']}' (Hash: {
                    matched_task['hash']}) deleted.")
    curses.napms(1500)


def run_tracker_app(stdscr):
    app_state = {
        "tasks": []
    }

    curses.noecho()
    curses.cbreak()
    stdscr.nodelay(True)
    stdscr.timeout(100)

    app_state["tasks"] = load_tasks(FILENAME, stdscr)

    while True:
        display_tasks(stdscr, app_state["tasks"])
        key = stdscr.getch()

        if key != -1:
            command = chr(key).lower()

            if command == 'i':
                handle_insert_task(stdscr, app_state)
            elif command == 'a':
                handle_add_progress(stdscr, app_state)
            elif command == 'd':
                handle_delete_task(stdscr, app_state)
            elif command == 'q':
                display_message(stdscr, "Quitting program. Goodbye!")
                curses.napms(1000)
                break
            else:
                display_message(stdscr, f"Invalid command '{
                                command}'. Use i, a, d, q.")
                curses.napms(1500)

        curses.napms(50)


if __name__ == "__main__":
    ensure_data_file_exists(FILENAME)
    try:
        curses.wrapper(run_tracker_app)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print("Please ensure your terminal supports curses and is large enough.")
