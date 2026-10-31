# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026, Ansible Project

"""
String utilities.
"""

from __future__ import annotations

import abc
import sys
import typing as t
import unicodedata

# The following tests whether Python 3.15+ is used.
_HAS_ITER_GRAPHEMES = hasattr(unicodedata, "iter_graphemes")

if not _HAS_ITER_GRAPHEMES:
    import grapheme


def _iter_graphemes(
    text: str, *, start: int = 0, end: int = sys.maxsize
) -> t.Generator[tuple[int, int]]:
    """
    Uses unicodedata.iter_graphemes for Python 3.15+, and functionality from the
    grapheme dependency on older Pythons.

    This basically implements:
    https://www.unicode.org/reports/tr29/#Grapheme_Cluster_Boundaries
    """
    if _HAS_ITER_GRAPHEMES:
        for segment in unicodedata.iter_graphemes(  # type: ignore[attr-defined]
            text, start, end
        ):
            yield segment.start, segment.end
    else:
        position = start
        # pylint: disable-next=possibly-used-before-assignment
        for length in grapheme.grapheme_lengths(text[start:end]):
            next_pos = position + length
            yield position, next_pos
            position = next_pos


class StringProcessor(metaclass=abc.ABCMeta):
    """
    Abstract class that provides string processing functionality.
    """

    @abc.abstractmethod
    def get_column_count(self, *, text: str) -> int:
        """
        Compute the number of columns needed for a string.
        """

    @abc.abstractmethod
    def split(
        self, *, text: str, remaining_columns: int, total_columns: int
    ) -> tuple[bool, str, int, str, int, str]:
        """
        Given a text, try to determine a beginning that fits into the current line,
        or in the next line, and the remainder.

        The return value is a tuple ``(newline, text, text_columns, space,
        space_columns, remainder)``, where:

        newline
            Whether ``text`` fits into this line (``False``),
            or needs to be put into a new line (``True``).
        text
            The text to put into this or the next line.
        text_columns
            The number of columns used up by ``text``.
        space:
            Whitespace following text (before ``remainder``).
        space_columns:
            The number of columns used up by ``space``.
        remainder:
            The remaining text.
        """


class ASCIIStringProcessor(StringProcessor):
    """
    Provides string processing functionality assuming basically ASCII characters.
    """

    def get_column_count(self, *, text: str) -> int:
        """
        Compute the number of columns needed for a string.
        """
        return len(text)

    def _strip_space(self, text: str) -> tuple[str, int, str]:
        length = len(text)
        index = 0
        while index < length and text[index] == " ":
            index += 1
        return text[:index], index, text[index:]

    def _split_fit(self, text: str) -> tuple[str, int, str, int]:
        idx = len(text)
        while idx > 0 and text[idx - 1] == " ":
            idx -= 1
        return text[:idx], idx, text[idx:], len(text) - idx

    def _split_make_fitting(
        self, text: str, columns: int
    ) -> tuple[str, int, str, int, str] | None:
        idx = text.rfind(" ", 0, columns + 1)
        if idx < 0:
            return None
        while idx > 0 and text[idx - 1] == " ":
            idx -= 1
        if idx == 0 and text[0] == " ":
            return "", 0, *self._strip_space(text[idx:])
        return text[:idx], idx, *self._strip_space(text[idx:])

    def split(
        self, *, text: str, remaining_columns: int, total_columns: int
    ) -> tuple[bool, str, int, str, int, str]:
        """
        Given a text, try to determine a beginning that fits into the current line,
        or in the next line, and the remainder.

        The return value is a tuple ``(newline, text, text_columns, space,
        space_columns, remainder)``, where:

        newline
            Whether ``text`` fits into this line (``False``),
            or needs to be put into a new line (``True``).
        text
            The text to put into this or the next line.
        text_columns
            The number of columns used up by ``text``.
        space:
            Whitespace following text (before ``remainder``).
        space_columns:
            The number of columns used up by ``space``.
        remainder:
            The remaining text.
        """
        newline = remaining_columns < total_columns
        if newline:
            if len(text) <= remaining_columns:
                return False, *self._split_fit(text), ""
            result = self._split_make_fitting(text, remaining_columns)
            if result:
                return False, *result
            # We must put it into the next line, so trim leading space
            text = text.lstrip()
        if len(text) <= total_columns:
            return newline, *self._split_fit(text), ""
        result = self._split_make_fitting(text, total_columns)
        if result:
            return newline, *result
        return newline, text[:total_columns], total_columns, "", 0, text[total_columns:]


_HYPHEN_MINUS = "-"
_HYPHEN = "\u2010"
_SOFT_HYPHEN = "\u00ad"
_ZERO_WIDTH = (_SOFT_HYPHEN,)


def _remove_zero_width(*, text: str) -> str:
    for codepoint in _ZERO_WIDTH:
        text = text.replace(codepoint, "")
    return text


def _get_column_count(*, text: str, start: int, end: int) -> int:
    # This is similar to Sphinx' implementation, but ignores certain codepoints
    # we treat as zero-width.
    return sum(
        (
            0
            if codepoint in _ZERO_WIDTH
            else (2 if unicodedata.east_asian_width(codepoint) in ("W", "F") else 1)
        )
        for codepoint in text[start:end]
        if not unicodedata.combining(codepoint)
    )


def _find_space(*, text: str, start: int, end: int) -> tuple[int, int]:
    index = start
    while index < end:
        if unicodedata.category(text[index]) != "Zs":
            break
        index += 1
    return (
        index,
        _get_column_count(text=text, start=start, end=index),
    )


class UnicodeStringProcessor(StringProcessor):
    """
    Provides string processing functionality with proper Unicode support.

    It would be better to implement the Unicode line breaking algorithm
    (https://www.unicode.org/reports/tr14/), but that's far from trivial
    (https://www.rogerbinns.com/blog/a-small-club-implementing-unicode-tr29-and-tr14.html).
    We can either use a library such as PyICU (https://pypi.org/project/pyicu/),
    which comes with its own set of baggage, or stick to a simpler, but often
    enough sufficient approach like this one.
    """

    def get_column_count(self, *, text: str) -> int:
        """
        Compute the number of columns needed for a string.
        """
        return _get_column_count(text=text, start=0, end=len(text))

    @staticmethod
    def _can_split(
        *,
        text: str,
        position: int,
        next_position: int,
        columns: int,
        next_columns: int,  # pylint: disable=unused-argument
        is_space: bool,
        last_was_space: bool,
    ) -> tuple[int, int, int, str | None] | None:
        if is_space:
            # There should not be any space graphemes consisting out of more than one codepoint
            assert next_position == position + 1
            if not last_was_space:
                return position, position, columns, None
        elif text[position] in (_HYPHEN_MINUS, _HYPHEN) and not last_was_space:
            return position + 1, position + 1, columns + 1, None
        elif text[position] == _SOFT_HYPHEN and not last_was_space:
            return position, position + 1, columns + 1, "-"
        return None

    @staticmethod
    def _split(
        *,
        newline: bool,
        text: str,
        initial_skip: int,
        position: int,
        next_position: int,
        column_count: int,
        appendix: str | None,
    ) -> tuple[bool, str, int, str, int, str]:
        remainder_index, space_columns = _find_space(
            text=text, start=next_position, end=len(text)
        )
        main_text = _remove_zero_width(text=text[initial_skip:position])
        if appendix is not None:
            main_text += appendix
        return (
            newline,
            main_text,
            column_count,
            _remove_zero_width(text=text[next_position:remainder_index]),
            space_columns,
            text[remainder_index:],
        )

    @staticmethod
    def _split_end(
        *,
        text: str,
        columns: int,
        remaining_columns: int,
        total_columns: int,
        space_end: int,
        space_columns: int,
        end_index: int,
    ) -> tuple[bool, str, int, str, int, str]:
        initial_skip = 0
        newline = columns > remaining_columns and total_columns > remaining_columns
        if newline:
            initial_skip = space_end
            columns -= space_columns
        return UnicodeStringProcessor._split(
            newline=newline,
            text=text,
            initial_skip=initial_skip,
            position=end_index,
            next_position=end_index,
            column_count=columns,
            appendix=None,
        )

    def split(  # pylint: disable=too-many-locals
        self, *, text: str, remaining_columns: int, total_columns: int
    ) -> tuple[bool, str, int, str, int, str]:
        """
        Given a text, try to determine a beginning that fits into the current line,
        or in the next line, and the remainder.

        The return value is a tuple ``(newline, text, text_columns, space,
        space_columns, remainder)``, where:

        newline
            Whether ``text`` fits into this line (``False``),
            or needs to be put into a new line (``True``).
        text
            The text to put into this or the next line.
        text_columns
            The number of columns used up by ``text``.
        space:
            Whitespace following text (before ``remainder``).
        space_columns:
            The number of columns used up by ``space``.
        remainder:
            The remaining text.
        """
        length = len(text)
        space_end, space_columns = _find_space(text=text, start=0, end=length)
        if space_end == length:
            return False, "", 0, text, space_columns, ""

        columns = 0
        potential_split: tuple[int, int, int, str | None] | None = None
        last_was_space = False
        for start, end in _iter_graphemes(text):
            is_space = unicodedata.category(text[start]) == "Zs"
            cur_columns = _get_column_count(text=text, start=start, end=end)
            opt_potential_split = UnicodeStringProcessor._can_split(
                text=text,
                position=start,
                next_position=end,
                columns=columns,
                next_columns=cur_columns,
                is_space=is_space,
                last_was_space=last_was_space,
            )
            if opt_potential_split is not None and opt_potential_split[0] == start:
                # Only assign a successful potential split yet if it doesn't extend beyond start
                potential_split = opt_potential_split
            columns += cur_columns
            if (
                columns > remaining_columns
                and potential_split is not None
                and potential_split[2] <= remaining_columns
            ):
                position, next_position, column_count, appendix = potential_split
                return UnicodeStringProcessor._split(
                    newline=False,
                    text=text,
                    initial_skip=0,
                    position=position,
                    next_position=next_position,
                    column_count=column_count,
                    appendix=appendix,
                )
            if columns - space_columns > total_columns:
                if potential_split is not None and potential_split[2] <= total_columns:
                    position, next_position, column_count, appendix = potential_split
                    return UnicodeStringProcessor._split(
                        newline=True,
                        text=text,
                        initial_skip=space_end,
                        position=position,
                        next_position=next_position,
                        column_count=column_count - space_columns,
                        appendix=appendix,
                    )
                if columns > cur_columns:
                    columns -= cur_columns
                    return self._split_end(
                        text=text,
                        columns=columns,
                        remaining_columns=remaining_columns,
                        total_columns=total_columns,
                        space_end=space_end,
                        space_columns=space_columns,
                        end_index=start,
                    )
            potential_split = opt_potential_split or potential_split
            last_was_space = is_space

        end_index = length
        while end_index > 0 and unicodedata.category(text[end_index - 1]) == "Zs":
            end_index -= 1
        end_space_cols = _get_column_count(text=text, start=end_index, end=length)
        columns -= end_space_cols
        return self._split_end(
            text=text,
            columns=columns,
            remaining_columns=remaining_columns,
            total_columns=total_columns,
            space_end=space_end,
            space_columns=space_columns,
            end_index=end_index,
        )
