# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
Test text module.
"""

from __future__ import annotations

import typing as t

import pytest

from antsibull_docutils._collector import EmptyState
from antsibull_docutils._string import UnicodeStringProcessor
from antsibull_docutils.text import (
    Context,
    DocumentContext,
    GlobalContext,
    render_as_text,
)
from antsibull_docutils.utils import get_document_structure

RENDER_AS_TEXT_AND_STRUCTURE_DATA: list[
    tuple[str, str, t.Literal["markdown", "restructuredtext"], str, set[str]]
] = [
    (
        "empty",
        "",
        "restructuredtext",
        "",
        set(),
    ),
    (
        "hello-world",
        "Hello world.",
        "restructuredtext",
        r"Hello world.",
        set(),
    ),
    (
        "link",
        "`foo <bar>`__",
        "restructuredtext",
        "foo (bar)",
        set(),
    ),
    (
        "lorem-ipsum",
        r"""
Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex
sapien ``vitae pellentesque sem placerat``. In id cursus mi pretium tellus duis
convallis. Tempus leo eu aenean sed diam urna tempor. **Pulvinar vivamus
fringilla lacus nec metus bibendum egestas.** Iaculis massa nisl malesuada
lacinia integer nunc posuere. *Ut hendrerit semper vel class aptent taciti
sociosqu.* Ad litora torquent per conubia nostra inceptos himenaeos.

Lorem ipsum dolor sit amet, consectetur adipiscing elit,
sed do eiusmod tempor incididunt ut labore et dolore magna
aliqua::

  Ut enim ad minim veniam, quis nostrud exercitation
    ullamco laboris nisi ut aliquip ex ea commodo consequat.

* Lorem ipsum dolor sit *amet consectetur* adipiscing elit. Quisque faucibus ex
  sapien vitae pellentesque sem placerat. **In id cursus** mi pretium tellus duis
  convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus
  fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada
  lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti
  sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.

  * Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex
    sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis
    convallis. Tempus leo eu aenean sed diam urna tempor.

    * Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex
      sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis
      convallis.

      * Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex
        sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis
        convallis.

        * Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex
          sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis
          convallis.
""",
        "restructuredtext",
        """Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex
sapien `vitae pellentesque sem placerat`. In id cursus mi pretium tellus duis
convallis. Tempus leo eu aenean sed diam urna tempor. \x1b[0;1mPulvinar vivamus fringilla\x1b[0m
\x1b[0;1mlacus nec metus bibendum egestas.\x1b[0m Iaculis massa nisl malesuada lacinia integer
nunc posuere. \x1b[0;3mUt hendrerit semper vel class aptent taciti sociosqu.\x1b[0m Ad litora
torquent per conubia nostra inceptos himenaeos.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua:

Ut enim ad minim veniam, quis nostrud exercitation   ullamco laboris nisi ut
aliquip ex ea commodo consequat.

- Lorem ipsum dolor sit \x1b[0;3mamet consectetur\x1b[0m adipiscing elit. Quisque faucibus ex
  sapien vitae pellentesque sem placerat. \x1b[0;1mIn id cursus\x1b[0m mi pretium tellus duis
  convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus
  fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada
  lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti
  sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.

  - Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus
    ex sapien vitae pellentesque sem placerat. In id cursus mi pretium
    tellus duis convallis. Tempus leo eu aenean sed diam urna tempor.

    - Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque
      faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi
      pretium tellus duis convallis.

      - Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque
        faucibus ex sapien vitae pellentesque sem placerat. In id cursus
        mi pretium tellus duis convallis.

        - Lorem ipsum dolor sit amet consectetur adipiscing elit.
          Quisque faucibus ex sapien vitae pellentesque sem placerat.
          In id cursus mi pretium tellus duis convallis.""",
        set(),
    ),
    (
        "bug-2",
        r"""
A block quote:

    Some block quote.
    Another line.

    Another paragraph.

.. note::

  This is a note.
  A second line!

  And a second paragraph.

.. note::

  And another note.

- A list item
- .. note::

    This is a note.
    A second line!

    And a second paragraph.

  .. note::

    And another note.
""",
        "restructuredtext",
        """A block quote:

  Some block quote. Another line.

  Another paragraph.

!⃝ This is a note. A second line!

   And a second paragraph.

!⃝ And another note.

- A list item
- !⃝ This is a note. A second line!

     And a second paragraph.

  !⃝ And another note.""",
        set(),
    ),
]


@pytest.mark.parametrize(
    "title, input, input_parser, expected_output, expected_unsupported_class_names",
    RENDER_AS_TEXT_AND_STRUCTURE_DATA,
    ids=[e[0] for e in RENDER_AS_TEXT_AND_STRUCTURE_DATA],
)
def test_render_as_text(
    title: str,
    input: str,
    input_parser: t.Literal["markdown", "restructuredtext"],
    expected_output: str,
    expected_unsupported_class_names: set[str],
) -> None:
    result = render_as_text(input, parser_name=input_parser)
    print(get_document_structure(input, parser_name=input_parser).output)
    print(result.output)
    print(repr(result.output))
    assert result.output == expected_output
    assert result.unsupported_class_names == expected_unsupported_class_names


def test_context() -> None:
    context = Context(
        has_top=False,
        remaining_width=80,
        state=EmptyState(),
        string_proc=UnicodeStringProcessor(),
    )
    with pytest.raises(ValueError) as exc:
        context.top.append(text="test")
    assert str(exc.value) == "Context has no top part"

    subcontext = Context(
        has_top=True,
        remaining_width=70,
        state=EmptyState(),
        string_proc=UnicodeStringProcessor(),
    )
    subcontext.close()
    with pytest.raises(ValueError) as exc:
        context.append(subcontext)
    assert str(exc.value) == "Context has no top part"

    context2 = Context(
        has_top=True,
        remaining_width=80,
        state=EmptyState(),
        string_proc=UnicodeStringProcessor(),
    )
    context2.append(subcontext)


def test_document_context() -> None:
    global_context = GlobalContext()
    doc_context = DocumentContext(global_context)

    with pytest.raises(ValueError) as exc:
        doc_context.pop_context()
    assert str(exc.value) == "Cannot pop last element"

    previous_top = doc_context.top

    a_context = Context(
        remaining_width=80, state=EmptyState(), string_proc=UnicodeStringProcessor()
    )
    doc_context.push_context(a_context)
    assert doc_context.top is a_context
    doc_context.pop_context()

    assert doc_context.top is previous_top
