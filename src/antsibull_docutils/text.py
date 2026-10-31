# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026, Ansible Project

"""
Code for conversion to (formatted) plain text.
"""

from __future__ import annotations

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


class GlobalContext:  # pylint: disable=too-few-public-methods
    """
    The global conversion context.
    """

    title_headings: str = """=-~^.*+:`'"_#"""
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
            ignore_newlines=True,
        )
        self._main = _Collector(
            width=self.remaining_width,
            state=self.state,
            string_proc=self.string_proc,
            ignore_newlines=True,
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

    def get_text(self) -> str:
        """
        Return the content of the context as a string.
        """
        if self._result_main is None or self._result_top is None:
            raise ValueError("Context is not closed!")
        return "\n".join(self._result_top + self._result_main)


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
    ):
        indent_columns = string_proc.get_column_count(text=first_indent)
        super().__init__(
            remaining_width=remaining_width - indent_columns,
            state=state,
            string_proc=string_proc,
        )
        self.first_indent = first_indent
        self.next_indent = " " * indent_columns if next_indent is None else next_indent

    def close(self) -> None:
        super().close()
        assert self._result_main is not None
        _indent(
            self._result_main,
            first_indent=self.first_indent,
            next_indent=self.next_indent,
        )


class ListContext(Context):
    """
    Context for lists (enumeration, bullet list).
    """

    def __init__(
        self,
        *,
        indent: str,
        remaining_width: int,
        state: _State,
        string_proc: _StringProcessor,
    ):
        super().__init__(
            remaining_width=remaining_width - string_proc.get_column_count(text=indent),
            state=state,
            string_proc=string_proc,
        )
        self.first_indent = indent
        self.next_indent = " " * len(indent)


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


_Class = t.TypeVar("_Class")


def _get_generic_visit(
    value: _Formatting | tuple[str, str] | None,
) -> t.Callable[[t.Any, nodes.Node], None]:
    # pylint: disable-next=unused-argument
    def visit(self: t.Any, node: nodes.Node) -> None:
        if isinstance(value, tuple):
            # pylint: disable-next=protected-access
            self._context.top.main.append(text=value[0])
        elif value is not None:
            # pylint: disable-next=protected-access
            self._context.top.state.push_formatting(value)
            # pylint: disable-next=protected-access
            self._context.top.main.update_state()

    return visit


def _get_generic_depart(
    value: _Formatting | tuple[str, str] | None,
) -> t.Callable[[t.Any, nodes.Node], None]:
    # pylint: disable-next=unused-argument
    def depart(self: t.Any, node: nodes.Node) -> None:
        if isinstance(value, tuple):
            # pylint: disable-next=protected-access
            self._context.top.main.append(text=value[1])
        elif value is not None:
            # pylint: disable-next=protected-access
            self._context.top.state.pop_formatting(value)
            # pylint: disable-next=protected-access
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


# pylint: disable=duplicate-code
@_add_unsupported_classes
@_add_simple(
    {
        "document": None,
        "inline": None,
        "generated": None,
        "literal": ("`", "`"),
        "emphasis": _Formatting.ITALICS,
        "strong": _Formatting.BOLD,
        "subscript": ("<sub>", "</sub>"),
        "superscript": ("<sup>", "</sup>"),
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
            self._context.top.main.append(text=underline)
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
            self._context.top.top.new_line()
            self._context.top.main.append(text=underline)
            self._context.top.state.pop_formatting(_Formatting.BOLD)
            self._context.top.main.update_state()
            self._context.top.top.new_par()
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
            raise ValueError(
                f"Do not know how to handle reference with attributes {node.attributes!r}"
            )
        self._context.top.main.append(text=f" ({url})")

    # Node: bullet_list

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_bullet_list(self, node: nodes.bullet_list) -> None:
        self._context.top.main.new_par()
        self._context.push_context(
            ListContext(
                indent="- ",
                remaining_width=self._context.top.remaining_width,
                state=self._context.top.state,
                string_proc=self._context.top.string_proc,
            )
        )

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_bullet_list(self, node: nodes.bullet_list) -> None:
        self._context.pop_context()

    # Node: enumerated_list

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_enumerated_list(self, node: nodes.enumerated_list) -> None:
        self._context.top.main.new_par()
        self._context.push_context(
            ListContext(
                indent="1. ",
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
        self._context.push_context(
            IndentContext(
                remaining_width=self._context.top.remaining_width,
                state=self._context.top.state,
                string_proc=self._context.top.string_proc,
                first_indent=list_context.first_indent,
                next_indent=list_context.next_indent,
            )
        )

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_list_item(self, node: nodes.list_item) -> None:
        self._context.pop_context()

    # Node: literal_block

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_literal_block(self, node: nodes.literal_block) -> None:
        self._context.top.main.new_par()

        class LiteralContext(Context):
            """
            Context for a literal block.
            """

        self._context.push_context(
            LiteralContext(
                remaining_width=self._context.top.remaining_width,
                state=self._context.top.state,
                string_proc=self._context.top.string_proc,
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
        self._context.top.main.new_line()

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_system_message(self, node: nodes.system_message) -> None:
        self._context.top.main.new_par()

    # Node: note

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_note(self, node: nodes.note) -> None:
        self._context.top.main.new_par()
        self._context.push_context(
            IndentContext(
                remaining_width=self._context.top.remaining_width,
                state=self._context.top.state,
                string_proc=self._context.top.string_proc,
                first_indent="!\u20dd ",
            )
        )

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_note(self, node: nodes.note) -> None:
        self._context.pop_context()

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
    def visit_problematic(self, node):
        self._context.top.main.append(text="⚠️ ")

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_problematic(self, node):
        self._context.top.main.append(text=" ⚠️")

    # Node: problematic

    # pylint: disable-next=missing-function-docstring
    def visit_table(self, node):
        # TODO: render tables!
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
