from pathlib import Path
from typing import Dict

JUNK_TEXT = "asdf#$@#g9765sdfg54hggaw"

TEST_FILES: Dict[str, Path] = {
    test_file: Path(*test_file.split("/"))
    for test_file in (
        "Desktop/temp.zip",
        "Documents/Photos/DCM0001.jpg",
        "Documents/Photos/DCM0002.jpg",
        "Documents/Skiing Trip.mp4",
        "Downloads/Return of the Jedi 1080p.mkv",
        "Downloads/archer.2009.s10e07.webrip.x264-lucidtv.mkv",
        "Downloads/the.goonies.1985.mp4",
        "Ninja Turtles (1990).mkv",
        "avengers infinity war.wmv",
        "game.of.thrones.01x05-eztv.mp4",
        "scan001.tiff",
    )
}
