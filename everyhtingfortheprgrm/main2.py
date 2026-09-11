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
    Path(__file__).parent / "bop_cat.gif",
    Path(__file__).parent / "scuba1.gif",
]

STICKER_SIZE = 120
STICKER_LIFETIME = 5000  # milliseconds
MAX_FRAMES = 30

click_queue = queue.Queue()


# -----------------------------
# LOAD GIF
# -----------------------------

def load_gif(gif_path):
    frames = []
    durations = []

    with Image.open(gif_path) as gif:
        for frame_number, frame in enumerate(
            ImageSequence.Iterator(gif)
        ):
            # Stop after a maximum number of frames
            if frame_number >= MAX_FRAMES:
                break

            # Read duration before converting the frame
            duration = frame.info.get("duration", 100)

            # Make a copy before converting
            frame = frame.convert("RGBA")
            frame.thumbnail((STICKER_SIZE, STICKER_SIZE))

            frames.append(frame.copy())
            durations.append(max(duration, 20))

    return frames, durations


# -----------------------------
# TKINTER SETUP
# -----------------------------

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)


# -----------------------------
# PRELOAD GIFS
# -----------------------------

loaded_gifs = []

for gif_file in GIF_FILES:
    try:
        frames, durations = load_gif(gif_file)

        if frames:
            # Convert PIL frames into Tkinter images only once
            photos = [
                ImageTk.PhotoImage(frame)
                for frame in frames
            ]

            loaded_gifs.append((photos, durations))

            print(
                f"Loaded {gif_file.name}: "
                f"{len(photos)} frames"
            )

    except Exception as error:
        print(f"Could not load {gif_file.name}: {error}")


if not loaded_gifs:
    print("No GIFs could be loaded.")
    root.destroy()
    raise SystemExit


# -----------------------------
# SPAWN STICKER
# -----------------------------

def spawn_sticker(x, y):

    photos, durations = random.choice(loaded_gifs)

    sticker = tk.Toplevel(root)
    sticker.overrideredirect(True)
    sticker.attributes("-topmost", True)

    sticker.configure(bg="black")
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

    def animate(frame_number=0):

        if not sticker.winfo_exists():
            return

        label.configure(image=photos[frame_number])

        next_frame = (
            frame_number + 1
        ) % len(photos)

        sticker.after(
            durations[frame_number],
            animate,
            next_frame
        )

    animate()

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

    with mouse.Listener(
        on_click=on_click
    ) as listener:
        listener.join()


# Start mouse listener in background
threading.Thread(
    target=start_mouse_listener,
    daemon=True
).start()


# Start processing clicks
process_clicks()

root.mainloop()