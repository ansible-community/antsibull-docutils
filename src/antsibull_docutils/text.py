# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026, Ansible Project

"""
Code for conversion to (formatted) plain text.
"""

from __future__ import annotations

import abc
import io
import math
import typing as t

from docutils import nodes, writers
from docutils.core import publish_parts

from ._collector import ANSIState as _ANSIState
from ._collector import Collector as _Collector
from ._collector import EmptyState as _EmptyState
from ._collector import Formatting as _Formatting
from ._collector import State as _State
from ._string import StringProcessor as _StringProcessor
from ._string import UnicodeStringProcessor as _UnicodeStringProcessor
from ._table import Cell as _Cell
from ._table import TableHelper as _TableHelper
from ._utils import ContextBase as _ContextBase
from ._utils import DocumentContextBase as _DocumentContextBase
from ._utils import add_skip as _add_skip
from ._utils import add_unsupported_classes as _add_unsupported_classes
from .utils import (
    _PARSER_NAME_ARG,
    RenderResult,
    SupportedParser,
    get_docutils_publish_settings,
)

_Class = t.TypeVar("_Class")


class GlobalContext:  # pylint: disable=too-few-public-methods
    """
    The global conversion context.
    """

    title_headings: str = """═━─┉┅┈┄-~.+`'"_"""
    column_width: int = 80
    use_ansi_formatting: bool = True


class Context(_ContextBase["Context"]):  # pylint: disable=too-many-instance-attributes
    """
    Base context class for text conversion.
    """

    def __init__(
        self,
        *,
        remaining_width: int,
        state: _State,
        string_proc: _StringProcessor,
        has_top: bool = False,
        ignore_newlines: bool = True,
    ) -> None:
        self.remaining_width = remaining_width
        self.top_state = state.clone()
        self.state = state.clone()
        self.string_proc = string_proc
        self._has_top = has_top
        self._top = _Collector(
            width=self.remaining_width,
            state=self.top_state,
            string_proc=self.string_proc,
            ignore_newlines=ignore_newlines,
        )
        self._main = _Collector(
            width=self.remaining_width,
            state=self.state,
            string_proc=self.string_proc,
            ignore_newlines=ignore_newlines,
        )
        self._result_top: list[str] | None = None
        self._result_main: list[str] | None = None

    @property
    def top(self) -> _Collector:
        """
        Get hold of top collector.
        """
        if not self._has_top:
            raise ValueError("Context has no top part")
        return self._top

    @property
    def main(self) -> _Collector:
        """
        Get hold of main collector.
        """
        return self._main

    def append(
        self,
        context: Context,
    ) -> None:
        """
        Append another context to this context.
        """
        # pylint: disable-next=protected-access
        if context._result_top is None or context._result_main is None:
            raise ValueError("Context is not closed!")
        if context._has_top:  # pylint: disable=protected-access
            if not self._has_top:
                raise ValueError("Context has no top part")
            self._top.add_raw_lines(
                context._result_top  # pylint: disable=protected-access
            )
        self._main.add_raw_lines(
            context._result_main  # pylint: disable=protected-access
        )

    def close(self) -> None:
        """
        Close the context.

        Should be called before using its value / content, for example by
        passing it to ``append()`` or calling ``get_text()``.
        """
        if self._result_main is not None or self._result_top is not None:
            raise ValueError("Context is already closed!")
        self._result_top = self._top.close()
        self._result_main = self._main.close()

    def get_lines(self) -> list[str]:
        """
        Return the content of the context as a list of lines.
        """
        if self._result_main is None or self._result_top is None:
            raise ValueError("Context is not closed!")
        return self._result_top + self._result_main

    def get_text(self) -> str:
        """
        Return the content of the context as a string.
        """
        return "\n".join(self.get_lines())


class IndentContext(Context):
    """
    Context for things to be indented.
    """

    def __init__(
        self,
        *,
        first_indent: str,
        next_indent: str | None = None,
        remaining_width: int,
        state: _State,
        string_proc: _StringProcessor,
        at_least_one_line: bool = False,
        ignore_newlines: bool = True,
    ):
        indent_columns = string_proc.get_column_count(text=first_indent)
        super().__init__(
            remaining_width=remaining_width - indent_columns,
            state=state,
            string_proc=string_proc,
            ignore_newlines=ignore_newlines,
        )
        self.first_indent = first_indent
        self.next_indent = " " * indent_columns if next_indent is None else next_indent
        self.at_least_one_line = at_least_one_line

    def close(self) -> None:
        super().close()
        assert self._result_main is not None
        _indent(
            self._result_main,
            first_indent=self.first_indent,
            next_indent=self.next_indent,
        )
        if self.at_least_one_line and not self._result_main:
            self._result_main.append(self.first_indent.rstrip())


class _Enumerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_maximal_length(self) -> int:
        """
        Return the maximum indentation length.
        """

    @abc.abstractmethod
    def get_next_first_indent(self) -> str:
        """
        Generates a new first indent.
        Must be called exactly as many times as defined.
        """


class _ConstEnumerator(_Enumerator):
    def __init__(self, *, prefix: str, string_proc: _StringProcessor) -> None:
        self.prefix = prefix
        self.string_proc = string_proc

    def get_maximal_length(self) -> int:
        """
        Return the maximum indentation length.
        """
        return self.string_proc.get_column_count(text=self.prefix)

    def get_next_first_indent(self) -> str:
        """
        Generates a new first indent.
        Must be called exactly as many times as defined.
        """
        return self.prefix


def _arabic(index: int) -> str:
    return f"{index + 1}. "


class _VariableEnumerator(_Enumerator):
    def __init__(
        self,
        *,
        generator: t.Callable[[int], str],
        count: int,
        string_proc: _StringProcessor,
    ) -> None:
        self.index = 0
        self.prefixes = [generator(i) for i in range(count)]
        self.max_length = (
            max(string_proc.get_column_count(text=elt) for elt in self.prefixes)
            if self.prefixes
            else 0
        )

    def get_maximal_length(self) -> int:
        """
        Return the maximum indentation length.
        """
        return self.max_length

    def get_next_first_indent(self) -> str:
        """
        Generates a new first indent.
        Must be called exactly as many times as defined.
        """
        index = self.index
        self.index += 1
        return self.prefixes[index]


class ListContext(Context):
    """
    Context for lists (enumeration, bullet list).
    """

    def __init__(
        self,
        *,
        enumerator: _Enumerator,
        remaining_width: int,
        state: _State,
        string_proc: _StringProcessor,
    ):
        max_length = enumerator.get_maximal_length()
        super().__init__(
            remaining_width=remaining_width - max_length,
            state=state,
            string_proc=string_proc,
        )
        self.enumerator = enumerator
        self.max_length = max_length

    def get_next_item_indents(self) -> tuple[str, str]:
        """
        Retrieve the ``(first_indent, next_indent)`` pair for the next list item.
        """
        first_indent = self.enumerator.get_next_first_indent()
        indent_length = self.string_proc.get_column_count(text=first_indent)
        if indent_length > self.max_length:
            raise RuntimeError(  # pragma: no cover
                f"Expected a maximum indent column count of {self.max_length},"
                f" but got {first_indent!r} of column count {indent_length}"
            )
        return (
            first_indent + " " * (self.max_length - indent_length),
            " " * self.max_length,
        )


class DocumentContext(_DocumentContextBase[GlobalContext, Context]):
    """
    Conversion context for a document.
    """

    def __init__(self, global_context: GlobalContext) -> None:
        super().__init__(global_context)
        state = _ANSIState() if global_context.use_ansi_formatting else _EmptyState()
        string_proc = _UnicodeStringProcessor()
        self._contexts.append(
            Context(
                has_top=True,
                remaining_width=global_context.column_width,
                state=state,
                string_proc=string_proc,
            )
        )


def _indent(lines: list[str], *, first_indent: str, next_indent: str) -> None:
    while lines and lines[0] == "":
        del lines[0]
    while lines and lines[-1] == "":
        del lines[-1]
    for i, line in enumerate(lines):
        if i == 0:
            lines[i] = f"{first_indent}{line}".rstrip(" ")
        else:
            lines[i] = f"{next_indent}{line}".rstrip(" ")


class _TableRenderer:  # pylint: disable=too-many-instance-attributes,too-few-public-methods
    def __init__(
        self, *, table: nodes.table, destination: Context, visitor: _Translator
    ) -> None:
        self.table = table
        self.destination = destination
        self.visitor = visitor
        helper = _TableHelper(table=table)
        self.title = helper.title
        self.col_specs = helper.col_specs
        self.row_matrix = helper.row_matrix
        self.cells = helper.cells
        self.header_rows = helper.header_rows
        self._horizontal_padding = 1
        self._vertical_padding = 0

    def _get_maximum_column_widths(self) -> list[int]:
        # TODO: use values in self.col_specs
        cols = len(self.col_specs)
        frame_width = cols * (1 + 2 * self._horizontal_padding) + 1
        max_content_width = self.destination.remaining_width - frame_width
        w = max(1, max_content_width // cols) if cols else 1
        return [w] * cols

    def _prerender_cell(self, *, cell: _Cell, max_col_widths: list[int]) -> int:
        # Compute max width
        width = 0
        for col in range(cell.begin_col, cell.end_col + 1):
            width += max_col_widths[col]
        width += (cell.end_col - cell.begin_col) * (1 + 2 * self._horizontal_padding)

        # Compute content lines
        top = Context(
            remaining_width=width,
            state=self.destination.state.clone(),
            string_proc=self.destination.string_proc,
            ignore_newlines=True,
        )
        # pylint: disable-next=protected-access
        with self.visitor._context.with_fake_top(fake_top=top):
            cell.entry.walkabout(self.visitor)
        top.close()

        # Add content lines
        padding = " " * self._horizontal_padding
        for _ in range(self._vertical_padding):
            cell.lines.append(padding * 2)
        for line in top.get_lines():
            cell.lines.append(f"{padding}{line}{padding}")
        for _ in range(self._vertical_padding):
            cell.lines.append(padding * 2)

        # Compute maximum width
        return (
            max(
                self.destination.string_proc.get_column_count(text=line)
                for line in cell.lines
            )
            if cell.lines
            else 0
        )

    def _prerender_title(self, *, max_width: int) -> list[str]:
        if self.title is None:
            return []

        # Compute content lines
        top = Context(
            remaining_width=max_width,
            state=self.destination.state.clone(),
            string_proc=self.destination.string_proc,
            ignore_newlines=True,
        )
        # pylint: disable-next=protected-access
        with self.visitor._context.with_fake_top(fake_top=top):
            for node in self.title:
                node.walkabout(self.visitor)
        top.close()

        return top.get_lines()

    def _position_cols(self, *, act_col_widths: list[int]) -> list[int]:
        result = [0] * (len(act_col_widths) + 1)
        for col, width in enumerate(act_col_widths):
            result[col + 1] = result[col] + 1 + max(width, 2 * self._horizontal_padding)
        return result

    def _position_rows(self) -> list[int]:
        result = [0] * (len(self.row_matrix) + 1)
        for row_idx, row in enumerate(self.row_matrix):
            result[row_idx + 1] = result[row_idx] + 1
            for cell in row:
                if cell is not None and cell.begin_row == row_idx:
                    result[cell.end_row + 1] = max(
                        result[cell.end_row + 1], result[row_idx] + 1 + len(cell.lines)
                    )
        return result

    def _render_line(self, *, content: list[tuple[int, str]]) -> str:
        content.sort()
        result = []
        width = 0
        for position, text in content:
            if position > width:
                result.append(" " * (position - width))
                width = position
            elif position < width:
                raise ValueError(  # pragma: no cover
                    f"Bad content, overlap at {position}: {content}"
                )
            result.append(text)
            width += self.destination.string_proc.get_column_count(text=text)
        return "".join(result)

    @staticmethod
    def _get_box_drawing(
        *,
        has_above: bool = False,
        has_below: bool = False,
        has_left: bool = False,
        has_right: bool = False,
        header_sep: bool,
    ) -> str:
        index = (
            (0 if has_above else 8)
            + (0 if has_below else 4)
            + (0 if has_left else 2)
            + (0 if has_right else 1)
        )
        if header_sep:
            return "╪╡╞│╧╛╘╵╤╕╒╷═╴╶ "[index]
        return "┼┤├│┴┘└╵┬┐┌╷─╴╶ "[index]

    def _render_lines(
        self,
        *,
        line_content: list[list[tuple[int, str]]],
        has_right: bool,
        has_below: bool,
        row: int,
        ridx: int,
        col: int,
        cidx: int,
        cols: list[int],
        rows: list[int],
        is_header_sep: bool,
    ) -> None:
        if has_right:
            line_content[row].append(
                (
                    col + 1,
                    self._get_box_drawing(
                        has_left=True,
                        has_right=True,
                        header_sep=is_header_sep,
                    )
                    * (cols[cidx + 1] - col - 1),
                )
            )
        if has_below:
            c = self._get_box_drawing(has_above=True, has_below=True, header_sep=False)
            for r in range(row + 1, rows[ridx + 1]):
                line_content[r].append((col, c))

    def _render_frame(
        self,
        *,
        line_content: list[list[tuple[int, str]]],
        rows: list[int],
        cols: list[int],
    ) -> None:
        for ridx, row in enumerate(rows):
            has_row_before = ridx > 0
            has_row_after = ridx + 1 < len(rows)
            is_header_sep = ridx == self.header_rows
            for cidx, col in enumerate(cols):
                has_col_before = cidx > 0
                has_col_after = cidx + 1 < len(cols)
                c11 = (
                    self.row_matrix[ridx - 1][cidx - 1]
                    if has_col_before and has_row_before
                    else None
                )
                c12 = (
                    self.row_matrix[ridx - 1][cidx]
                    if has_col_after and has_row_before
                    else None
                )
                c21 = (
                    self.row_matrix[ridx][cidx - 1]
                    if has_col_before and has_row_after
                    else None
                )
                has_above = has_row_before
                has_below = has_row_after
                has_left = has_col_before
                has_right = has_col_after
                if c11 and c11.end_col >= cidx:
                    has_above = False
                if c21 and c21.end_col >= cidx:
                    has_below = False
                if c11 and c11.end_row >= ridx:
                    has_left = False
                if c12 and c12.end_row >= ridx:
                    has_right = False
                if has_above or has_below or has_left or has_right:
                    line_content[row].append(
                        (
                            col,
                            self._get_box_drawing(
                                has_above=has_above,
                                has_below=has_below,
                                has_left=has_left,
                                has_right=has_right,
                                header_sep=is_header_sep,
                            ),
                        )
                    )
                    self._render_lines(
                        line_content=line_content,
                        has_right=has_right,
                        has_below=has_below,
                        row=row,
                        ridx=ridx,
                        col=col,
                        cidx=cidx,
                        cols=cols,
                        rows=rows,
                        is_header_sep=is_header_sep,
                    )

    def _render_cells(
        self,
        *,
        line_content: list[list[tuple[int, str]]],
        rows: list[int],
        cols: list[int],
    ) -> None:
        for cell in self.cells:
            start_row = rows[cell.begin_row] + 1
            start_col = cols[cell.begin_col] + 1
            for index, line in enumerate(cell.lines):
                line_content[start_row + index].append((start_col, line))

    def _render_table(
        self, *, rows: list[int], cols: list[int], title_lines: list[str]
    ) -> list[str]:
        line_content: list[list[tuple[int, str]]] = [[] for _ in range(rows[-1] + 1)]
        self._render_frame(line_content=line_content, rows=rows, cols=cols)
        self._render_cells(line_content=line_content, rows=rows, cols=cols)
        lines = [self._render_line(content=content) for content in line_content]
        lines.extend(title_lines)
        return lines

    def render(self) -> None:
        """
        Render the table.
        """
        max_col_widths = self._get_maximum_column_widths()
        act_col_widths = [0] * len(max_col_widths)
        for cell in self.cells:
            cell_width = self._prerender_cell(cell=cell, max_col_widths=max_col_widths)
            # TODO: do this more weighted to avoid unnecessary space for a column
            col_width = math.ceil(cell_width / (cell.end_col - cell.begin_col + 1))
            for col in range(cell.begin_col, cell.end_col + 1):
                act_col_widths[col] = max(act_col_widths[col], col_width)
        cols = self._position_cols(act_col_widths=act_col_widths)
        rows = self._position_rows()
        title_lines = self._prerender_title(max_width=self.destination.remaining_width)
        lines = self._render_table(rows=rows, cols=cols, title_lines=title_lines)
        self.destination.main.add_raw_lines(lines)


def _get_generic_visit(
    value: _Formatting | tuple[str, str] | None,
) -> t.Callable[[t.Any, nodes.Node], None]:
    # pylint: disable-next=unused-argument
    def visit(self: t.Any, node: nodes.Node) -> None:
        # pylint: disable=protected-access
        if isinstance(value, tuple):
            self._context.top.main.append(text=value[0])
        elif value is not None:
            self._context.top.state.push_formatting(value)
            self._context.top.main.update_state()

    return visit


def _get_generic_depart(
    value: _Formatting | tuple[str, str] | None,
) -> t.Callable[[t.Any, nodes.Node], None]:
    # pylint: disable-next=unused-argument
    def depart(self: t.Any, node: nodes.Node) -> None:
        # pylint: disable=protected-access
        if isinstance(value, tuple):
            self._context.top.main.append(text=value[1])
        elif value is not None:
            self._context.top.state.pop_formatting(value)
            self._context.top.main.update_state()

    return depart


def _add_simple(
    definitions: dict[str, _Formatting | tuple[str, str] | None],
) -> t.Callable[[_Class], _Class]:
    def decorator(clazz: _Class) -> _Class:
        for class_name, value in definitions.items():
            setattr(clazz, f"visit_{class_name}", _get_generic_visit(value))
            setattr(clazz, f"depart_{class_name}", _get_generic_depart(value))
        return clazz

    return decorator


def _add_admonitions(
    definitions: dict[str, str],
) -> t.Callable[[_Class], _Class]:
    def decorator(clazz: _Class) -> _Class:
        def get_visit(first_indent: str):
            # pylint: disable-next=unused-argument
            def visit(self: t.Any, node: nodes.Node) -> None:
                # pylint: disable=protected-access
                self._context.top.main.new_par()
                self._context.push_context(
                    IndentContext(
                        remaining_width=self._context.top.remaining_width,
                        state=self._context.top.state,
                        string_proc=self._context.top.string_proc,
                        first_indent=first_indent,
                        at_least_one_line=True,
                    )
                )

            return visit

        def get_depart():
            # pylint: disable-next=unused-argument
            def depart(self: t.Any, node: nodes.Node) -> None:
                # pylint: disable=protected-access
                self._context.pop_context()

            return depart

        for class_name, first_indent in definitions.items():
            setattr(clazz, f"visit_{class_name}", get_visit(first_indent))
            setattr(clazz, f"depart_{class_name}", get_depart())
        return clazz

    return decorator


# pylint: disable=duplicate-code
@_add_unsupported_classes
@_add_simple(
    {
        "document": None,
        "inline": None,
        "generated": None,
        "entry": None,
        "literal": ("`", "`"),
        "emphasis": _Formatting.ITALICS,
        "strong": _Formatting.BOLD,
        "subscript": ("<sub>", "</sub>"),
        "superscript": ("<sup>", "</sup>"),
    }
)
@_add_admonitions(
    {
        "attention": "⚠️ ",
        "caution": "⚠️ ",
        "danger": "⚠️ ",
        "error": "❌ ",
        "important": "!\u20dd ",
        "note": "!\u20dd ",
        "tip": "ℹ️ ",
        "hint": "ℹ️ ",
        "warning": "⚠️ ",
    }
)
@_add_skip(
    [
        "comment",
    ]
)
class _Translator(nodes.NodeVisitor):  # pylint: disable=too-many-public-methods
    """
    Translates a docutils node tree to text in a ``DocumentContext``.
    """

    _context: DocumentContext

    def __init__(self, document, document_context: DocumentContext):
        super().__init__(document)
        self._context = document_context

    def get_text(self) -> str:
        """
        Return the result as a text.

        Must only be called after processing the document, and at most once.
        """
        context = self._context.top
        context.close()
        return context.get_text().lstrip("\n").rstrip("\n")

    # Node: paragraph

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_paragraph(self, node: nodes.paragraph) -> None:
        self._context.top.main.new_par()

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_paragraph(self, node: nodes.paragraph) -> None:
        self._context.top.main.new_par()

    # Node: title

    # pylint: disable-next=missing-function-docstring
    def visit_title(self, node: nodes.title) -> None:
        level = self._context.section_depth + 1
        title = node.astext()
        sep = self._context.global_context.title_headings[level - 1]
        underline = sep * math.ceil(
            self._context.top.string_proc.get_column_count(text=title)
            / self._context.top.string_proc.get_column_count(text=sep)
        )
        if self._context.section_depth == 0:
            self._context.top.top_state.push_formatting(_Formatting.BOLD)
            self._context.top.top.update_state()
            self._context.top.top.append(text=title)
            self._context.top.top.new_line()
            self._context.top.top.append(text=underline)
            self._context.top.top_state.push_formatting(_Formatting.BOLD)
            self._context.top.top.update_state()
            self._context.top.top.new_line()
            # Make sure there is an empty line
            self._context.top.top.new_line(force=True)
        else:
            self._context.top.main.new_par()
            self._context.top.state.push_formatting(_Formatting.BOLD)
            self._context.top.main.update_state()
            self._context.top.main.append(text=title)
            self._context.top.main.new_line()
            self._context.top.main.append(text=underline)
            self._context.top.state.pop_formatting(_Formatting.BOLD)
            self._context.top.main.update_state()
            self._context.top.main.new_par()
        raise nodes.SkipNode

    # Node: section

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_section(self, node: nodes.section) -> None:
        self._context.top.main.new_par()
        self._context.section_depth += 1

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_section(self, node: nodes.section) -> None:
        self._context.section_depth -= 1

    # Node: text

    # pylint: disable-next=missing-function-docstring,invalid-name
    def visit_Text(self, node: nodes.Text) -> None:
        text = node.astext()
        self._context.top.main.append(text=text)

    # pylint: disable-next=missing-function-docstring,invalid-name
    def depart_Text(self, node: nodes.Text) -> None:
        pass

    # Node: target

    # pylint: disable-next=missing-function-docstring
    def visit_target(self, node: nodes.target) -> None:
        pass

    # pylint: disable-next=missing-function-docstring
    def depart_target(self, node: nodes.target) -> None:
        pass

    # Node: reference

    # pylint: disable-next=missing-function-docstring
    def visit_reference(self, node: nodes.reference) -> None:
        pass

    # pylint: disable-next=missing-function-docstring
    def depart_reference(self, node: nodes.reference) -> None:
        if "refuri" in node.attributes:
            url: str = node.attributes["refuri"]
            # name = node.attributes.get("name") or "link"
            # TODO: is this really an URL? What does 'name' tell us?
        elif "refid" in node.attributes:
            return
        else:
            # docutils fails an assertion at this point
            raise ValueError(  # pragma: no cover
                f"Do not know how to handle reference with attributes {node.attributes!r}"
            )
        if node.astext() == url:
            return
        self._context.top.main.append(text=f" ({url})")

    # Node: bullet_list

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_bullet_list(self, node: nodes.bullet_list) -> None:
        self._context.top.main.new_par()
        self._context.push_context(
            ListContext(
                enumerator=_ConstEnumerator(
                    prefix="- ", string_proc=self._context.top.string_proc
                ),
                remaining_width=self._context.top.remaining_width,
                state=self._context.top.state,
                string_proc=self._context.top.string_proc,
            )
        )

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_bullet_list(self, node: nodes.bullet_list) -> None:
        self._context.pop_context()

    # Node: enumerated_list

    # pylint: disable-next=missing-function-docstring
    def visit_enumerated_list(self, node: nodes.enumerated_list) -> None:
        self._context.top.main.new_par()
        self._context.push_context(
            ListContext(
                enumerator=_VariableEnumerator(
                    generator=_arabic,
                    count=len(node),
                    string_proc=self._context.top.string_proc,
                ),
                remaining_width=self._context.top.remaining_width,
                state=self._context.top.state,
                string_proc=self._context.top.string_proc,
            )
        )

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_enumerated_list(self, node: nodes.enumerated_list) -> None:
        self._context.pop_context()

    # Node: list_item

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_list_item(self, node: nodes.list_item) -> None:
        list_context = t.cast(ListContext, self._context.top)
        first_indent, next_indent = list_context.get_next_item_indents()
        self._context.push_context(
            IndentContext(
                remaining_width=self._context.top.remaining_width,
                state=self._context.top.state,
                string_proc=self._context.top.string_proc,
                first_indent=first_indent,
                next_indent=next_indent,
                at_least_one_line=True,
            )
        )

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_list_item(self, node: nodes.list_item) -> None:
        self._context.pop_context()

    # Node: literal_block

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_literal_block(self, node: nodes.literal_block) -> None:
        self._context.top.main.new_par()
        self._context.push_context(
            IndentContext(
                remaining_width=self._context.top.remaining_width,
                state=self._context.top.state,
                string_proc=self._context.top.string_proc,
                ignore_newlines=False,
                first_indent="  ",
            )
        )

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_literal_block(self, node: nodes.literal_block) -> None:
        self._context.pop_context()

    # Node: block_quote

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_block_quote(self, node: nodes.block_quote) -> None:
        self._context.push_context(
            IndentContext(
                remaining_width=self._context.top.remaining_width,
                state=self._context.top.state,
                string_proc=self._context.top.string_proc,
                first_indent="  ",
            )
        )

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_block_quote(self, node: nodes.block_quote) -> None:
        self._context.pop_context()

    # Node: system_message

    # pylint: disable-next=missing-function-docstring
    def visit_system_message(self, node: nodes.system_message) -> None:
        message_type = node["type"]
        message_level = node["level"]
        source = node["source"]
        if node.hasattr("line"):
            source = f'{source}, line {node["line"]}'
        self._context.top.main.new_par()
        self._context.top.state.push_formatting(_Formatting.BOLD)
        self._context.top.main.update_state()
        self._context.top.main.append(
            text=f"⚠️ {message_type}/{message_level} ⚠️ ({source})"
        )
        self._context.top.state.pop_formatting(_Formatting.BOLD)
        self._context.top.main.update_state()
        self._context.top.main.new_par()
        self._context.push_context(
            IndentContext(
                first_indent="  ",
                remaining_width=self._context.top.remaining_width,
                state=self._context.top.state,
                string_proc=self._context.top.string_proc,
            )
        )

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_system_message(self, node: nodes.system_message) -> None:
        self._context.pop_context()
        self._context.top.main.new_par()

    # Node: topic

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_topic(self, node: nodes.topic) -> None:
        # The main use of <topic> elements is for Table of Contents
        class TopicContext(Context):
            """
            Context for a topic.
            """

        self._context.section_depth += 1
        self._context.push_context(
            TopicContext(
                remaining_width=self._context.top.remaining_width,
                state=self._context.top.state,
                string_proc=self._context.top.string_proc,
            )
        )

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_topic(self, node: nodes.topic) -> None:
        self._context.pop_context()
        self._context.section_depth -= 1

    # Node: image

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_image(self, node: nodes.image) -> None:
        self._context.top.main.new_par()
        raise nodes.SkipNode

    # Node: transition

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_transition(self, node: nodes.transition) -> None:
        self._context.top.main.new_par()
        elt = "─"
        self._context.top.main.append(
            text=elt
            * (
                self._context.top.remaining_width
                // self._context.top.string_proc.get_column_count(text=elt)
            )
        )
        self._context.top.main.new_par()
        raise nodes.SkipNode

    # Node: title_reference

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_title_reference(self, node: nodes.title_reference) -> None:
        # This usually happens if someone uses single backticks instead of double backticks
        self._context.top.state.push_formatting(_Formatting.ITALICS)
        self._context.top.main.update_state()

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_title_reference(self, node: nodes.title_reference) -> None:
        self._context.top.state.pop_formatting(_Formatting.ITALICS)
        self._context.top.main.update_state()

    # Node: problematic

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_problematic(self, node: nodes.problematic) -> None:
        self._context.top.main.append(text="⚠️ ")

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_problematic(self, node: nodes.problematic) -> None:
        self._context.top.main.append(text=" ⚠️")

    # Node: problematic

    # pylint: disable-next=missing-function-docstring
    def visit_table(self, node: nodes.table) -> None:
        renderer = _TableRenderer(
            table=node, destination=self._context.top, visitor=self
        )
        renderer.render()
        raise nodes.SkipNode


class _TextWriter(writers.Writer):
    """
    Create a text document from a docutils node tree.
    """

    def __init__(self, document_context: DocumentContext):
        writers.Writer.__init__(self)
        self.document_context = document_context
        self.translator_class = _Translator

    def translate(self) -> None:
        """
        Translate the document node tree to text.
        """
        translator = self.translator_class(self.document, self.document_context)
        if self.document:
            self.document.walkabout(translator)
        self.output = translator.get_text()


def render_as_text(
    source: str,
    /,
    parser_name: SupportedParser,
    global_context: GlobalContext | None = None,
    source_path: str | None = None,
    destination_path: str | None = None,
) -> RenderResult:
    """
    Render the document as text.

    :arg source: The document.
    :kwarg parser_name: The parser to use for ``source``.
    :kwarg global_context: An optional ``GlobalContext`` object.
    :kwarg source_path: An optional path for ``source``, to be used in error
        messages.
    :kwarg destination_path: An optional path for where the destination will
        be stored, to be used in error messages.
    :return: A ``RenderResult`` object containing the output and further
        information.
    """
    if global_context is None:
        global_context = GlobalContext()
    document_context = DocumentContext(global_context)
    # pylint: disable=duplicate-code
    warnings_stream = io.StringIO()
    opts: dict[str, t.Any] = {
        _PARSER_NAME_ARG: parser_name,
    }
    parts = publish_parts(
        source=source,
        source_path=source_path,
        destination_path=destination_path,
        writer=_TextWriter(document_context),
        settings_overrides=get_docutils_publish_settings(
            warnings_stream=warnings_stream
        ),
        **opts,
    )
    whole = parts["whole"]
    return RenderResult(
        whole.decode("utf-8") if isinstance(whole, bytes) else whole,
        document_context.unknown_node_types,
        warnings_stream.getvalue().splitlines(),
    )
    # pylint: enable=duplicate-code


__all__ = ("GlobalContext", "render_as_text")
