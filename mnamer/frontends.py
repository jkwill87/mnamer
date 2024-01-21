import time
from abc import ABC, abstractmethod
from pathlib import Path

from watchdog.events import FileClosedEvent, FileSystemEventHandler
from watchdog.observers import Observer

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


class Cli(Frontend, FileSystemEventHandler):
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
        if self.settings.watch:
            self._watch_targets()
        else:
            self._ensure_targets()
            self._process_targets()
            self._report_results()

    def _watch_targets(self) -> None:
        observer = Observer()
        for target in self.settings.targets:
            tty.msg(f"watching {str(target.absolute())}", debug=True)
            observer.schedule(
                self, str(target.absolute()), recursive=self.settings.recurse
            )

        observer.start()
        try:
            self._process_targets()

            while True:
                time.sleep(5)
        except:
            observer.stop()
        observer.join()

    def on_closed(self, event: FileClosedEvent):
        if event.is_directory:
            return

        target = Target.filter_file_path(self.settings, Path(event.src_path))
        if target is None:
            return

        try:
            self._process_target(target)
        except FileNotFoundError:
            tty.msg(f"file not found {str(target.source)}", MessageType.ALERT)

    def _ensure_targets(self) -> None:
        if not self.targets:
            tty.msg("", debug=True)
            tty.msg("no media files found", MessageType.ALERT)
            raise SystemExit(0)

    def _process_targets(self) -> None:
        for target in self.targets:
            cancel = self._process_target(target)
            if cancel:
                break

    def _process_target(self, target: Target) -> bool:
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
            return False
        try:
            if self.settings.batch:
                match = matches[0] if matches else target.metadata
            elif not matches:
                match = tty.metadata_guess(target.metadata)
            else:
                match = tty.metadata_prompt(matches)
        except MnamerSkipException:
            tty.msg("skipping (user request)", MessageType.ALERT)
            return False
        except MnamerAbortException:
            tty.msg("aborting (user request)", MessageType.ERROR)
            return True
        target.metadata.update(match)

        if is_subtitle(target.metadata.container) and not target.metadata.language_sub:
            if self.settings.batch:
                tty.msg(
                    "skipping (subtitle language can't be detected)",
                    MessageType.ALERT,
                )
                return False
            try:
                target.metadata.language_sub = tty.subtitle_prompt()
            except MnamerSkipException:
                tty.msg("skipping (user request)", MessageType.ALERT)
                return False
            except MnamerAbortException:
                tty.msg("aborting (user request)", MessageType.ERROR)
                return True

        # sanity check move
        if target.destination == target.source:
            tty.msg(
                "skipping (source and destination paths are the same)",
                MessageType.ALERT,
            )
            return False
        if self.settings.no_overwrite and target.destination.exists():
            tty.msg("skipping (--no-overwrite)", MessageType.ALERT)
            return False

        self._rename_and_move_file(target)
        return False

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

    def _rename_and_move_file(self, target: Target):
        tty.msg(
            f"moving to {target.destination.absolute()}",
            MessageType.SUCCESS,
        )
        if self.settings.test:
            self.success_count += 1
            return
        try:
            target.relocate()
        except MnamerException:
            tty.msg("FAILED!", MessageType.ERROR)
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
