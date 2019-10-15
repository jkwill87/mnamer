clean:
	$(info cleaning demo directory...)
	@find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__
	@rm -rf build dist *.egg-info demo


# Testing helpers --------------------------------------------------------------

demo: demo-setup
	@python3 -m mnamer --batch --recurse demo


# Sync Helpers -----------------------------------------------------------------

sync: setup-poetry sync-deps sync-version

sync-deps:
	python3 -m poetry export --without-hashes -f requirements.txt \
	    > requirements.txt
	python3 -m poetry export --without-hashes -f requirements.txt --dev \
	    > requirements-dev.txt

sync-version:
	@echo VERSION = \"`python3 -m poetry version | egrep -o '[0-9].*'`\" \
	    > mnamer/__version__.py
	@cat mnamer/__version__.py


# Deployment Helpers -----------------------------------------------------------

build: sync
	rm -rvf build dist *.egg-info
	python3 -m poetry build

publish:
	python3 -m poetry publish

tag:
    git tag python3 -m poetry version | egrep -o '[0-9].*'`

bump-patch:
    python3 -m poetry version patch
    make sync-version
    git reset --
    git add mnamer/__version__.py
    git add pyproject.toml
    git commit -m "Patch version bump"

bump-minor:
    python3 -m poetry version minor
    make sync-version
    git reset --
    git add mnamer/__version__.py
    git add pyproject.toml
    git commit -m "Minor version bump"

bump-major:
    python3 -m poetry version major
    make sync-version
    git reset --
    git add mnamer/__version__.py
    git add pyproject.toml
    git commit -m "Major version bump"


# Setup Helpers ----------------------------------------------------------------

setup-poetry:
	pip3 install --pre -U poetry
	python3 -m poetry update

setup-deps:
	pip3 install -r requirements-dev.txt

setup-env:
	deactivate || true
	rm -rf venv
	python3 -m virtualenv venv

setup-demo: clean
	$(info setting up demo directory...)
	@mkdir -p \
	    demo \
	    'demo/Avengers Infinity War'
	@cd demo && touch \
	    "Avengers Infinity War/Avengers.Infinity.War.wmv" \
	    "Avengers Infinity War/Avengers.Infinity.War.srt" \
	    "game.of.thrones.01x05-eztv.mp4" \
	    "homework.txt" \
	    "made up show s01e10.mkv" \
	    "made up movie.mp4" \
	    "archer.2009.s10e07.webrip.x264-lucidtv.mp4" \
	    "Planet Earth II S01E06 - Cities (2016) (2160p).mp4" \
	    "O.J. - Made in America S01EP03 (2016) (1080p).mp4"
