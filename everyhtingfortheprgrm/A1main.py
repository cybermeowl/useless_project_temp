import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
from pynput import mouse
import threading
import queue
import random
from pathlib import Path


# -----------------------------
# SETTINGS
# -----------------------------

GIF_FILES = [
    Path(__file__).parent / "bop_cat.gif"
]

STICKER_SIZE = 120
STICKER_LIFETIME = 5000  # milliseconds

# All clicks will be sent here
click_queue = queue.Queue()


# -----------------------------
# LOAD GIF
# -----------------------------

def load_gif(gif_path):
    gif = Image.open(gif_path)
    frames = []
    durations = []

    for frame in ImageSequence.Iterator(gif):
        duration = frame.info.get("duration", 100)

        frame = frame.convert("RGBA")
        frame.thumbnail((STICKER_SIZE, STICKER_SIZE))

        frames.append(frame.copy())
        durations.append(duration)

    return frames, durations


# -----------------------------
# TKINTER SETUP
# -----------------------------

root = tk.Tk()

root.withdraw()

root.attributes("-topmost", True)


# -----------------------------
# SPAWN STICKER
# -----------------------------

def spawn_sticker(x, y):

    frames, durations = load_gif(random.choice(GIF_FILES))

# Limit the GIF to its first 30 frames
    frames = frames[:30]
    durations = durations[:30]

    sticker = tk.Toplevel(root)

    sticker.overrideredirect(True)

    sticker.attributes("-topmost", True)

    sticker.configure(bg="black")

    # Make black transparent
    sticker.attributes("-transparentcolor", "black")

    label = tk.Label(
        sticker,
        bg="black",
        bd=0
    )

    label.pack()

    sticker.geometry(
        f"{STICKER_SIZE}x{STICKER_SIZE}+{x}+{y}"
    )

    photos = [
        ImageTk.PhotoImage(frame)
        for frame in frames
    ]

    def animate(frame_number=0):

        if not sticker.winfo_exists():
            return

        label.configure(image=photos[frame_number])

        next_frame = (frame_number + 1) % len(photos)

        sticker.after(
            durations[frame_number],
            animate,
            next_frame
        )

    animate()

    # Remove after lifetime
    sticker.after(
        STICKER_LIFETIME,
        sticker.destroy
    )


# -----------------------------
# PROCESS CLICKS
# -----------------------------

def process_clicks():

    while not click_queue.empty():

        x, y = click_queue.get()

        spawn_sticker(
            x - STICKER_SIZE // 2,
            y - STICKER_SIZE // 2
        )

    root.after(10, process_clicks)


# -----------------------------
# GLOBAL MOUSE LISTENER
# -----------------------------

def on_click(x, y, button, pressed):

    if pressed:

        click_queue.put((x, y))


def start_mouse_listener():

    with mouse.Listener(on_click=on_click) as listener:

        listener.join()


# Start mouse listener in background
threading.Thread(
    target=start_mouse_listener,
    daemon=True
).start()


# Start processing clicks
process_clicks()

root.mainloop()