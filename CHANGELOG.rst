========================================
Antsibull docutils helpers Release Notes
========================================

.. contents:: Topics

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
