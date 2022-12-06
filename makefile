help:
	$(info * deployment:  build, publish, publish-test)
	$(info * versioning:  bump-patch, bump-minor, bump-major)
	$(info * setup:       venv, demo)

clean-build:
	$(info * cleaning build files)
	@find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__
	@rm -rf mnamer.egg-info build dist

clean-demo:
	$(info * cleaning demo files)
	@rm -rf build dist *.egg-info demo

clean-venv:
	$(info * removing venv files)
	@deactivate 2> /dev/null || true
	@rm -rf venv

clean: clean-build clean-demo clean-venv


# Deployment Helpers -----------------------------------------------------------

build: clean-build
	$(info * building distributable)
	@python3 -m build --sdist --wheel --no-isolation > /dev/null 2>&1

publish: build
	$(info * publishing to PyPI repository)
	twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

publish-test: build
	$(info * publishing to PyPI test repository)
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*


# Version Helpers --------------------------------------------------------------

bump-patch:
	$(info * resetting any current changes)
	git reset --
	$(info * bumping patch version)
	@vbump --patch
	git add mnamer/__version__.py
	$(info * commiting version change)
	git commit -m "Patch version bump"
	$(info * creating tag)
	git tag `vbump | egrep -o '[0-9].*'`

bump-minor:
	$(info * resetting any current changes)
	git reset --
	$(info * bumping minor version)
	vbump --minor
	git add mnamer/__version__.py
	$(info * commiting version change)
	git commit -m "Minor version bump"
	$(info * creating tag)
	git tag `vbump | egrep -o '[0-9].*'`

bump-major:
	$(info * resetting any current changes)
	git reset --
	$(info * bumping major version)
	vbump --major
	git add mnamer/__version__.py
	$(info * commiting version change)
	git commit -m "Major version bump"
	$(info * creating tag)
	git tag `vbump | egrep -o '[0-9].*'`


# Setup Helpers ----------------------------------------------------------------

demo: clean-demo
	$(info * setting up demo directory)
	@mkdir -p \
	    demo \
	    'demo/Avengers Infinity War' \
	    'demo/Sample' \
	    'demo/Downloads' \
	    'demo/Images/Photos'
	@cd demo && touch \
        "Avengers Infinity War/Avengers.Infinity.War.en.srt" \
        "Avengers Infinity War/Avengers.Infinity.War.wmv" \
        "Downloads/Return of the Jedi 1080p.mkv" \
        "Downloads/archer.2009.s10e07.webrip.x264-lucidtv.mkv" \
        "Downloads/the.goonies.1985.mp4" \
        "Images/Photos/DCM0001.jpg" \
        "Images/Photos/DCM0002.jpg" \
        "Ninja Turtles (1990).mkv" \
        "O.J. - Made in America S01EP03 (2016) (1080p).mp4" \
        "Planet Earth II S01E06 - Cities (2016) (2160p).mp4" \
        "Pride & Prejudice 2005.ts" \
        "Sample/the mandalorian s01x02.mp4" \
        "Skiing Trip.mp4" \
        "aladdin.1992.avi" \
        "aladdin.2019.avi" \
        "archer.2009.s10e07.webrip.x264-lucidtv.mp4" \
        "game.of.thrones.01x05-eztv.mp4" \
        "homework.txt" \
        "kill.bill.2003.ts" \
        "lost s01e01-02.mp4" \
        "made up movie.mp4" \
        "made up show s01e10.mkv" \
        "s.w.a.t.2017.s02e01.mkv" \
        "scan001.tiff" \
        "temp.zip"

venv: clean-venv
	$(info * initializing venv)
	@python3 -m venv venv
	$(info * installing dev requirements)
	@./venv/bin/pip install -qU pip
	@./venv/bin/pip install -qr requirements-dev.txt
