help:
	@echo
	@echo 'deployment:  build, publish, tag'
	@echo 'versioning:  bump-patch, bump-minor, bump-major'
	@echo 'setup:       setup-deps, setup-env, setup-demo'

clean:
	$(info cleaning demo directory)
	@find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__
	@rm -rvf build dist *.egg-info demo


# Deployment Helpers -----------------------------------------------------------

build: clean
	python3 setup.py sdist bdist_wheel --universal

publish:
	twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

publish-test:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

tag:
	git tag `vbump | egrep -o '[0-9].*'`

install:
	pip3 install --user -U .

# Version Helpers --------------------------------------------------------------

bump-patch:
	vbump --patch
	make sync-version
	git reset --
	git add mnamer/__version__.py
	git add pyproject.toml
	git commit -m "Patch version bump"

bump-minor:
	vbump --minor
	make sync-version
	git reset --
	git add mnamer/__version__.py
	git add pyproject.toml
	git commit -m "Minor version bump"

bump-major:
	vbump --major
	make sync-version
	git reset --
	git add mnamer/__version__.py
	git add pyproject.toml
	git commit -m "Major version bump"


# Setup Helpers ----------------------------------------------------------------

setup-deps:
	pip3 install -r requirements-dev.txt

setup-env:
	deactivate || true
	rm -rf venv
	virtualenv venv
	./venv/bin/pip install -r requirements-dev.txt

setup-demo: clean
	$(info setting up demo directory)
	@mkdir -p \
	    demo \
	    'demo/Avengers Infinity War' \
	    'demo/Sample' \
	    'demo/Downloads' \
	    'demo/Images/Photos'
	@cd demo && touch \
        "Avengers Infinity War/Avengers.Infinity.War.srt" \
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
