# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
MarkDown utilities.
"""

from __future__ import annotations

import re

_MD_ESCAPE = re.compile(r"""([!"#$%&'()*+,:;<=>?@[\\\]^_`{|}~.-])""")


def md_escape(text: str) -> str:
    """
    Escape a text for MarkDown.
    """
    return _MD_ESCAPE.sub(r"\\\1", text)


__all__ = ("md_escape",)
