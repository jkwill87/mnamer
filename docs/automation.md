# Automation

## Step 1: Enable Batch Mode

In addition to operating interactively, mnamer can be configured to run in batch mode, automatically renaming and moving files without used involvement. As detailed in the [settings](configuration.md) section this can be set using the `batch` setting. This along with all other settings mentioned here can be set using CLI arguments or config file keys.

## Step 2: Set Destination Directories

This isn't specific to batch mode or necessary but if you're looking to automate file relocation you probably have a destination in mind that you want your files moved to. mnamer uses the `movie-directory` and `episode-directory` settings to configure the move and episode directories, respectfully.

## Step 3: Set Your Comfort Level

All of mnamer's settings are available in and out of batch mode but these are particularly recommended to make automation safer-- using them mnamer might not do the right thing but at least it won't do the wrong thing.

* `noguess` prevents guessing using the metadata available from parsing when a file can't be matched against a provider.
* `noreplace` prevents moving or renaming a file if it will result in overwriting an existing file.

## Step 4: Setup a Workflow

Once you have mnamer configured to your liking you need some way to run it. Here are some options:

* If you use a torrent of NZB client it may allow you to run a script after a file is completed.
* Using a scheduled job using **cron** or **journalctl**
* Watching a directory using **inotifywait**





