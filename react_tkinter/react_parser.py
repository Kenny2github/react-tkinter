from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional
from html import unescape, escape

__all__ = ['parse', 'Element']

@dataclass
class _Element: # for closing tags
    name: str

@dataclass
class Element(_Element):
    name: str
    attrs: dict[str, Any]
    children: Optional[list[Element]] = None
    content: Optional[Any] = None
    parent: Optional[Element] = None

    def __str__(self) -> str:
        attrs: list[str] = []
        for attr, value in self.attrs.items():
            if isinstance(value, str):
                attrs.append(f'{attr}="{escape(value)}"')
            elif value is True:
                attrs.append(attr)
            else:
                attrs.append(f'{attr}={{{value!r}}}')
        if attrs:
            str_attrs = ' ' + ' '.join(attrs)
        else:
            str_attrs = ''
        if self.children:
            content = '\n' + '\n'.join(map(str, self.children)) + '\n'
        elif self.content is not None:
            if isinstance(self.content, str):
                content = escape(self.content)
            else:
                content = '{' + repr(self.content) + '}'
        else:
            return f'<{self.name}{str_attrs} />'
        return f'<{self.name}{str_attrs}>{content}</{self.name}>'

if TYPE_CHECKING:
    _Scope = tuple[dict[str, Any], dict[str, Any]]

def skip_ws(text: str, start: int = 0) -> int:
    while start < len(text) and text[start].isspace():
        start += 1
    return start

def jump_to_ws(text: str, start: int = 0) -> int:
    while start < len(text) and not text[start].isspace():
        start += 1
    return start

def parse_expr(text: str, scope: _Scope, start: int = 0
               ) -> tuple[int, Any]:
    # assumes just after {
    stack = 0
    end = start
    quote: Optional[str] = None
    while (
        end < len(text)
        and (stack > 0 or text[end] != '}')
    ):
        if text[end] == quote: # when quote is None this is always false
            if text[end-1] == '\\': # ignore quote escaping
                pass
            else: # reached close quote
                quote = None
        elif text[end] in "'\"":
            quote = text[end]
        elif text[end] == '{':
            stack += 1
        elif text[end] == '}':
            stack -= 1
        end += 1
    if not (end < len(text)):
        raise ValueError(f'attr value at char {start} left unclosed')
    # don't unescape, because python strings have different escaping
    value = eval(text[start:end], *scope)
    return end + 1, value # just after }

def parse_attr(text: str, scope: _Scope, start: int = 0) -> tuple[
    # new start, name, value
    int, Optional[str], Any
]:
    end = start
    while (
        end < len(text)
        and text[end] not in '>='
        and not text[end].isspace()
    ):
        end += 1
    if not (end < len(text)):
        raise ValueError(f'tag at char {start} left unclosed')
    name = text[start:end]
    if text[end] == '>' or text[end].isspace():
        # premature end of attribute name,
        # e.g. <tag attr>
        return end, name, True
    # text[end] == '='
    start = end = end + 1 # just after =
    if text[end] == '"':
        # quoted value
        start = end = end + 1 # just after "
        while end < len(text) and text[end] != '"':
            end += 1
        if not (end < len(text)):
            raise ValueError(f'attr value at char {start} left unclosed')
        return end + 1, name, unescape(text[start:end])
    if text[end] == '{':
        end, value = parse_expr(text, scope, end + 1) # just after { then }
        return end, name, value
    # assume unquoted string value
    while end < len(text) and text[end] != '>' and not text[end].isspace():
        end += 1
    return end, name, unescape(text[start:end])

def parse_elem(text: str, scope: _Scope, start: int = 0) -> tuple[int, _Element]:
    # assumes start is just after <
    end = start
    if text[start] == '/':
        start = end = end + 1 # just after /
        while end < len(text) and text[end] != '>':
            end += 1
        if not (end < len(text)):
            raise ValueError(f'closing tag at char {start} left unclosed')
        return end + 1, _Element(text[start:end]) # just after >
    while (
        end < len(text)
        and text[end] not in '/>'
        and not text[end].isspace()
    ):
        end += 1
    if not (end < len(text)):
        raise ValueError(f'opening tag at char {start} left unclosed')
    name = text[start:end]
    end = skip_ws(text, end)
    attrs: dict[str, Any] = {}
    while end < len(text) and text[end] not in '/>':
        end, attr, value = parse_attr(text, scope, end)
        if attr: # attr="value" > can produce empty attr names
            attrs[attr] = value
        end = skip_ws(text, end)
    if not (end < len(text)):
        raise ValueError(f'opening tag at char {start} left unclosed')
    if text[end] == '/':
        end = skip_ws(text, end + 1)
        if not (end < len(text)):
            raise ValueError(f'self-closing tag at char {start} not closed')
        if text[end] != '>':
            raise ValueError(f'illegal / in self-closing tag at char {start}')
        return end + 1, Element(name, attrs) # just after >
    start = end = end + 1 # just after >
    end = skip_ws(text, end)
    if not (end < len(text)):
        raise ValueError(f'tag at char {start} left unclosed')
    if text[end] == '<':
        # mode set to children only
        children: list[Element] = []
        result = Element(name, attrs, children)
        while 1:
            start = end = end + 1 # just after <
            end, elem = parse_elem(text, scope, start) # just after >
            if not isinstance(elem, Element):
                if elem.name == name:
                    break
                raise ValueError(f'unexpected closing {elem.name!r} tag')
            elem.parent = result
            children.append(elem)
            end = skip_ws(text, end)
            if text[end] != '<':
                raise ValueError(f'unexpected {text[end]!r} at char {end}')
        return end, result # just after >
    elif text[end] == '{':
        end, content = parse_expr(text, scope, end + 1) # just after { then }
        end = skip_ws(text, end)
        if not (end < len(text)) or text[end] != '<':
            raise ValueError(f'{name!r} tag at char {start} left unclosed')
        end, elem = parse_elem(text, scope, end + 1) # just after < then >
        if isinstance(elem, Element) or elem.name != name:
            raise ValueError(f'unexpected {elem.name!r} tag')
        return end, Element(name, attrs, content=content) # just after >
    else: # just after >
        while end < len(text) and text[end] != '<':
            end += 1
        if not (end < len(text)) or text[end] != '<':
            raise ValueError(f'{name!r} tag at char {start} left unclosed')
        content = unescape(text[start:end])
        end, elem = parse_elem(text, scope, end + 1) # just after < then >
        if isinstance(elem, Element) or elem.name != name:
            raise ValueError(f'unexpected {elem.name!r} tag')
        return end, Element(name, attrs, content=content) # just after >

def parse(text: str, globs: dict[str, Any], locs: dict[str, Any]) -> Element:
    text = text.strip()
    if text[0] != '<':
        raise ValueError('malformed string from onset')
    _, elem = parse_elem(text, (globs, locs), 1)
    if not isinstance(elem, Element):
        raise ValueError(f'unexpected closing {elem.name!r} tag')
    return elem

if __name__ == '__main__':
    var = 1
    root = parse(
        """
<hi hello={var + 1}>
    <how are="you">are</how>
    <you />
    <doing>{var - 1}</doing>
</hi>""",
        globals(), locals())
    print(root)
