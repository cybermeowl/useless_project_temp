import tkinter as tk

window = tk.Tk()
window.title("memeify")
window.geometry("500x300")

label = tk.Label(
    window,
    text="gatto ahhhh",
    font=("Arial", 20)
)
label.pack(expand=True)

window.mainloop()