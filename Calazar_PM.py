#!/usr/bin/env python3
"""
password_dragon.py
Terminal Password Strength Analyzer + Suggester with ASCII dragon animation.
Uses curses (standard library). Optional pyperclip for clipboard copy.
"""

import curses
import time
import math
import random
import threading
import sys

try:
    import pyperclip
    PYPERCLIP = True
except Exception:
    PYPERCLIP = False

# ---------- ASCII Dragon frames (small, simple) ----------
DRAGON_FRAMES = [
r"""   __/\
  /  . \
 /_  _\ \
   \/_/  """,

r"""   __/\
  / o. \
 /_  _\ \
   \/_/  """,

r"""   __/\
  /  . \
 /_  _\ \
   \/\/  """,

r"""   __/\
  / o. \
 /_  _\ \
   \/\/  """
]

# ---------- Common weak passwords list (short sample) ----------
COMMONS = {
    "123456","password","123456789","qwerty","abc123","111111","123123","iloveyou",
    "password1","admin","letmein"
}

# ---------- Utilities ----------
def calc_entropy(pw: str) -> float:
    """Calculate approximate entropy in bits."""
    pool = 0
    if any(c.islower() for c in pw): pool += 26
    if any(c.isupper() for c in pw): pool += 26
    if any(c.isdigit() for c in pw): pool += 10
    # approximate special char set
    if any(not c.isalnum() for c in pw): pool += 32
    if pool == 0 or len(pw) == 0:
        return 0.0
    entropy = len(pw) * math.log2(pool)
    # round to 2 decimal places carefully (digit-by-digit style)
    return float(round(entropy, 2))

def analyze_password(pw: str) -> dict:
    """Return analysis dict: score, entropy, rating_text, suggestions list."""
    if not pw:
        return {"score":0,"entropy":0.0,"rating":"Empty","suggestions":["Type a password"]}

    if pw.lower() in COMMONS:
        return {"score":0,"entropy":calc_entropy(pw),"rating":"Very Weak (common)","suggestions":["Use a unique password not in common lists","Increase length","Add symbols and mixed case"]}

    entropy = calc_entropy(pw)
    score = 0
    if len(pw) >= 8: score += 1
    if len(pw) >= 12: score += 1
    if any(c.islower() for c in pw): score += 1
    if any(c.isupper() for c in pw): score += 1
    if any(c.isdigit() for c in pw): score += 1
    if any(not c.isalnum() for c in pw): score += 1
    if entropy > 60: score += 1

    # rating
    if score <= 2:
        rating = "Weak"
    elif score <= 4:
        rating = "Medium"
    elif score <= 6:
        rating = "Strong"
    else:
        rating = "Very Strong"

    # suggestions
    suggestions = []
    if len(pw) < 12:
        suggestions.append("Increase length to 12+ characters")
    if not any(c.isupper() for c in pw):
        suggestions.append("Add uppercase letters (A-Z)")
    if not any(c.islower() for c in pw):
        suggestions.append("Add lowercase letters (a-z)")
    if not any(c.isdigit() for c in pw):
        suggestions.append("Add digits (0-9)")
    if not any(not c.isalnum() for c in pw):
        suggestions.append("Include symbols (e.g. ! @ # $ %)")
    if " " in pw:
        suggestions.append("Avoid spaces in passwords (or use predictable separators carefully)")
    if not suggestions:
        suggestions.append("Looks good — consider using a passphrase for extra entropy")

    return {"score":score,"entropy":entropy,"rating":rating,"suggestions":suggestions}

def generate_suggestion(length=16) -> str:
    """Generate a strong suggested password (random mix)."""
    lowers = "abcdefghijklmnopqrstuvwxyz"
    uppers = lowers.upper()
    digits = "0123456789"
    symbols = "!@#$%^&*()-_=+[]{};:,.<>/?"
    # ensure inclusion of at least one of each category
    allchars = lowers + uppers + digits + symbols
    pwd = [
        random.choice(lowers),
        random.choice(uppers),
        random.choice(digits),
        random.choice(symbols)
    ]
    while len(pwd) < length:
        pwd.append(random.choice(allchars))
    random.shuffle(pwd)
    return "".join(pwd)

# ---------- Curses UI ----------
def draw_dragon(stdscr, frame, x, y, color_pair):
    """Draw dragon frame at (y,x)."""
    for i, line in enumerate(frame.splitlines()):
        try:
            stdscr.addstr(y + i, x, line, curses.color_pair(color_pair))
        except curses.error:
            # off-screen writes will raise; ignore
            pass

def draw_input_box(stdscr, center_y, center_x, width, height, shimmer=False):
    """Draw the liquid-glass style input box (simulated)."""
    top = center_y - height//2
    left = center_x - width//2
    # outer border
    for dx in range(width):
        stdscr.addch(top, left+dx, curses.ACS_HLINE, curses.color_pair(2))
        stdscr.addch(top+height-1, left+dx, curses.ACS_HLINE, curses.color_pair(2))
    for dy in range(1, height-1):
        stdscr.addch(top+dy, left, curses.ACS_VLINE, curses.color_pair(2))
        stdscr.addch(top+dy, left+width-1, curses.ACS_VLINE, curses.color_pair(2))
    stdscr.addch(top, left, curses.ACS_ULCORNER, curses.color_pair(2))
    stdscr.addch(top, left+width-1, curses.ACS_URCORNER, curses.color_pair(2))
    stdscr.addch(top+height-1, left, curses.ACS_LLCORNER, curses.color_pair(2))
    stdscr.addch(top+height-1, left+width-1, curses.ACS_LRCORNER, curses.color_pair(2))

    # inner "glass" shimmer rows
    for i in range(1, height-1):
        row_text = " " * (width-2)
        if shimmer and (i % 3 == 0):
            stdscr.addstr(top+i, left+1, row_text, curses.color_pair(3) | curses.A_BOLD)
        else:
            stdscr.addstr(top+i, left+1, row_text, curses.color_pair(1))

def main(stdscr):
    # --- init ---
    curses.curs_set(0)  # hide cursor
    stdscr.nodelay(True)  # non-blocking getch
    stdscr.timeout(80)    # refresh every 80ms
    curses.start_color()
    curses.use_default_colors()

    # color pairs
    # pair 1 = green on black (main text)
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    # pair 2 = dim green for border
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    # pair 3 = bright bold green for shimmer/highlight
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    # pair 4 = dark grey for secondary text (if terminal supports)
    try:
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)
    except:
        curses.init_pair(4, curses.COLOR_BLACK, -1)

    max_y, max_x = stdscr.getmaxyx()
    center_y, center_x = max_y // 2, max_x // 2

    input_buffer = []
    message = "Type your password (Enter to evaluate). Press 's' to generate suggestion, Ctrl+C to exit."
    suggestion_pwd = ""
    copied_text = ""

    # dragon animation positions
    frame_idx = 0
    dragon_x = -20
    dragon_y = 2
    dragon_direction = 1

    last_shimmer = 0

    # main loop
    try:
        while True:
            stdscr.erase()
            max_y, max_x = stdscr.getmaxyx()
            center_y, center_x = max_y // 2, max_x // 2

            # draw background "green rain" effect (sparse)
            for i in range(0, max_x, 5):
                r = (i + int(time.time()*3)) % max_y
                try:
                    stdscr.addstr(r, i, random.choice([".", ",", "`", "'"]), curses.color_pair(1))
                except curses.error:
                    pass

            # animate dragon moving across top - loops back
            frame = DRAGON_FRAMES[frame_idx % len(DRAGON_FRAMES)]
            draw_dragon(stdscr, frame, dragon_x, dragon_y, 1)
            frame_idx += 1
            dragon_x += dragon_direction * 2
            if dragon_x > max_x:
                dragon_x = -len(frame.splitlines()[0]) - 5

            # shimmer toggle for the glass effect
            shimmer = (int(time.time() * 2) % 2 == 0)

            # draw input box
            box_w = max(60, min(80, max_x - 10))
            box_h = 7
            draw_input_box(stdscr, center_y, center_x, box_w, box_h, shimmer=shimmer)

            # show title
            title = "🔐 Password Strength Analyzer"
            try:
                stdscr.addstr(center_y - box_h//2 - 2, center_x - len(title)//2, title, curses.A_BOLD | curses.color_pair(3))
            except curses.error:
                pass

            # show instruction
            try:
                stdscr.addstr(center_y - box_h//2 + 1, center_x - (box_w//2) + 2, message, curses.color_pair(1))
            except curses.error:
                pass

            # show input text as bullets for privacy
            display_pwd = "".join(input_buffer)
            display_mask = "*" * len(display_pwd)
            try:
                stdscr.addstr(center_y, center_x - (box_w//2) + 3, display_mask[:box_w-6], curses.color_pair(1) | curses.A_BOLD)
            except curses.error:
                pass

            # analyze live
            analysis = analyze_password(display_pwd)
            rating = f"[{analysis['rating']}] Entropy: {analysis['entropy']} bits"
            try:
                stdscr.addstr(center_y + box_h//2 + 1, center_x - len(rating)//2, rating, curses.color_pair(1))
            except curses.error:
                pass

            # show strength bar
            bar_w = min(40, max_x - 20)
            score = analysis["score"]
            # map score (0..7+) to filled
            filled = int((score / 7.0) * bar_w)
            bar = "[" + "#" * filled + "-" * (bar_w - filled) + "]"
            try:
                stdscr.addstr(center_y + box_h//2 + 3, center_x - len(bar)//2, bar, curses.color_pair(1))
            except curses.error:
                pass

            # show suggestions (first two)
            sug_title = "Suggestions:"
            try:
                stdscr.addstr(center_y + box_h//2 + 5, center_x - box_w//2 + 3, sug_title, curses.color_pair(1) | curses.A_UNDERLINE)
                for idx, s in enumerate(analysis["suggestions"][:4]):
                    stdscr.addstr(center_y + box_h//2 + 6 + idx, center_x - box_w//2 + 5, f"- {s}", curses.color_pair(1))
            except curses.error:
                pass

            # show suggestion password and copy hint
            if suggestion_pwd:
                sp = f"Suggested: {suggestion_pwd}"
                try:
                    stdscr.addstr(center_y - box_h//2 - 1, center_x + box_w//2 - len(sp) - 2, sp, curses.color_pair(1))
                    if PYPERCLIP:
                        stdscr.addstr(center_y - box_h//2 - 1, center_x + box_w//2 - len(sp) - 20, "[copied to clipboard]", curses.color_pair(1))
                except curses.error:
                    pass

            # show small footer
            footer = "Press BACKSPACE to erase, Enter to evaluate fully, 's' to suggest a strong password, Ctrl+C to quit."
            try:
                stdscr.addstr(max_y - 2, max(0, (max_x - len(footer))//2), footer, curses.color_pair(1))
            except curses.error:
                pass

            stdscr.refresh()

            # read key
            try:
                key = stdscr.getch()
            except KeyboardInterrupt:
                break

            if key == -1:
                # no input; continue animation
                time.sleep(0.02)
                continue

            # Enter key (evaluate / final display)
            if key in (curses.KEY_ENTER, 10, 13):
                # On enter, we can flash a confirmation message
                msg = f"Final rating: {analysis['rating']} — entropy {analysis['entropy']} bits."
                try:
                    stdscr.addstr(center_y + box_h//2 + 8, center_x - len(msg)//2, msg, curses.color_pair(3) | curses.A_BOLD)
                    stdscr.refresh()
                except curses.error:
                    pass
                time.sleep(0.8)
                continue

            # backspace
            if key in (curses.KEY_BACKSPACE, 127, 8):
                if input_buffer:
                    input_buffer.pop()
                continue

            # 's' key => generate suggestion
            if key in (ord('s'), ord('S')):
                suggestion_pwd = generate_suggestion(16)
                if PYPERCLIP:
                    try:
                        pyperclip.copy(suggestion_pwd)
                    except Exception:
                        pass
                continue

            # allow printable characters
            if 32 <= key <= 126:
                input_buffer.append(chr(key))
                continue

            # other keys are ignored for now

    except KeyboardInterrupt:
        pass
    finally:
        curses.curs_set(1)
        stdscr.nodelay(False)

if __name__ == "__main__":
    # quick check terminal size
    try:
        curses.wrapper(main)
    except Exception as e:
        print("An error occurred:", e)
        print("Make sure you're running this in a real terminal (macOS/Linux).")
        sys.exit(1)
