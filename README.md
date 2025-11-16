<!--
Copyright (c) Ansible Project
GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
SPDX-License-Identifier: GPL-3.0-or-later
-->

# antsibull-docutils -- Antsibull docutils helpers
[![Discuss on Matrix at #antsibull:ansible.com](https://img.shields.io/matrix/antsibull:ansible.com.svg?server_fqdn=ansible-accounts.ems.host&label=Discuss%20on%20Matrix%20at%20%23antsibull:ansible.com&logo=matrix)](https://matrix.to/#/#antsibull:ansible.com)
[![Nox badge](https://github.com/ansible-community/antsibull-docutils/workflows/nox/badge.svg?event=push&branch=main)](https://github.com/ansible-community/antsibull-docutils/actions?query=workflow%3A%22nox%22+branch%3Amain)
[![Codecov badge](https://img.shields.io/codecov/c/github/ansible-community/antsibull-docutils)](https://codecov.io/gh/ansible-community/antsibull-docutils)
[![REUSE status](https://api.reuse.software/badge/github.com/ansible-community/antsibull-docutils)](https://api.reuse.software/info/github.com/ansible-community/antsibull-docutils)

A Python library with some [docutils](https://www.docutils.org/) helpers used by Antsibull tools.

antsibull-docutils is covered by the [Ansible Code of Conduct](https://docs.ansible.com/projects/ansible/latest/community/code_of_conduct.html).

## Docutils support

In CI, compatibility with docutils 0.18+ is tested. Older versions of docutils might work as well, depending on your use-case. The tests do not pass for 0.16 and 0.17, as these versions emit different IDs and HTML (for tables). 0.16 also handles code blocks differently, and they will not be emitted with the MarkDown renderer.

## Development

Install and run `nox` to run all tests. That's it for simple contributions!
`nox` will create virtual environments in `.nox` inside the checked out project
and install the requirements needed to run the tests there.

To run specific tests:

1. `nox -e test` to only run unit tests;
2. `nox -e coverage` to display combined coverage results after running `nox -e
   test integration`;
3. `nox -e lint` to run all linters and formatters at once;
4. `nox -e formatters` to run `isort` and `black`;
5. `nox -e codeqa` to run `flake8`, `pylint`, `reuse lint`, and `antsibull-changelog lint`;
6. `nox -e typing` to run `mypy`.

## Creating a new release:

1. Run `nox -e bump -- <version> <release_summary_message>`. This:
   * Bumps the package version in `src/antsibull_docutils/__init__.py`.
   * Creates `changelogs/fragments/<version>.yml` with a `release_summary` section.
   * Runs `antsibull-changelog release` and adds the changed files to git.
   * Commits with message `Release <version>.` and runs `git tag -a -m 'antsibull-docutils <version>' <version>`.
   * Runs `hatch build --clean`.
2. Run `git push` to the appropriate remotes.
3. Once CI passes on GitHub, run `nox -e publish`. This:
   * Runs `hatch publish`;
   * Bumps the version to `<version>.post0`;
   * Adds the changed file to git and run `git commit -m 'Post-release version bump.'`;
4. Run `git push --follow-tags` to the appropriate remotes and create a GitHub release.

## License

Unless otherwise noted in the code, it is licensed under the terms of the GNU
General Public License v3 or, at your option, later. See
[LICENSES/GPL-3.0-or-later.txt](https://github.com/ansible-community/antsibull-docutils/tree/main/LICENSE)
for a copy of the license.

The repository follows the [REUSE Specification](https://reuse.software/spec/) for declaring copyright and
licensing information. The only exception are changelog fragments in ``changelog/fragments/``.
