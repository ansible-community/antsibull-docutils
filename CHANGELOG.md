# Antsibull docutils helpers Release Notes

**Topics**

- <a href="#v1-2-0">v1\.2\.0</a>
    - <a href="#release-summary">Release Summary</a>
    - <a href="#minor-changes">Minor Changes</a>
- <a href="#v1-1-0">v1\.1\.0</a>
    - <a href="#release-summary-1">Release Summary</a>
    - <a href="#minor-changes-1">Minor Changes</a>
    - <a href="#bugfixes">Bugfixes</a>
- <a href="#v1-0-0">v1\.0\.0</a>
    - <a href="#release-summary-2">Release Summary</a>

<a id="v1-2-0"></a>
## v1\.2\.0

<a id="release-summary"></a>
### Release Summary

Feature release\.

<a id="minor-changes"></a>
### Minor Changes

* Add helper <code>antsibull\_docutils\.rst\_code\_finder\.find\_code\_blocks\(\)</code> that allows to find code blocks in RST files\. This is useful for linters and also code that wants to modify the code block\'s contents\. \([https\://github\.com/ansible\-community/antsibull\-docutils/pull/12](https\://github\.com/ansible\-community/antsibull\-docutils/pull/12)\)\.

<a id="v1-1-0"></a>
## v1\.1\.0

<a id="release-summary-1"></a>
### Release Summary

Maintenance release\.

<a id="minor-changes-1"></a>
### Minor Changes

* Declare support for Python 3\.13 \([https\://github\.com/ansible\-community/antsibull\-docutils/pull/4](https\://github\.com/ansible\-community/antsibull\-docutils/pull/4)\)\.

<a id="bugfixes"></a>
### Bugfixes

* Ensure that docutils\' <code>publish\_parts\(\)</code> <code>whole</code> output is a text string and not bytes \([https\://github\.com/ansible\-community/antsibull\-docutils/pull/6](https\://github\.com/ansible\-community/antsibull\-docutils/pull/6)\)\.

<a id="v1-0-0"></a>
## v1\.0\.0

<a id="release-summary-2"></a>
### Release Summary

Initial release\.

The codebase has been migrated from antsibull\-changelog\, with a few bugfixes and improvements\.
