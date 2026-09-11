import tkinter as tk
from PIL import Image, ImageTk
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

PET_FOLDER = BASE_FOLDER / "pet_the_car"

STICKER_GIFS = [
    BASE_FOLDER / "bop_cat.gif",
    BASE_FOLDER / "scuba_cat.gif",
    BASE_FOLDER / "jumping_cat.gif",
]

NYAN_GIF = BASE_FOLDER / "nyan_cat.gif"

NYAN_AUDIO = AUDIO_FOLDER / "nyan_audio"
YAY_AUDIO = AUDIO_FOLDER / "yay_audio"
NPC_AUDIO = AUDIO_FOLDER / "npc_audio"
MEOWMER_IMAGE = PET_FOLDER / "meowmer.png"

STICKER_AUDIO = {
    "bop_cat.gif": AUDIO_FOLDER / "bop_cat_audio.mp3",
    "scuba_cat.gif": AUDIO_FOLDER / "scuba_cat_audio.mp3",
    "jumping_cat.gif": AUDIO_FOLDER / "chipi_chip_chapa_chapa_audio.mp3",
}


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

pet_window = None
pet_label = None
pet_counter_label = None

pet_count = 0
pet_current_cat = None

# This number cancels old pet animations.
pet_animation_id = 0

nyan_audio_loaded = False
nyan_audio_file_loaded = None
yay_audio_loaded = False
meowmer_photo = None

loaded_sticker_gifs = []
loaded_pet_cats = {}

sticker_audio_loaded = {}
pet_audio_loaded = {}
npc_audio_loaded = None


# ==================================================
# AUDIO HELPERS
# ==================================================

def stop_all_audio():
    """
    Stop every sound and music channel.
    This prevents audio from clashing with Nyan Cat.
    """

    try:
        pygame.mixer.stop()
    except Exception:
        pass

    try:
        pygame.mixer.music.stop()
    except Exception:
        pass


def find_audio_file(path):
    if path is None:
        return None

    possible_files = [
        path,
        path.with_suffix(".mp3"),
        path.with_suffix(".wav"),
        path.with_suffix(".ogg"),
    ]

    for file_path in possible_files:
        if file_path.is_file():
            return file_path

    # Windows may hide extensions, and downloaded files sometimes have
    # slightly different names. Try a case-insensitive stem match too.
    if path.parent.exists():
        wanted = path.stem.lower()
        for file_path in path.parent.iterdir():
            if (
                file_path.is_file()
                and file_path.suffix.lower() in {".mp3", ".wav", ".ogg"}
                and file_path.stem.lower() == wanted
            ):
                return file_path

    return None


# ==================================================
# PET FILE DISCOVERY
# ==================================================

def discover_pet_cats():
    pet_cats = {}

    supported_extensions = {
        ".gif",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }

    if not PET_FOLDER.exists():
        print("Pet-the-car folder was not found:")
        print(PET_FOLDER)
        return pet_cats

    for pet_file in sorted(PET_FOLDER.iterdir()):
        if (
            pet_file.is_file()
            and pet_file.suffix.lower() in supported_extensions
            and pet_file.stem.lower() != "meowmer"
        ):
            pet_cats[pet_file.stem] = {
                "gif": pet_file,
                "audio": None,
            }

    return pet_cats


PET_CATS = discover_pet_cats()


# ==================================================
# AUDIO INITIALIZATION
# ==================================================

def initialize_audio():
    global nyan_audio_loaded, nyan_audio_file_loaded, yay_audio_loaded, npc_audio_loaded

    try:
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)

        print("Pygame audio initialized.")

    except Exception as error:
        print("Could not initialize pygame audio:")
        print(error)
        return

    # Normal sticker sounds
    for gif_path in STICKER_GIFS:
        audio_path = STICKER_AUDIO.get(
            gif_path.name
        )

        audio_file = find_audio_file(
            audio_path
        )

        if audio_file is None:
            print(
                f"No audio found for {gif_path.name}"
            )
            continue

        try:
            sound = pygame.mixer.Sound(
                str(audio_file)
            )

            sound.set_volume(1.0)

            sticker_audio_loaded[
                gif_path.name
            ] = sound

            print(
                f"Loaded sticker audio: "
                f"{audio_file.name}"
            )

        except Exception as error:
            print(
                f"Could not load sticker audio "
                f"for {gif_path.name}: {error}"
            )

    # Nyan Cat music
    nyan_audio_file = find_audio_file(
        NYAN_AUDIO
    )

    if nyan_audio_file is not None:
        try:
            pygame.mixer.music.load(
                str(nyan_audio_file)
            )

            nyan_audio_file_loaded = nyan_audio_file
            nyan_audio_loaded = True

            print(
                f"Loaded Nyan audio: "
                f"{nyan_audio_file.name}"
            )

        except Exception as error:
            print(
                f"Could not load Nyan audio: {error}"
            )

    # Meowmer audio
    yay_audio_file = find_audio_file(YAY_AUDIO)
    if yay_audio_file is not None:
        yay_audio_loaded = True
        print(f"Found yay audio: {yay_audio_file.name}")
    else:
        print("Yay audio not found.")

    # NPC audio plays continuously during the seven-cat challenge.
    npc_audio_file = find_audio_file(NPC_AUDIO)
    if npc_audio_file is not None:
        try:
            npc_audio_loaded = pygame.mixer.Sound(str(npc_audio_file))
            npc_audio_loaded.set_volume(1.0)
            print(f"Loaded NPC audio: {npc_audio_file.name}")
        except Exception as error:
            print(f"Could not load NPC audio: {error}")
    else:
        print("NPC audio not found.")

    # Pet audio is optional.
    for pet_name in PET_CATS:
        pet_audio_loaded[pet_name] = None
        audio_file = find_audio_file(AUDIO_FOLDER / f"{pet_name}_audio")
        if audio_file is not None:
            try:
                pet_audio_loaded[pet_name] = pygame.mixer.Sound(str(audio_file))
                print(f"Loaded pet audio: {audio_file.name}")
            except Exception as error:
                print(f"Could not load pet audio for {pet_name}: {error}")


initialize_audio()


# ==================================================
# IMAGE/GIF LOADING
# ==================================================

def load_gif(
    file_path,
    max_size,
    max_frames=None
):
    image = Image.open(file_path)

    frames = []
    durations = []

    frame_count = getattr(
        image,
        "n_frames",
        1
    )

    for frame_index in range(frame_count):
        try:
            image.seek(frame_index)
        except EOFError:
            break

        frame = image.convert("RGBA")

        frame.thumbnail(
            (
                max_size,
                max_size
            )
        )

        frames.append(
            frame.copy()
        )

        duration = image.info.get(
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

    image.close()

    return frames, durations


# ==================================================
# LOAD NORMAL STICKERS
# ==================================================

for gif_path in STICKER_GIFS:
    if not gif_path.exists():
        print(
            f"Sticker file missing: {gif_path}"
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
            {
                "photos": photos,
                "durations": durations,
                "sound": sticker_audio_loaded.get(
                    gif_path.name
                ),
                "name": gif_path.name,
            }
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
# LOAD PET-THE-CAR IMAGES
# ==================================================

for pet_name, pet_data in PET_CATS.items():
    file_path = pet_data["gif"]

    try:
        frames, durations = load_gif(
            file_path,
            PET_CAT_SIZE
        )

        photos = [
            ImageTk.PhotoImage(frame)
            for frame in frames
        ]

        loaded_pet_cats[pet_name] = {
            "photos": photos,
            "durations": durations,
        }

        print(
            f"Loaded pet image: {file_path.name}"
        )

    except Exception as error:
        print(
            f"Could not load pet image "
            f"{file_path.name}: {error}"
        )


print(
    f"Loaded {len(loaded_pet_cats)} "
    f"pet images."
)


# ==================================================
# NORMAL STICKER SPAWNING
# ==================================================

def spawn_sticker(x, y):
    if not loaded_sticker_gifs:
        return

    sticker_data = random.choice(
        loaded_sticker_gifs
    )

    photos = sticker_data["photos"]
    durations = sticker_data["durations"]
    sound = sticker_data["sound"]

    if sound is not None:
        try:
            sound.play()
        except Exception as error:
            print(
                f"Could not play sticker sound: "
                f"{error}"
            )

    sticker = tk.Toplevel(root)

    sticker.overrideredirect(True)
    sticker.attributes("-topmost", True)
    sticker.configure(bg="black")

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
        f"{STICKER_SIZE}x{STICKER_SIZE}"
        f"+{x}+{y}"
    )

    def animate(frame_number=0):
        if not sticker.winfo_exists():
            return

        label.configure(
            image=photos[frame_number]
        )

        label.image = photos[frame_number]

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
# PET CHALLENGE
# ==================================================

def start_pet_challenge():
    global pet_running
    global pet_window
    global pet_label
    global pet_counter_label
    global pet_count
    global pet_current_cat
    global pet_animation_id

    if pet_running:
        return

    if not loaded_pet_cats:
        print(
            "No images found in pet_the_car."
        )
        return

    pet_running = True
    pet_count = 0
    pet_current_cat = None

    # Stop any normal sticker sounds, then start the NPC sound for
    # the entire seven-pet challenge.
    stop_all_audio()
    if npc_audio_loaded is not None:
        try:
            npc_audio_loaded.play(loops=-1)
        except Exception as error:
            print(f"Could not play NPC audio: {error}")

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
        text="Pets: 0/7",
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
    global pet_animation_id

    pet_running = False

    # Invalidate the old animation.
    pet_animation_id += 1

    if pet_window is not None:
        try:
            pet_window.destroy()
        except tk.TclError:
            pass

    pet_window = None


# ==================================================
# SHOW ONE PET IMAGE
# ==================================================

def show_pet_cat():
    global pet_current_cat
    global pet_animation_id

    if not pet_running:
        return

    if pet_window is None:
        return

    available_cats = list(
        loaded_pet_cats.keys()
    )

    if not available_cats:
        return

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

    # Cancel every previous pet animation.
    pet_animation_id += 1

    current_animation_id = (
        pet_animation_id
    )

    def animate(frame_number=0):
        if not pet_running:
            return

        if pet_window is None:
            return

        if not pet_window.winfo_exists():
            return

        # Ignore callbacks belonging to old cats.
        if current_animation_id != pet_animation_id:
            return

        pet_label.configure(
            image=photos[frame_number]
        )

        pet_label.image = photos[frame_number]

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
# PET CLICK
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
            try:
                pet_window.destroy()
            except tk.TclError:
                pass

        # Make absolutely sure no previous audio remains.
        stop_all_audio()

        root.after(
            300,
            start_meowmer_screen
        )

    else:
        # Show exactly one new pet image.
        show_pet_cat()


# ==================================================
# MEOWMER SCREEN
# ==================================================

def start_meowmer_screen():
    global meowmer_photo

    stop_all_audio()

    if not MEOWMER_IMAGE.exists():
        print(f"Meowmer image missing: {MEOWMER_IMAGE}")
        root.after(300, start_nyan_cat)
        return

    try:
        image = Image.open(MEOWMER_IMAGE).convert("RGBA")
        image.thumbnail((600, 600))
        meowmer_photo = ImageTk.PhotoImage(image)
    except Exception as error:
        print(f"Could not load meowmer image: {error}")
        root.after(300, start_nyan_cat)
        return

    window = tk.Toplevel(root)
    window.title("Meowmer")
    window.attributes("-topmost", True)
    window.configure(bg="#202020")
    window.resizable(False, False)

    label = tk.Label(
        window, image=meowmer_photo,
        bg="#202020",
        padx=20, pady=20
    )
    label.pack()

    window.update_idletasks()
    x = (window.winfo_screenwidth() - window.winfo_width()) // 2
    y = (window.winfo_screenheight() - window.winfo_height()) // 2
    window.geometry(f"+{x}+{y}")

    yay_file = find_audio_file(YAY_AUDIO)
    if yay_file is not None:
        try:
            pygame.mixer.music.load(str(yay_file))
            pygame.mixer.music.play()
        except Exception as error:
            print(f"Could not play yay audio: {error}")

    def finish():
        stop_all_audio()
        try:
            window.destroy()
        except tk.TclError:
            pass
        root.after(200, start_nyan_cat)

    window.after(2500, finish)


# ==================================================
# NYAN CAT
# ==================================================

def start_nyan_cat():
    global nyan_running

    if nyan_running:
        return

    # Stop every audio source before Nyan appears.
    stop_all_audio()

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
            f"Could not load Nyan GIF: {error}"
        )

        nyan_running = False
        return

    if nyan_audio_loaded:
        try:
            # The Meowmer screen uses pygame.mixer.music for yay_audio,
            # so reload Nyan here before starting it.
            pygame.mixer.music.load(str(nyan_audio_file_loaded))
            pygame.mixer.music.play()
        except Exception as error:
            print(
                f"Could not play Nyan audio: "
                f"{error}"
            )

    overlay = tk.Toplevel(root)

    overlay.overrideredirect(True)
    overlay.attributes("-topmost", True)

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
            return

        canvas.delete("rainbow")
        canvas.delete("cat")

        trail_end = current_x + 25

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
            stop_all_audio()

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
# EVENT PROCESSING
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
# MOUSE LISTENER
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