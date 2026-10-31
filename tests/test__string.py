# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026, Ansible Project

"""
Test _string module.
"""

from __future__ import annotations

import pytest

from antsibull_docutils._string import ASCIIStringProcessor, UnicodeStringProcessor

TEST_ASCII_STRING_PROCESSOR_GET_COLUMN_COUNT_DATA: list[tuple[str, int]] = [
    ("", 0),
    ("foo", 3),
    ("foo bar", 7),
    ("      ", 6),
]


@pytest.mark.parametrize(
    "text, expected_columns",
    TEST_ASCII_STRING_PROCESSOR_GET_COLUMN_COUNT_DATA,
)
def test_ASCIIStringProcessor_get_column_count(
    text: str,
    expected_columns: int,
) -> None:
    proc = ASCIIStringProcessor()
    columns = proc.get_column_count(text=text)
    assert columns == expected_columns


TEST_ASCII_STRING_PROCESSOR_SPLIT_DATA: list[
    tuple[str, int, int, bool, str, int, str, int, str]
] = [
    (
        "",
        10,
        20,
        False,
        "",
        0,
        "",
        0,
        "",
    ),
    (
        "  ",
        10,
        20,
        False,
        "",
        0,
        "  ",
        2,
        "",
    ),
    (
        "  foobarbazbam  baz",
        10,
        20,
        False,
        "",
        0,
        "  ",
        2,
        "foobarbazbam  baz",
    ),
    (
        "foobarbazbam  ",
        10,
        20,
        True,
        "foobarbazbam",
        12,
        "  ",
        2,
        "",
    ),
    (
        "foobarbazbam  baz",
        10,
        20,
        True,
        "foobarbazbam  baz",
        17,
        "",
        0,
        "",
    ),
    (
        "foobarbazbam  bambazfoobar",
        10,
        20,
        True,
        "foobarbazbam",
        12,
        "  ",
        2,
        "bambazfoobar",
    ),
    (
        "Hello foo!",
        10,
        20,
        False,
        "Hello foo!",
        10,
        "",
        0,
        "",
    ),
    (
        "Hello foo!  ",
        10,
        20,
        False,
        "Hello foo!",
        10,
        "  ",
        2,
        "",
    ),
    (
        "Hello  foo!",
        10,
        20,
        False,
        "Hello",
        5,
        "  ",
        2,
        "foo!",
    ),
    (
        "       foo!",
        10,
        20,
        False,
        "",
        0,
        "       ",
        7,
        "foo!",
    ),
    (
        "Hello world!",
        10,
        20,
        False,
        "Hello",
        5,
        " ",
        1,
        "world!",
    ),
    (
        "Helloworld!",
        10,
        10,
        False,
        "Helloworld",
        10,
        "",
        0,
        "!",
    ),
    (
        "Helloworld!",
        10,
        20,
        True,
        "Helloworld!",
        11,
        "",
        0,
        "",
    ),
    (
        "Helloworld!  ",
        10,
        20,
        True,
        "Helloworld!",
        11,
        "  ",
        2,
        "",
    ),
]


@pytest.mark.parametrize(
    "text, remaining_columns, total_columns, expected_newline, expected_text,"
    " expected_text_columns, expected_space, expected_space_columns, expected_remainder",
    TEST_ASCII_STRING_PROCESSOR_SPLIT_DATA,
)
def test_ASCIIStringProcessor_split(
    text: str,
    remaining_columns: int,
    total_columns: int,
    expected_newline: bool,
    expected_text: str,
    expected_text_columns: int,
    expected_space: str,
    expected_space_columns: int,
    expected_remainder: str,
) -> None:
    proc = ASCIIStringProcessor()
    newline, text, text_columns, space, space_columns, remainder = proc.split(
        text=text, remaining_columns=remaining_columns, total_columns=total_columns
    )
    print(
        newline, repr(text), text_columns, repr(space), space_columns, repr(remainder)
    )
    assert newline == expected_newline
    assert text == expected_text
    assert text_columns == expected_text_columns
    assert space == expected_space
    assert space_columns == expected_space_columns
    assert remainder == expected_remainder


TEST_UNICODE_STRING_PROCESSOR_GET_COLUMN_COUNT_DATA: list[tuple[str, int]] = [
    ("", 0),
    ("foo", 3),
    ("foo bar", 7),
    ("      ", 6),
]


@pytest.mark.parametrize(
    "text, expected_columns",
    TEST_UNICODE_STRING_PROCESSOR_GET_COLUMN_COUNT_DATA,
)
def test_UnicodeStringProcessor_get_column_count(
    text: str,
    expected_columns: int,
) -> None:
    proc = UnicodeStringProcessor()
    columns = proc.get_column_count(text=text)
    assert columns == expected_columns


TEST_UNICODE_STRING_PROCESSOR_SPLIT_DATA: list[
    tuple[str, int, int, bool, str, int, str, int, str]
] = [
    (
        "",
        10,
        20,
        False,
        "",
        0,
        "",
        0,
        "",
    ),
    (
        "  ",
        10,
        20,
        False,
        "",
        0,
        "  ",
        2,
        "",
    ),
    (
        "  foobarbazbam  baz",
        10,
        20,
        False,
        "",
        0,
        "  ",
        2,
        "foobarbazbam  baz",
    ),
    (
        "foobarbazbam  ",
        10,
        20,
        True,
        "foobarbazbam",
        12,
        "  ",
        2,
        "",
    ),
    (
        "foobarbazbam  baz",
        10,
        20,
        True,
        "foobarbazbam  baz",
        17,
        "",
        0,
        "",
    ),
    (
        "foobarbazbam  bambazfoobar",
        10,
        20,
        True,
        "foobarbazbam",
        12,
        "  ",
        2,
        "bambazfoobar",
    ),
    (
        "Hello foo!",
        10,
        20,
        False,
        "Hello foo!",
        10,
        "",
        0,
        "",
    ),
    (
        "Hello foo!  ",
        10,
        20,
        False,
        "Hello foo!",
        10,
        "  ",
        2,
        "",
    ),
    (
        "Hello  foo!",
        10,
        20,
        False,
        "Hello",
        5,
        "  ",
        2,
        "foo!",
    ),
    (
        "       foo!",
        10,
        20,
        False,
        "",
        0,
        "       ",
        7,
        "foo!",
    ),
    (
        "Hello world!",
        10,
        20,
        False,
        "Hello",
        5,
        " ",
        1,
        "world!",
    ),
    (
        "Helloworld!",
        10,
        10,
        False,
        "Helloworld",
        10,
        "",
        0,
        "!",
    ),
    (
        "Helloworld!",
        10,
        20,
        True,
        "Helloworld!",
        11,
        "",
        0,
        "",
    ),
    (
        "Helloworld!  ",
        10,
        20,
        True,
        "Helloworld!",
        11,
        "  ",
        2,
        "",
    ),
    (
        "Hello-world!  ",
        10,
        20,
        False,
        "Hello-",
        6,
        "",
        0,
        "world!  ",
    ),
    (
        "Hello\u00adworld!  ",
        10,
        20,
        False,
        "Hello-",
        6,
        "",
        0,
        "world!  ",
    ),
    (
        "\u00adx\u00ad",
        1,
        1,
        False,
        "x",
        1,
        "",
        0,
        "",
    ),
    (
        "\u00adx\u00adx",
        1,
        1,
        False,
        "x",
        1,
        "",
        0,
        "x",
    ),
    (
        "\u00adx\u00adx",
        1,
        2,
        True,
        "xx",
        2,
        "",
        0,
        "",
    ),
    # The following use grapheme cluster examples from
    # https://www.unicode.org/reports/tr29/#Grapheme_Cluster_Boundaries
    (
        "நிx",  # Tamil ni grapheme (two codeopints)
        1,
        2,
        True,
        "நி",
        2,
        "",
        0,
        "x",
    ),
    (
        "กำx",  # Thai kam grapheme (two codepoints)
        1,
        2,
        True,
        "กำ",
        2,
        "",
        0,
        "x",
    ),
    (
        "षिx",  # Devanagari ssi grapheme (two codepoints)
        1,
        2,
        True,
        "षि",
        2,
        "",
        0,
        "x",
    ),
    (
        "क्षिx",  # Devanagari kshi grapheme (four codepoints)
        2,
        3,
        True,
        "क्षि",
        3,
        "",
        0,
        "x",
    ),
    (
        "क्षिx",  # Devanagari kshi grapheme (four codepoints)
        1,
        2,
        True,
        "क्षि",
        3,
        "",
        0,
        "x",
    ),
]


@pytest.mark.parametrize(
    "text, remaining_columns, total_columns, expected_newline, expected_text,"
    " expected_text_columns, expected_space, expected_space_columns, expected_remainder",
    TEST_UNICODE_STRING_PROCESSOR_SPLIT_DATA,
)
def test_UnicodeStringProcessor_split(
    text: str,
    remaining_columns: int,
    total_columns: int,
    expected_newline: bool,
    expected_text: str,
    expected_text_columns: int,
    expected_space: str,
    expected_space_columns: int,
    expected_remainder: str,
) -> None:
    proc = UnicodeStringProcessor()
    newline, text, text_columns, space, space_columns, remainder = proc.split(
        text=text, remaining_columns=remaining_columns, total_columns=total_columns
    )
    print(
        newline, repr(text), text_columns, repr(space), space_columns, repr(remainder)
    )
    assert newline == expected_newline
    assert text == expected_text
    assert text_columns == expected_text_columns
    assert space == expected_space
    assert space_columns == expected_space_columns
    assert remainder == expected_remainder
