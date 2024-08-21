# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
MarkDown utilities.
"""

from __future__ import annotations

from html import escape as _html_escape


def html_escape(text: str) -> str:
    """
    Escape a text for HTML.
    """
    return _html_escape(text).replace("&quot;", '"')


def html_argument_escape(text: str) -> str:
    """
    Escape a text for HTML inside an argument delimited with double quotes (").
    """
    return _html_escape(text)


__all__ = ("html_escape", "html_argument_escape")
