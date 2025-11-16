========================================
Antsibull docutils helpers Release Notes
========================================

.. contents:: Topics

v1.3.1
======

Release Summary
---------------

Maintenance release.

Minor Changes
-------------

- Declare support for Python 3.14 (https://github.com/ansible-community/antsibull-docutils/pull/19).

v1.3.0
======

Release Summary
---------------

Feature and bugfix release.

Minor Changes
-------------

- Add functionality to parse documents, and to search for code blocks in parsed documents. This allows to perform other operations on the parsed document, instead of having to parse it multiple times (https://github.com/ansible-community/antsibull-docutils/pull/14, https://github.com/ansible-community/antsibull-docutils/pull/16).
- Allow to find all literal blocks without language (https://github.com/ansible-community/antsibull-docutils/pull/15).
- Allow to pass ``content_offset`` to ``mark_antsibull_code_block()`` for more precise locating (https://github.com/ansible-community/antsibull-docutils/pull/16).

Bugfixes
--------

- Fix code block first content line detection (https://github.com/ansible-community/antsibull-docutils/pull/16).

v1.2.1
======

Release Summary
---------------

Bugfix release.

Bugfixes
--------

- Ensure that ``path`` and ``root_prefix`` for ``antsibull_docutils.rst_code_finder.find_code_blocks()`` can actually be path-like objects (https://github.com/ansible-community/antsibull-docutils/pull/13).

v1.2.0
======

Release Summary
---------------

Feature release.

Minor Changes
-------------

- Add helper ``antsibull_docutils.rst_code_finder.find_code_blocks()`` that allows to find code blocks in RST files. This is useful for linters and also code that wants to modify the code block's contents. (https://github.com/ansible-community/antsibull-docutils/pull/12).

v1.1.0
======

Release Summary
---------------

Maintenance release.

Minor Changes
-------------

- Declare support for Python 3.13 (https://github.com/ansible-community/antsibull-docutils/pull/4).

Bugfixes
--------

- Ensure that docutils' ``publish_parts()`` ``whole`` output is a text string and not bytes (https://github.com/ansible-community/antsibull-docutils/pull/6).

v1.0.0
======

Release Summary
---------------

Initial release.

The codebase has been migrated from antsibull-changelog, with a few bugfixes and improvements.
