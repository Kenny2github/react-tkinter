from __future__ import annotations
from typing import Any, Optional
import tkinter as tk
from . import elements
from .react_parser import parse

def react(root: tk.Tk, text: str, globs: Optional[dict[str, Any]] = None,
          locs: Optional[dict[str, Any]] = None) -> elements.Root:
    elem = parse(text, globs or globals(), locs or locals())
    return elements.Root(root, elem)