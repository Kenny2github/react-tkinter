from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union
import tkinter as tk
from tkinter import ttk
from .react_parser import Element as _Element

def stickies(attr: str) -> tuple[str, ...]:
    return tuple(
        getattr(tk, s, s) for s in attr.split())

@dataclass
class Reference:
    current: Optional[Element]

class Element:
    children: list[Element]
    tkobj: tk.Grid

    def __init__(self, parent: Element, elem: _Element) -> None:
        self.parent = parent
        self.elem = elem
        if 'ref' in elem.attrs:
            elem.attrs['ref'].current = self
        self.children = []

    def __repr__(self) -> str:
        return repr(self.elem)

    @property
    def root(self) -> ttk.Frame:
        return self.parent.root

class Root(Element):

    def __init__(self, root: tk.Tk, elem: _Element) -> None:
        kwargs = {}
        if 'padding' in elem.attrs:
            kwargs['padding'] = elem.attrs['padding']
        self.tkobj = ttk.Frame(root, **kwargs)
        gridded = elem.attrs.get('grid', False)
        if gridded:
            self.tkobj.grid(column=0, row=0, sticky=stickies(
                elem.attrs['sticky']))
            root.columnconfigure(0, weight=1)
            root.rowconfigure(0, weight=1)
        super().__init__(None, elem)
        for i, child in enumerate(elem.children or [], start=1):
            if child.name == 'Row' and 'index' not in child.attrs:
                child.attrs['index'] = i
            self.children.append(ELEMENTS[child.name](self, child))

    @property
    def root(self) -> ttk.Frame:
        return self.tkobj

class Row(Element):

    def __init__(self, parent: Element, elem: _Element) -> None:
        super().__init__(parent, elem)
        for i, child in enumerate(elem.children or []):
            self.children.append(ELEMENTS[child.name](self, child))
            kwargs = {'column': i, 'row': elem.attrs['index']}
            if 'sticky' in child.attrs:
                kwargs['sticky'] = stickies(child.attrs['sticky'])
            self.children[-1].tkobj.grid(**kwargs)

class Empty(Element):
    class tkobj:
        def grid(*args, **kwargs):
            pass

class Input(Element):
    var: tk.StringVar

    def __init__(self, root: ttk.Frame, elem: _Element) -> None:
        super().__init__(root, elem)
        self.var = elem.attrs.get('var', tk.StringVar())
        kwargs = {}
        if 'width' in elem.attrs:
            kwargs['width'] = int(elem.attrs['width'])
        if 'height' in elem.attrs:
            kwargs['height'] = int(elem.attrs['height'])
        kwargs['textvariable'] = self.var
        self.tkobj = ttk.Entry(self.root, **kwargs)

    @property
    def value(self) -> str:
        return self.var.get()

class Label(Element):
    def __init__(self, parent: Element, elem: _Element) -> None:
        super().__init__(parent, elem)
        text: Union[str, tk.StringVar] = elem.content or tk.StringVar()
        if isinstance(text, str):
            self.tkobj = ttk.Label(self.root, text=text)
        else:
            self.tkobj = ttk.Label(self.root, textvariable=text)

class Button(Element):
    def __init__(self, parent: Element, elem: _Element) -> None:
        super().__init__(parent, elem)
        command = elem.attrs['command']
        self.tkobj = ttk.Button(self.root, text=elem.content, command=command)

ELEMENTS = {cls.__name__: cls for cls in Element.__subclasses__()}
