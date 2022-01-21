"""
Adapted from http://tkdocs.com/tutorial/firstexample.html
"""
import tkinter as tk
from tkinter import ttk

def converter(from_var: tk.StringVar, to_var: tk.StringVar):
    def wrapper(func):
        def convert(*args):
            try:
                value = from_var.get()
                to_var.set(func(value))
            except ValueError:
                pass
        return convert
    return wrapper

root = tk.Tk()
root.title('Feet to Meters')

main_frame = ttk.Frame(root, padding='3 3 12 12')
main_frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

feet = tk.StringVar()
feet_entry = ttk.Entry(main_frame, width=10, textvariable=feet)
feet_entry.grid(column=2, row=1, sticky=(tk.W, tk.E))

meters = tk.StringVar()
ttk.Label(main_frame, textvariable=meters).grid(column=2, row=2, sticky=(tk.W, tk.E))

@converter(feet, meters)
def feet_to_meters(value: str):
    return int(0.3048 * float(value) * 10000.0 + 0.5) / 10000.0

ttk.Button(main_frame, text='Convert', command=feet_to_meters).grid(column=3, row=3, sticky=tk.W)

ttk.Label(main_frame, text='feet').grid(column=3, row=1, sticky=tk.W)
ttk.Label(main_frame, text='is equivalent to').grid(column=1, row=2, sticky=tk.E)
ttk.Label(main_frame, text='meters').grid(column=3, row=2, sticky=tk.W)

for child in main_frame.winfo_children():
    child.grid_configure(padx=5, pady=5)

feet_entry.focus()
root.bind('<Return>', feet_to_meters)

root.mainloop()
