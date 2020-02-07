# Formatting

## Getting Started

Using the **episode-directory**, **episode-format**, **movie-directory**, or **movie-format** [settings](configuration.md) you customize how your files are renamed.

### Syntax Overview

mnamer formatting uses Python's builtin [format string syntax](https://docs.python.org/3/library/string.html#format-string-syntax). Variables wrapped in braces `{}` get substituted with of parsed values for the template field variables listed below. See the example section below for inspiration.

### Advanced Format Specifiers Use

mnamer also has limited support format specifier:

It supports padding number values by appending `:0n` to a variable, where `n` is the number of digits to pad to. For instance, `{season:02}` to pad a season with to two digits, or `{season:03}` to pad it to to three.

It also supports indexing string values by appending `[n]` to a variable, where `n` is the zero-based index. For instance `{name[0]}` will output the first character of name.

### Other Considerations

In all cases whitespace and punctuation are trimmed and collapsed. Also worth note, nesting directories in the fields will result in their automatic creation, as needed.

### Template Field Variables

| Field   | Description                                           | Media Type |
| :------ | :---------------------------------------------------- | :--------- |
| name    | movie name                                            | Movie      |
| title   | episode title                                         | Episode    |
| year    | movie release year                                    | Movie      |
| series  | episode's series name                                 | Episode    |
| season  | episode's airing season number                        | Episode    |
| episode | episode's episode number                              | Episode    |
| date    | episode's airdate                                     | Episode    |
| quality | a combination of parsed audio-visual quality metadata | Any        |

## Examples

### 00x00 Television Format

- television_format: `{series} {season:02}x{episode:02}{title}{extension}`
- target: `~/Downloads/Rick.and.Morty.S02E01.WEBRip.x264-RARBG.mp4`
- result: `~/Downloads/Rick and Morty - 02x01 - A Rickle in Time.mp4`

### Missing Metadata

{% hint style="info" %}
Target file is missing group metadata field in title and will be omitted gracefully
{% endhint %}

- television_format: `{series} - S{season:02}E{episode:02} - {group} - {title}{extension}`
- target: `~/Downloads/The.Orville.S01E01.1080p.WEB-DL.DD5.1.H264.mkv`
- result: `~/Downloads/The Orville - S01E01 - Old Wounds.mkv`

### Nesting Directories

{% hint style="info" %}
If the subdirectory doesn't exist, mnamer will create it
{% endhint %}

- movie_format: `{name} ({year}){extension}`
- movie_directory: `/media/movies/{name[0]}/{name} ({year})`
- target: `~/Downloads/Seven.720p.BluRay.x264-SiNNERS.mkv`
- result: `/media/movies/S/Seven (1995)/Seven (1995).mkv`
