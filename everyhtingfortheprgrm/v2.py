import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
from pynput import mouse
import threading
import queue
import random
from pathlib import Path
import pygame


# ==================================================
# SETTINGS
# ==================================================

BASE_FOLDER = Path(__file__).parent

STICKER_GIFS = [
    BASE_FOLDER / "bop_cat.gif",
]

NYAN_GIF = BASE_FOLDER / "nyan_cat.gif"
NYAN_AUDIO = BASE_FOLDER / "nyan_audio.mp3"

STICKER_SIZE = 120
STICKER_LIFETIME = 5000
MAX_STICKER_FRAMES = 30

CLICK_LIMIT = 30

NYAN_SIZE = 180
NYAN_SPEED = 18
RAINBOW_SPEED = 12


# ==================================================
# GLOBAL VARIABLES
# ==================================================

click_queue = queue.Queue()

click_count = 0
nyan_running = False

loaded_sticker_gifs = []


# ==================================================
# LOAD GIF FRAMES
# ==================================================

def load_gif(gif_path, max_size, max_frames=None):
    gif = Image.open(gif_path)

    frames = []
    durations = []

    for frame in ImageSequence.Iterator(gif):
        duration = frame.info.get("duration", 100)
        duration = max(20, duration)

        frame = frame.convert("RGBA")
        frame.thumbnail((max_size, max_size))

        frames.append(frame.copy())
        durations.append(duration)

        if max_frames is not None:
            if len(frames) >= max_frames:
                break

    return frames, durations


# ==================================================
# MAIN TKINTER WINDOW
# ==================================================

root = tk.Tk()
root.withdraw()


# ==================================================
# INITIALIZE AUDIO
# ==================================================

try:
    pygame.mixer.init()
    pygame.mixer.music.load(str(NYAN_AUDIO))
    print("Nyan Cat audio loaded")

except Exception as error:
    nyan_sound = None
    print(f"Audio could not be loaded: {error}")


# ==================================================
# PRELOAD STICKER GIFS
# ==================================================

for gif_file in STICKER_GIFS:
    try:
        frames, durations = load_gif(
            gif_file,
            STICKER_SIZE,
            MAX_STICKER_FRAMES
        )

        if frames:
            photos = [
                ImageTk.PhotoImage(frame)
                for frame in frames
            ]

            # Keeping the PhotoImage objects here prevents
            # them from being destroyed by Python's garbage collector.
            loaded_sticker_gifs.append(
                (photos, durations)
            )

            print(
                f"Loaded {gif_file.name}: "
                f"{len(photos)} frames"
            )

    except Exception as error:
        print(
            f"Could not load {gif_file.name}: "
            f"{error}"
        )


# ==================================================
# SPAWN NORMAL STICKER
# ==================================================

def spawn_sticker(x, y):
    if not loaded_sticker_gifs:
        return

    photos, durations = random.choice(
        loaded_sticker_gifs
    )

    sticker = tk.Toplevel(root)

    sticker.overrideredirect(True)
    sticker.attributes("-topmost", True)

    # Black is made transparent on Windows
    sticker.configure(bg="black")
    sticker.attributes(
        "-transparentcolor",
        "black"
    )

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

        label.configure(
            image=photos[frame_number]
        )

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


# ==================================================
# NYAN CAT EVENT
# ==================================================

def start_nyan_cat():
    global nyan_running

    if nyan_running:
        return

    nyan_running = True

    try:
        frames, durations = load_gif(
            NYAN_GIF,
            NYAN_SIZE
        )

        if not frames:
            print("Nyan Cat GIF has no frames")
            nyan_running = False
            return

        nyan_photos = [
            ImageTk.PhotoImage(frame)
            for frame in frames
        ]

    except Exception as error:
        print(
            f"Could not load Nyan Cat GIF: "
            f"{error}"
        )

        nyan_running = False
        return

    # Start audio
    if nyan_sound is not None:
        try:
            pygame.mixer.music.play()
        except Exception as error:
            print(
                f"Could not play audio: "
                f"{error}"
            )

    # Fullscreen overlay
    overlay = tk.Toplevel(root)

    overlay.overrideredirect(True)
    overlay.attributes("-topmost", True)

    screen_width = overlay.winfo_screenwidth()
    screen_height = overlay.winfo_screenheight()

    overlay.geometry(
        f"{screen_width}x{screen_height}+0+0"
    )

    canvas = tk.Canvas(
        overlay,
        width=screen_width,
        height=screen_height,
        bg="black",
        highlightthickness=0
    )

    canvas.pack(
        fill="both",
        expand=True
    )

    cat_y = (
        screen_height - NYAN_SIZE
    ) // 2

    cat_x = -NYAN_SIZE

    rainbow_colors = [
        "#ff0000",
        "#ff8c00",
        "#ffff00",
        "#00cc00",
        "#008cff",
        "#8a2be2"
    ]

    rainbow_height = 12
    rainbow_segment_width = 45

    def animate_nyan(
        frame_number=0,
        current_x=cat_x,
        rainbow_offset=0
    ):
        global nyan_running

        if not overlay.winfo_exists():
            nyan_running = False
            return

        canvas.delete("rainbow")
        canvas.delete("cat")

        # The rainbow ends behind the cat
        trail_end = current_x + 25

        if trail_end > 0:
            for color_index, color in enumerate(
                rainbow_colors
            ):
                stripe_y = (
                    cat_y
                    + NYAN_SIZE // 2
                    - (
                        len(rainbow_colors)
                        * rainbow_height
                    ) // 2
                    + color_index * rainbow_height
                )

                # Each stripe consists of moving segments.
                # This creates the animated rainbow effect.
                segment_x = (
                    -rainbow_segment_width
                    + rainbow_offset
                )

                while segment_x < trail_end:
                    segment_right = (
                        segment_x
                        + rainbow_segment_width
                    )

                    canvas.create_rectangle(
                        segment_x,
                        stripe_y,
                        min(
                            segment_right,
                            trail_end
                        ),
                        stripe_y + rainbow_height,
                        fill=color,
                        outline="",
                        tags="rainbow"
                    )

                    # Gap between rainbow segments
                    segment_x += (
                        rainbow_segment_width * 2
                    )

        # Draw the current animated cat frame
        canvas.create_image(
            current_x,
            cat_y,
            image=nyan_photos[frame_number],
            anchor="nw",
            tags="cat"
        )

        next_frame = (
            frame_number + 1
        ) % len(nyan_photos)

        next_x = current_x + NYAN_SPEED

        next_rainbow_offset = (
            rainbow_offset + RAINBOW_SPEED
        ) % (
            rainbow_segment_width * 2
        )

        # End when the cat fully leaves the screen
        if current_x > screen_width:
            if nyan_sound is not None:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass

            overlay.destroy()
            nyan_running = False
            return

        delay = max(
            20,
            durations[frame_number]
        )

        overlay.after(
            delay,
            animate_nyan,
            next_frame,
            next_x,
            next_rainbow_offset
        )

    animate_nyan()


# ==================================================
# PROCESS EVENTS ON TKINTER'S MAIN THREAD
# ==================================================

def process_clicks():
    while not click_queue.empty():
        event_type, data = click_queue.get()

        if event_type == "NYAN":
            start_nyan_cat()

        elif event_type == "CLICK":
            x, y = data

            spawn_sticker(
                x - STICKER_SIZE // 2,
                y - STICKER_SIZE // 2
            )

    root.after(
        10,
        process_clicks
    )


# ==================================================
# GLOBAL MOUSE LISTENER
# ==================================================

def on_click(x, y, button, pressed):
    global click_count

    if not pressed:
        return

    if nyan_running:
        return

    click_count += 1

    print(
        f"Click count: {click_count}"
    )

    if click_count >= CLICK_LIMIT:
        click_count = 0
        click_queue.put(
            ("NYAN", None)
        )

    else:
        click_queue.put(
            ("CLICK", (x, y))
        )


def start_mouse_listener():
    with mouse.Listener(
        on_click=on_click
    ) as listener:
        listener.join()


# ==================================================
# START PROGRAM
# ==================================================

threading.Thread(
    target=start_mouse_listener,
    daemon=True
).start()

process_clicks()

root.mainloop()