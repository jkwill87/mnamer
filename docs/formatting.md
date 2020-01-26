# Formatting

Using the **episode-directory**, **episode-format**, **movie-directory**, or **movie-format** [settings](configuration.md) you customize how your files are renamed.

mnamer uses Python's builtin [format string syntax](https://docs.python.org/3/library/string.html#format-string-syntax) which wraps template field variables in braces \(`{}`\). Additionally, it automatically trims and concatenates whitespace and punctuation.

Also worth note, nesting directories in the fields will result in their automatic creation, as needed.

## Template Field Variables

| Field | Description | Media Type |
| :--- | :--- | :--- |
| name | movie name | Movie |
| title | episode title | Episode |
| year | movie release year | Movie |
| series | episode's series name | Episode |
| season | episode's airing season number | Episode |
| episode | episode's episode number | Episode |
| date | episode's airdate | Episode |
| quality | a combination of parsed audio-visual quality metadata | Any |

## Examples

### 00x00 Television Format

* television\_format: `{series} {season:02}x{episode:02}{title}{extension}`
* target: `~/Downloads/Rick.and.Morty.S02E01.WEBRip.x264-RARBG.mp4`
* result: `~/Downloads/Rick and Morty - 02x01 - A Rickle in Time.mp4`

### Missing Metadata

{% hint style="info" %}
Target file is missing group metadata field in title and will be omitted gracefully
{% endhint %}

* television\_format: `{series} - S{season:02}E{episode:02} - {group} - {title}{extension}`
* target: `~/Downloads/The.Orville.S01E01.1080p.WEB-DL.DD5.1.H264.mkv`
* result: `~/Downloads/The Orville - S01E01 - Old Wounds.mkv`

### Nesting Directories

{% hint style="info" %}
If the subdirectory doesn't exist, mnamer will create it
{% endhint %}

* movie\_format: `{name} ({year}){extension}`
* movie\_directory: `/media/movies/{name} ({year})`
* target: `~/Downloads/The.Goonies.1985.720p.BluRay.x264-SiNNERS.mkv`
* result: `/media/movies/The Goonies (1985)/The Goonies (1985).mkv`

