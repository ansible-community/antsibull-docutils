# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
Utilities.
"""

from __future__ import annotations

import abc
import typing as t

from docutils import nodes

_Class = t.TypeVar("_Class")
_GlobalContext = t.TypeVar("_GlobalContext")


def add_unsupported_classes(clazz: _Class) -> _Class:
    """
    Add unknown classes encountered in the node visitor to the ``unknown_node_types``
    set of the visitor's context.
    """

    def get_visit(class_name: str):
        # pylint: disable-next=unused-argument
        def visit_unsupported(self: t.Any, node: nodes.Node):
            # pylint: disable-next=protected-access
            self._context.unknown_node_types.add(class_name)
            raise nodes.SkipNode

        return visit_unsupported

    for class_name in nodes.node_class_names:
        function_name = f"visit_{class_name}"
        if not hasattr(clazz, function_name):
            setattr(clazz, function_name, get_visit(class_name))

    return clazz


def add_skip(class_names: list[str]) -> t.Callable[[_Class], _Class]:
    """
    Skip class names in the node visitor.
    """

    def decorator(clazz: _Class) -> _Class:
        def visit(self: t.Any, node: nodes.Node) -> None:
            raise nodes.SkipNode

        for class_name in class_names:
            setattr(clazz, f"visit_{class_name}", visit)
        return clazz

    return decorator


_ContextBase = t.TypeVar("_ContextBase")


class ContextBase(t.Generic[_ContextBase], metaclass=abc.ABCMeta):
    """
    Base context class for MarkDown conversion.
    """

    @abc.abstractmethod
    def append(
        self,
        context: _ContextBase,
    ) -> None:
        """
        Append another context to this context.
        """

    @abc.abstractmethod
    def close(self) -> None:
        """
        Close the context.

        Should be called before using its value / content, for example by
        passing it to ``append()`` or calling ``get_text()``.
        """


_Context = t.TypeVar("_Context", bound=ContextBase)


class DocumentContextBase(t.Generic[_GlobalContext, _Context]):
    """
    Conversion context for a document.
    """

    section_depth: int
    global_context: _GlobalContext
    unknown_node_types: set[str]
    created_labels: set[str]

    _contexts: list[_Context]

    def __init__(self, global_context: _GlobalContext) -> None:
        self.section_depth = 0
        self.global_context = global_context
        self.unknown_node_types = set()
        self.created_labels = set()
        self._contexts = []

    def push_context(self, context: _Context) -> None:
        """
        Add a new context on the context stack.
        """
        self._contexts.append(context)

    def pop_context(self) -> None:
        """
        Pop the top-most context from the context stack.

        The last context cannot be popped, trying to do so will result in a
        ``ValueError`` exception.
        """
        if len(self._contexts) < 2:
            raise ValueError("Cannot pop last element")
        context = self._contexts.pop()
        context.close()
        self._contexts[-1].append(context)

    @property
    def top(self) -> _Context:
        """
        Return the top-most context from the context stack.
        """
        return self._contexts[-1]
