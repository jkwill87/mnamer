from abc import ABC, abstractmethod

from mnamer import tty
from mnamer.const import SYSTEM, USAGE, VERSION
from mnamer.exceptions import (
    MnamerAbortException,
    MnamerException,
    MnamerNetworkException,
    MnamerNotFoundException,
    MnamerSkipException,
)
from mnamer.language import Language
from mnamer.setting_store import SettingStore
from mnamer.target import Target
from mnamer.types import MessageType
from mnamer.utils import clear_cache, get_filesize, is_subtitle


class Frontend(ABC):
    settings: SettingStore
    targets: list[Target]

    def __init__(self, settings: SettingStore):
        self.settings = settings
        self.targets = Target.populate_paths(self.settings)
        tty.configure(self.settings)
        self._handle_directives()
        self._print_configuration()

    def _handle_directives(self) -> None:
        if self.settings.version:
            tty.msg(f"mnamer version {VERSION}")
            raise SystemExit(0)

        if self.settings.config_dump:
            print(self.settings.as_json())
            raise SystemExit(0)

        if self.settings.clear_cache:
            clear_cache()
            tty.msg("cache cleared", MessageType.ALERT)
            raise SystemExit(0)

        if self.settings.test:
            tty.msg("testing mode", MessageType.ALERT)
        if self.settings.config_path:
            tty.msg(
                f"loaded config from '{self.settings.config_path}'", MessageType.ALERT
            )

    def _print_configuration(self) -> None:
        tty.msg("\nsystem", debug=True)
        tty.msg(SYSTEM, debug=True)
        tty.msg("\nsettings", debug=True)
        tty.msg(self.settings.as_dict(), debug=True)
        tty.msg("\ntargets", debug=True)
        if self.targets:
            tty.msg(self.targets, debug=True)
        else:
            tty.msg([None], debug=True)

    @abstractmethod
    def launch(self):
        pass


class Cli(Frontend):
    def __init__(self, settings: SettingStore):
        super().__init__(settings)
        if not settings.targets:
            tty.error(USAGE)
            raise SystemExit(2)
        self.success_count = 0

    @property
    def total_count(self):
        return len(self.targets)

    def launch(self) -> None:
        tty.msg("Starting mnamer", MessageType.HEADING)
        self._ensure_targets()
        self._process_targets()
        self._report_results()

    def _ensure_targets(self) -> None:
        if not self.targets:
            tty.msg("", debug=True)
            tty.msg("no media files found", MessageType.ALERT)
            raise SystemExit(0)

    def _process_targets(self) -> None:
        for target in self.targets:
            self._announce_file(target)
            self._list_details(target)

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
                    match = tty.metadata_guess(target.metadata)
                else:
                    match = tty.metadata_prompt(matches)
            except MnamerSkipException:
                tty.msg("skipping (user request)", MessageType.ALERT)
                continue
            except MnamerAbortException:
                tty.msg("aborting (user request)", MessageType.ERROR)
                break
            target.metadata.update(match)

            if (
                is_subtitle(target.metadata.container)
                and not target.metadata.language_sub
            ):
                #! Harcoding subtitle language to English
                english = Language(name="English", a2="en", a3="eng")
                Language.ensure_valid_for_tvdb(english)
                target.metadata.language_sub = english

                #! # Uncomment the following lines if you want to prompt for subtitle language
                # try:
                #     # target.metadata.language_sub = tty.subtitle_prompt()
                # except MnamerSkipException:
                #     tty.msg("skipping (user request)", MessageType.ALERT)
                #     continue
                # except MnamerAbortException:
                #     tty.msg("aborting (user request)", MessageType.ERROR)
                #     break

            if target.source.is_symlink():
                error_msg = "Source is a symlink"
                tty.msg(error_msg, MessageType.ERROR)

                raise MnamerException(error_msg)

            if target.destination.resolve() == target.source.resolve():
                if target.source.is_symlink():
                    "This means that the source and symlink destination are in the same directory"
                    error_msg = (
                        "Source and destination symlinks are in the same directory"
                    )
                    tty.msg(error_msg, MessageType.ERROR)

                    raise MnamerException(error_msg)

                if target.destination.is_symlink():
                    if self.settings.move:
                        self._rename_and_move_file(target)

                    tty.msg(
                        "Destination is already a symlink of source",
                        MessageType.ALERT,
                    )

                    if self.settings.recreate_symlink:
                        tty.msg(
                            "Recreating symlink is enabled, recreating it",
                            MessageType.ALERT,
                        )
                        self._recreate_symlink(target)

                    continue
                else:
                    # source and destination are the same, skip
                    tty.msg(
                        "Skipping (source and destination paths are the same)",
                        MessageType.ALERT,
                    )
                    continue

            if self.settings.no_overwrite and target.destination.exists():
                tty.msg("Skipping (--no-overwrite)", MessageType.ALERT)
                continue

            self._rename_and_move_file(target)

    def _announce_file(self, target: Target):
        media_type = target.metadata.to_media_type().value.title()
        description = (
            f"{media_type} Subtitle"
            if is_subtitle(target.metadata.container)
            else media_type
        )
        filename_label = target.source.name
        filesize_label = get_filesize(target.source)
        tty.msg(
            f'\nProcessing {description} "{filename_label}" ({filesize_label})',
            MessageType.HEADING,
        )
        tty.msg(target.source, debug=True)

    def _list_details(self, target: Target):
        tty.msg(f"using {target.provider_type.value}", MessageType.ALERT, debug=True)
        tty.msg("\nsearch parameters", debug=True)
        tty.msg(target.metadata.as_dict(), debug=True)
        tty.msg("", debug=True)

    def _recreate_symlink(self, target: Target):
        tty.msg(
            f"Re-creating symlink in {target.destination.absolute()}",
            MessageType.SUCCESS,
        )

        if self.settings.test:
            self.success_count += 1
            return
        try:
            # recreate symlink
            target.relocate(should_relocate_with_symlink=True)
        except MnamerException as e:
            tty.msg("FAILED!", MessageType.ERROR)
            tty.msg(str(e), MessageType.ERROR)
        else:
            tty.msg("OK!", MessageType.SUCCESS)
            self.success_count += 1

    def _rename_and_move_file(self, target: Target):
        should_relocate_with_symlink = not self.settings.move
        action_name = "Symlink" if should_relocate_with_symlink else "Moving"

        tty.msg(
            f"{action_name} to {target.destination.absolute()}", MessageType.SUCCESS
        )

        if self.settings.test:
            self.success_count += 1
            return

        try:
            target.relocate(should_relocate_with_symlink=should_relocate_with_symlink)
        except MnamerException:
            tty.msg("FAILED!", MessageType.ERROR)
        except PermissionError as e:
            tty.msg("FAILED!", MessageType.ERROR)
            tty.msg(f"Permission error: {e.strerror} ({e.filename})", MessageType.ERROR)
        else:
            tty.msg("OK!", MessageType.SUCCESS)
            self.success_count += 1

    def _report_results(self) -> None:
        if self.success_count == 0:
            message_type = MessageType.ERROR
        elif self.success_count == self.total_count:
            message_type = MessageType.SUCCESS
        else:
            message_type = MessageType.ALERT
        tty.msg(
            f"\n{self.success_count} out of {self.total_count} files processed successfully",
            message_type,
        )


class Gui(Frontend):
    def launch(self):
        pass  # to be implemented in v3
