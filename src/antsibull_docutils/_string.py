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

# import unicodedata


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
