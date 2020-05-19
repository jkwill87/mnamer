from abc import ABC, abstractmethod
from typing import List

from mnamer import tty
from mnamer.const import SYSTEM, USAGE, VERSION
from mnamer.exceptions import (
    MnamerAbortException,
    MnamerException,
    MnamerNetworkException,
    MnamerNotFoundException,
    MnamerSkipException,
)
from mnamer.setting_store import SettingStore
from mnamer.target import Target
from mnamer.types import MessageType
from mnamer.utils import clear_cache, get_filesize


class Frontend(ABC):
    settings: SettingStore
    targets: List[Target]

    def __init__(self, settings: SettingStore):
        self.settings = settings
        self.targets = Target.populate_paths(self.settings)
        tty.configure(self.settings)

        # handle directives and configuration
        if self.settings.version:
            tty.msg(f"mnamer version {VERSION}")
            raise SystemExit(0)

        if self.settings.config_dump:
            print(self.settings.as_json)
            raise SystemExit(0)

        if self.settings.clear_cache:
            clear_cache()
            tty.msg("cache cleared", MessageType.ALERT)
            raise SystemExit(0)

        if self.settings.test:
            tty.msg("testing mode", MessageType.ALERT)
        if self.settings.config_path:
            tty.msg(
                f"loaded config from '{self.settings.config_path}'",
                MessageType.ALERT,
            )

        # print configuration details
        tty.msg("\nsystem", debug=True)
        tty.msg(SYSTEM, debug=True)
        tty.msg("\nsettings", debug=True)
        tty.msg(self.settings.as_dict, debug=True)
        tty.msg("\ntargets", debug=True)
        tty.msg(self.targets or [None], debug=True)

    @abstractmethod
    def launch(self):
        pass


class Cli(Frontend):
    def __init__(self, settings: SettingStore):
        super().__init__(settings)
        if not settings.targets:
            tty.error(USAGE)
            raise SystemExit(2)
        tty.msg("Starting mnamer", MessageType.HEADING)

    def launch(self):
        # exit early if no media files are found
        total_count = len(self.targets)
        if total_count == 0:
            tty.msg("", debug=True)
            tty.msg("no media files found", MessageType.ALERT)
            raise SystemExit(0)

        # main program loop
        success_count = 0
        for target in self.targets:

            # announce file
            media_label = target.metadata.media.value.title()
            filename_label = target.source.name
            filesize_label = get_filesize(target.source)
            tty.msg(
                f'\nProcessing {media_label} "{filename_label}" ({filesize_label})',
                MessageType.HEADING,
            )
            tty.msg(target.source, debug=True)

            # list details
            tty.msg(
                f"using {target.provider_type.value}",
                MessageType.ALERT,
                debug=True,
            )
            tty.msg("\nsearch parameters", debug=True)
            tty.msg(target.metadata.as_dict, debug=True)
            tty.msg("", debug=True)

            # find match for target
            matches = []
            try:
                matches = target.query()
            except MnamerNotFoundException:
                tty.msg("no matches found", MessageType.ALERT)
            except MnamerNetworkException:
                tty.msg("network error", MessageType.ALERT)
            if not matches and self.settings.no_guess:
                tty.msg("skipping (--no-guess)", MessageType.ALERT)
                continue
            try:
                if self.settings.batch:
                    match = matches[0] if matches else target.metadata
                elif not matches:
                    match = tty.confirm_guess(target.metadata)
                else:
                    tty.msg("results")
                    match = tty.prompt(matches)
            except MnamerSkipException:
                tty.msg("skipping (user request)", MessageType.ALERT)
                continue
            except MnamerAbortException:
                tty.msg("aborting (user request)", MessageType.ERROR)
                break
            target.metadata.update(match)

            # sanity check move
            if target.destination == target.source:
                tty.msg(
                    f"skipping (source and destination paths are the same)",
                    MessageType.ALERT,
                )
                continue
            if self.settings.no_overwrite and target.destination.exists():
                tty.msg(
                    f"skipping (--no-overwrite)", MessageType.ALERT,
                )
                continue

            tty.msg(
                f"moving to {target.destination.absolute()}",
                MessageType.SUCCESS,
            )

            # rename and move file
            if self.settings.test:
                success_count += 1
                continue
            try:
                target.relocate()
            except MnamerException:
                tty.msg("FAILED!", MessageType.ERROR)
            else:
                tty.msg("OK!", MessageType.SUCCESS)
                success_count += 1

        # report results
        if success_count == 0:
            message_type = MessageType.ERROR
        elif success_count == total_count:
            message_type = MessageType.SUCCESS
        else:
            message_type = MessageType.ALERT
        tty.msg(
            f"\n{success_count} out of {total_count} files processed successfully",
            message_type,
        )


class Gui(Frontend):
    def launch(self):
        pass  # to be implemented in v3
