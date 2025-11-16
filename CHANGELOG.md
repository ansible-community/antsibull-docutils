# Antsibull docutils helpers Release Notes

**Topics**

- <a href="#v1-3-1">v1\.3\.1</a>
    - <a href="#release-summary">Release Summary</a>
    - <a href="#minor-changes">Minor Changes</a>
- <a href="#v1-3-0">v1\.3\.0</a>
    - <a href="#release-summary-1">Release Summary</a>
    - <a href="#minor-changes-1">Minor Changes</a>
    - <a href="#bugfixes">Bugfixes</a>
- <a href="#v1-2-1">v1\.2\.1</a>
    - <a href="#release-summary-2">Release Summary</a>
    - <a href="#bugfixes-1">Bugfixes</a>
- <a href="#v1-2-0">v1\.2\.0</a>
    - <a href="#release-summary-3">Release Summary</a>
    - <a href="#minor-changes-2">Minor Changes</a>
- <a href="#v1-1-0">v1\.1\.0</a>
    - <a href="#release-summary-4">Release Summary</a>
    - <a href="#minor-changes-3">Minor Changes</a>
    - <a href="#bugfixes-2">Bugfixes</a>
- <a href="#v1-0-0">v1\.0\.0</a>
    - <a href="#release-summary-5">Release Summary</a>

<a id="v1-3-1"></a>
## v1\.3\.1

<a id="release-summary"></a>
### Release Summary

Maintenance release\.

<a id="minor-changes"></a>
### Minor Changes

* Declare support for Python 3\.14 \([https\://github\.com/ansible\-community/antsibull\-docutils/pull/19](https\://github\.com/ansible\-community/antsibull\-docutils/pull/19)\)\.

<a id="v1-3-0"></a>
## v1\.3\.0

<a id="release-summary-1"></a>
### Release Summary

Feature and bugfix release\.

<a id="minor-changes-1"></a>
### Minor Changes

* Add functionality to parse documents\, and to search for code blocks in parsed documents\. This allows to perform other operations on the parsed document\, instead of having to parse it multiple times \([https\://github\.com/ansible\-community/antsibull\-docutils/pull/14](https\://github\.com/ansible\-community/antsibull\-docutils/pull/14)\, [https\://github\.com/ansible\-community/antsibull\-docutils/pull/16](https\://github\.com/ansible\-community/antsibull\-docutils/pull/16)\)\.
* Allow to find all literal blocks without language \([https\://github\.com/ansible\-community/antsibull\-docutils/pull/15](https\://github\.com/ansible\-community/antsibull\-docutils/pull/15)\)\.
* Allow to pass <code>content\_offset</code> to <code>mark\_antsibull\_code\_block\(\)</code> for more precise locating \([https\://github\.com/ansible\-community/antsibull\-docutils/pull/16](https\://github\.com/ansible\-community/antsibull\-docutils/pull/16)\)\.

<a id="bugfixes"></a>
### Bugfixes

* Fix code block first content line detection \([https\://github\.com/ansible\-community/antsibull\-docutils/pull/16](https\://github\.com/ansible\-community/antsibull\-docutils/pull/16)\)\.

<a id="v1-2-1"></a>
## v1\.2\.1

<a id="release-summary-2"></a>
### Release Summary

Bugfix release\.

<a id="bugfixes-1"></a>
### Bugfixes

* Ensure that <code>path</code> and <code>root\_prefix</code> for <code>antsibull\_docutils\.rst\_code\_finder\.find\_code\_blocks\(\)</code> can actually be path\-like objects \([https\://github\.com/ansible\-community/antsibull\-docutils/pull/13](https\://github\.com/ansible\-community/antsibull\-docutils/pull/13)\)\.

<a id="v1-2-0"></a>
## v1\.2\.0

<a id="release-summary-3"></a>
### Release Summary

Feature release\.

<a id="minor-changes-2"></a>
### Minor Changes

* Add helper <code>antsibull\_docutils\.rst\_code\_finder\.find\_code\_blocks\(\)</code> that allows to find code blocks in RST files\. This is useful for linters and also code that wants to modify the code block\'s contents\. \([https\://github\.com/ansible\-community/antsibull\-docutils/pull/12](https\://github\.com/ansible\-community/antsibull\-docutils/pull/12)\)\.

<a id="v1-1-0"></a>
## v1\.1\.0

<a id="release-summary-4"></a>
### Release Summary

Maintenance release\.

<a id="minor-changes-3"></a>
### Minor Changes

* Declare support for Python 3\.13 \([https\://github\.com/ansible\-community/antsibull\-docutils/pull/4](https\://github\.com/ansible\-community/antsibull\-docutils/pull/4)\)\.

<a id="bugfixes-2"></a>
### Bugfixes

* Ensure that docutils\' <code>publish\_parts\(\)</code> <code>whole</code> output is a text string and not bytes \([https\://github\.com/ansible\-community/antsibull\-docutils/pull/6](https\://github\.com/ansible\-community/antsibull\-docutils/pull/6)\)\.

<a id="v1-0-0"></a>
## v1\.0\.0

<a id="release-summary-5"></a>
### Release Summary

Initial release\.

The codebase has been migrated from antsibull\-changelog\, with a few bugfixes and improvements\.
