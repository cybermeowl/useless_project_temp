import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
from pynput import mouse

import threading
import queue
import random
from pathlib import Path

import pygame


# ==================================================
# PATHS
# ==================================================

BASE_FOLDER = Path(__file__).resolve().parent
AUDIO_FOLDER = BASE_FOLDER / "cat_audio"

STICKER_GIFS = [
    BASE_FOLDER / "bop_cat.gif",
    BASE_FOLDER / "scuba_cat.gif",
]

NYAN_GIF = BASE_FOLDER / "nyan_cat.gif"

PET_CATS = {
    "bop": {
        "gif": BASE_FOLDER / "bop_cat.gif",
        "audio": AUDIO_FOLDER / "bop_cat_audio.mp3",
    },

    "scuba": {
        "gif": BASE_FOLDER / "scuba_cat.gif",
        "audio": AUDIO_FOLDER / "scuba_cat_audio.mp3",
    },
}

NYAN_AUDIO = AUDIO_FOLDER / "nyan_audio.mp3"


# ==================================================
# SETTINGS
# ==================================================

STICKER_SIZE = 120
STICKER_LIFETIME = 5000
MAX_STICKER_FRAMES = 30

CLICK_LIMIT = 30

PETS_REQUIRED = 7
PET_CAT_SIZE = 260

NYAN_SIZE = 180
NYAN_SPEED = 18
RAINBOW_SPEED = 12


# ==================================================
# GLOBAL VARIABLES
# ==================================================

root = tk.Tk()
root.withdraw()

click_queue = queue.Queue()

click_count = 0

nyan_running = False
pet_running = False

loaded_sticker_gifs = []
loaded_pet_cats = {}

pet_window = None
pet_label = None
pet_counter_label = None

pet_current_cat = None
pet_count = 0

nyan_audio_loaded = False
pet_audio_loaded = {}


# ==================================================
# FIND AUDIO FILE
# ==================================================

def find_audio_file(path):

    possible_files = [
        path,
        path.with_suffix(".mp3"),
        path.with_suffix(".wav"),
        path.with_suffix(".ogg"),
    ]

    for possible_file in possible_files:

        if possible_file.exists():
            return possible_file

    return None


# ==================================================
# INITIALIZE AUDIO
# ==================================================

def initialize_audio():

    global nyan_audio_loaded

    print()
    print("========== AUDIO DEBUG ==========")
    print(f"Project folder: {BASE_FOLDER}")
    print(f"Audio folder: {AUDIO_FOLDER}")

    if AUDIO_FOLDER.exists():

        print("Files inside cat_audio:")

        for file in AUDIO_FOLDER.iterdir():
            print(f"  {file.name}")

    else:

        print("ERROR: cat_audio folder does not exist.")

    print("=================================")
    print()

    try:

        pygame.mixer.init()

        print("Pygame audio initialized.")

    except Exception as error:

        print("ERROR: Could not initialize pygame audio.")
        print(error)

        return

    # ----------------------------------------------
    # NYAN CAT AUDIO
    # ----------------------------------------------

    nyan_audio_file = find_audio_file(
        NYAN_AUDIO
    )

    if nyan_audio_file is not None:

        try:

            pygame.mixer.music.load(
                str(nyan_audio_file)
            )

            nyan_audio_loaded = True

            print(
                f"Nyan Cat audio loaded: "
                f"{nyan_audio_file}"
            )

        except Exception as error:

            print("ERROR loading Nyan Cat audio:")
            print(error)

    else:

        print(
            "ERROR: Nyan Cat audio not found."
        )

        print(
            f"Expected location: {NYAN_AUDIO}"
        )

    # ----------------------------------------------
    # PET CAT AUDIO
    # ----------------------------------------------

    for cat_name, cat_data in PET_CATS.items():

        audio_file = find_audio_file(
            cat_data["audio"]
        )

        if audio_file is None:

            print(
                f"ERROR: {cat_name} audio not found."
            )

            print(
                f"Expected location: "
                f"{cat_data['audio']}"
            )

            continue

        try:

            sound = pygame.mixer.Sound(
                str(audio_file)
            )

            pet_audio_loaded[cat_name] = sound

            print(
                f"{cat_name} cat audio loaded: "
                f"{audio_file}"
            )

        except Exception as error:

            print(
                f"ERROR loading {cat_name} audio:"
            )

            print(error)


initialize_audio()


# ==================================================
# LOAD GIF
# ==================================================

def load_gif(
    gif_path,
    max_size,
    max_frames=None
):

    gif = Image.open(gif_path)

    frames = []
    durations = []

    for frame in ImageSequence.Iterator(gif):

        frame = frame.convert("RGBA")

        frame.thumbnail(
            (
                max_size,
                max_size
            )
        )

        frames.append(
            frame.copy()
        )

        duration = frame.info.get(
            "duration",
            100
        )

        durations.append(
            max(
                20,
                duration
            )
        )

        if (
            max_frames is not None
            and len(frames) >= max_frames
        ):

            break

    gif.close()

    return frames, durations


# ==================================================
# LOAD NORMAL STICKERS
# ==================================================

for gif_path in STICKER_GIFS:

    if not gif_path.exists():

        print(
            f"Sticker GIF missing: {gif_path}"
        )

        continue

    try:

        frames, durations = load_gif(
            gif_path,
            STICKER_SIZE,
            MAX_STICKER_FRAMES
        )

        photos = [
            ImageTk.PhotoImage(frame)
            for frame in frames
        ]

        loaded_sticker_gifs.append(
            (
                photos,
                durations
            )
        )

        print(
            f"Loaded sticker: {gif_path.name}"
        )

    except Exception as error:

        print(
            f"Could not load sticker "
            f"{gif_path.name}: {error}"
        )


# ==================================================
# LOAD PET CATS
# ==================================================

for cat_name, cat_data in PET_CATS.items():

    gif_path = cat_data["gif"]

    if not gif_path.exists():

        print(
            f"Pet GIF missing: {gif_path}"
        )

        continue

    try:

        frames, durations = load_gif(
            gif_path,
            PET_CAT_SIZE
        )

        photos = [
            ImageTk.PhotoImage(frame)
            for frame in frames
        ]

        loaded_pet_cats[cat_name] = {
            "photos": photos,
            "durations": durations,
        }

        print(
            f"Loaded pet cat: {cat_name}"
        )

    except Exception as error:

        print(
            f"Could not load pet cat "
            f"{cat_name}: {error}"
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

    sticker.attributes(
        "-topmost",
        True
    )

    sticker.configure(
        bg="black"
    )

    try:

        sticker.attributes(
            "-transparentcolor",
            "black"
        )

    except tk.TclError:

        pass

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
# START PET CHALLENGE
# ==================================================

def start_pet_challenge():

    global pet_running
    global pet_window
    global pet_label
    global pet_counter_label
    global pet_count
    global pet_current_cat

    if pet_running:
        return

    if not loaded_pet_cats:

        print("No pet cats were loaded.")

        start_nyan_cat()

        return

    pet_running = True
    pet_count = 0
    pet_current_cat = None

    pet_window = tk.Toplevel(root)

    pet_window.title(
        "Pet the cat"
    )

    pet_window.attributes(
        "-topmost",
        True
    )

    pet_window.resizable(
        False,
        False
    )

    pet_window.configure(
        bg="#202020"
    )

    window_width = 420
    window_height = 430

    screen_width = (
        pet_window.winfo_screenwidth()
    )

    screen_height = (
        pet_window.winfo_screenheight()
    )

    window_x = (
        screen_width - window_width
    ) // 2

    window_y = (
        screen_height - window_height
    ) // 2

    pet_window.geometry(
        f"{window_width}x{window_height}"
        f"+{window_x}+{window_y}"
    )

    title_label = tk.Label(
        pet_window,
        text="pet the cat",
        font=(
            "Arial",
            24,
            "bold"
        ),
        fg="white",
        bg="#202020"
    )

    title_label.pack(
        pady=(
            20,
            5
        )
    )

    pet_counter_label = tk.Label(
        pet_window,
        text=f"Pets: 0/{PETS_REQUIRED}",
        font=(
            "Arial",
            15
        ),
        fg="white",
        bg="#202020"
    )

    pet_counter_label.pack(
        pady=(
            0,
            10
        )
    )

    pet_label = tk.Label(
        pet_window,
        bg="#202020",
        bd=0,
        cursor="hand2"
    )

    pet_label.pack(
        expand=True,
        fill="both",
        padx=20,
        pady=10
    )

    pet_label.bind(
        "<Button-1>",
        pet_cat
    )

    title_label.bind(
        "<Button-1>",
        pet_cat
    )

    pet_window.protocol(
        "WM_DELETE_WINDOW",
        close_pet_window
    )

    show_pet_cat()


# ==================================================
# CLOSE PET WINDOW
# ==================================================

def close_pet_window():

    global pet_running
    global pet_window

    pet_running = False

    if pet_window is not None:

        pet_window.destroy()

    pet_window = None


# ==================================================
# SHOW PET CAT
# ==================================================

def show_pet_cat():

    global pet_current_cat

    if not pet_running:
        return

    available_cats = list(
        loaded_pet_cats.keys()
    )

    if len(available_cats) > 1:

        choices = [
            cat
            for cat in available_cats
            if cat != pet_current_cat
        ]

    else:

        choices = available_cats

    pet_current_cat = random.choice(
        choices
    )

    cat_data = loaded_pet_cats[
        pet_current_cat
    ]

    photos = cat_data["photos"]
    durations = cat_data["durations"]

    sound = pet_audio_loaded.get(
        pet_current_cat
    )

    if sound is not None:

        try:

            sound.play()

        except Exception as error:

            print(
                f"Could not play "
                f"{pet_current_cat} audio: "
                f"{error}"
            )

    def animate(frame_number=0):

        if not pet_running:
            return

        if pet_window is None:
            return

        if not pet_window.winfo_exists():
            return

        pet_label.configure(
            image=photos[frame_number]
        )

        next_frame = (
            frame_number + 1
        ) % len(photos)

        pet_window.after(
            durations[frame_number],
            animate,
            next_frame
        )

    animate()


# ==================================================
# PET CAT
# ==================================================

def pet_cat(event=None):

    global pet_count
    global pet_running

    if not pet_running:
        return

    pet_count += 1

    pet_counter_label.configure(
        text=f"Pets: {pet_count}/{PETS_REQUIRED}"
    )

    if pet_count >= PETS_REQUIRED:

        pet_running = False

        if pet_window is not None:

            pet_window.destroy()

        root.after(
            300,
            start_nyan_cat
        )

    else:

        show_pet_cat()


# ==================================================
# NYAN CAT
# ==================================================

def start_nyan_cat():

    global nyan_running

    if nyan_running:
        return

    nyan_running = True

    if not NYAN_GIF.exists():

        print(
            f"Nyan GIF missing: {NYAN_GIF}"
        )

        nyan_running = False

        return

    try:

        frames, durations = load_gif(
            NYAN_GIF,
            NYAN_SIZE
        )

        nyan_photos = [
            ImageTk.PhotoImage(frame)
            for frame in frames
        ]

    except Exception as error:

        print(
            f"Could not load Nyan GIF: "
            f"{error}"
        )

        nyan_running = False

        return

    if nyan_audio_loaded:

        try:

            pygame.mixer.music.play()

        except Exception as error:

            print(
                f"Could not play Nyan audio: "
                f"{error}"
            )

    overlay = tk.Toplevel(root)

    overlay.overrideredirect(True)

    overlay.attributes(
        "-topmost",
        True
    )

    screen_width = (
        overlay.winfo_screenwidth()
    )

    screen_height = (
        overlay.winfo_screenheight()
    )

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
        "#8a2be2",
    ]

    rainbow_height = 12
    rainbow_width = 45

    def animate_nyan(
        frame_number=0,
        current_x=cat_x,
        rainbow_offset=0
    ):

        global nyan_running

        if not overlay.winfo_exists():

            nyan_running = False

            return

        canvas.delete(
            "rainbow"
        )

        canvas.delete(
            "cat"
        )

        trail_end = (
            current_x + 25
        )

        if trail_end > 0:

            for index, color in enumerate(
                rainbow_colors
            ):

                stripe_y = (
                    cat_y
                    + NYAN_SIZE // 2
                    - (
                        len(rainbow_colors)
                        * rainbow_height
                    ) // 2
                    + index * rainbow_height
                )

                segment_x = (
                    -rainbow_width
                    + rainbow_offset
                )

                while segment_x < trail_end:

                    canvas.create_rectangle(
                        segment_x,
                        stripe_y,
                        min(
                            segment_x
                            + rainbow_width,
                            trail_end
                        ),
                        stripe_y
                        + rainbow_height,
                        fill=color,
                        outline="",
                        tags="rainbow"
                    )

                    segment_x += (
                        rainbow_width * 2
                    )

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

        next_x = (
            current_x + NYAN_SPEED
        )

        next_offset = (
            rainbow_offset + RAINBOW_SPEED
        ) % (
            rainbow_width * 2
        )

        if current_x > screen_width:

            if nyan_audio_loaded:

                try:

                    pygame.mixer.music.stop()

                except Exception:

                    pass

            overlay.destroy()

            nyan_running = False

            return

        overlay.after(
            max(
                20,
                durations[frame_number]
            ),
            animate_nyan,
            next_frame,
            next_x,
            next_offset
        )

    animate_nyan()


# ==================================================
# PROCESS QUEUED EVENTS
# ==================================================

def process_clicks():

    while not click_queue.empty():

        event_type, data = click_queue.get()

        if event_type == "PET":

            start_pet_challenge()

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

def on_click(
    x,
    y,
    button,
    pressed
):

    global click_count

    if not pressed:
        return

    if nyan_running or pet_running:
        return

    click_count += 1

    print(
        f"Click count: {click_count}"
    )

    if click_count >= CLICK_LIMIT:

        click_count = 0

        click_queue.put(
            (
                "PET",
                None
            )
        )

    else:

        click_queue.put(
            (
                "CLICK",
                (
                    x,
                    y
                )
            )
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