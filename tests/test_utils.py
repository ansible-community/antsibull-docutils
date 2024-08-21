# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
Test utils module.
"""

from __future__ import annotations

import pytest

from antsibull_docutils.utils import (
    ensure_newline_after_last_content,
    get_document_structure,
    get_docutils_publish_settings,
)


def test_get_docutils_publish_settings():
    result = get_docutils_publish_settings()
    assert result["raw_enabled"] is False
    assert result["warning_stream"] is False

    result = get_docutils_publish_settings(warnings_stream="")
    assert result["raw_enabled"] is False
    assert result["warning_stream"] is False

    result = get_docutils_publish_settings(warnings_stream="foo")
    assert result["raw_enabled"] is False
    assert result["warning_stream"] == "foo"


def test_get_document_structure():
    result = get_document_structure(
        r"""Foo Bar :anunknownrole:`foo`

.. anunknownclass:
""",
        parser_name="restructuredtext",
    )
    print(result)
    assert isinstance(result.output, str)
    assert "Foo Bar" in result.output
    assert result.unsupported_class_names == set()
    assert any("anunknownrole" in line for line in result.warnings)
    assert all("anunknownclass" not in line for line in result.warnings)


@pytest.mark.parametrize(
    "lines, expected",
    [
        (
            [],
            [],
        ),
        (
            [
                "",
            ],
            [
                "",
            ],
        ),
        (
            [
                "Test",
            ],
            [
                "Test",
                "",
            ],
        ),
        (
            [
                "Test",
                "",
            ],
            [
                "Test",
                "",
            ],
        ),
    ],
)
def test_ensure_newline_after_last_content(lines, expected):
    lines = lines.copy()
    ensure_newline_after_last_content(lines)
    assert lines == expected
