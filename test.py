"""
Reactified tkintertest.py
"""
import tkinter as tk
from tkinter import ttk
from react_tkinter import react
from react_tkinter.elements import Reference

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

feet = tk.StringVar()
meters = tk.StringVar()
feet_entry = Reference

@converter(feet, meters)
def feet_to_meters(value: str):
    return int(0.3048 * float(value) * 10000.0 + 0.5) / 10000.0

root_element = react(root, """
<Root padding="3 3 12 12" grid sticky="N W E S">
	<Row><Empty/><Input var={feet} width={10} sticky="W E" ref={feet_entry}/><Label sticky="W">feet</Label></Row>
	<Row><Label sticky="E">is equivalent to</Label><Label sticky="W E">{meters}</Label><Label sticky="W">meters</Label></Row>
	<Row><Empty/><Empty/><Button command={feet_to_meters} sticky="W">Convert</Button></Row>
</Root>
""", globals(), locals())

main_frame: ttk.Frame = root_element.tkobj

for child in main_frame.winfo_children():
    child.grid_configure(padx=5, pady=5)

feet_entry.current.tkobj.focus()
root.bind('<Return>', feet_to_meters)

root.mainloop()
