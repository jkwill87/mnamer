# Migrating from v1 to v2

## Python Compatibility

mnamer v2 drops Python v2 support. Python 3.6+ is required.

## Configuration File

To avoid conflicts with mnamer v1's `.mnamer.json` configuration file, mnamer v2 uses `.mnamer-v2.json`.

## Settings Changes

Some settings have been renamed, some have been added, some have been removed.

### Renamed

{% hint style="info" %}
mnamer v2 documents settings using dashes instead of underscores however both are supported for compatibility.
{% endhint %}

| v1 | v2 |
| :--- | :--- |
| max\_hits | hits |
| extension\_mask | mask |
| movie\_destination | movie-directory |
| television\_api | episode-api |
| television\_destination | episode-directory |
| television\_template | episode-template |
| test\_run | test |
| blacklist | ignore |

### Removed

* config\_load
* config\_save

### Added

* id-imdb
* id-tmdb
* id-tvdb
* noguess
* nocache
* version

## Templating

* variables inside curly braces \(e.g. `{variable}`\) inside of **television\_directory**, **television\_format**, **movie\_directory**, and **movie\_format** fields will be replaced by metadata. 
* Custom angle bracket format syntax replaced with standard Python braces compatible with the builtin `format()` method.

