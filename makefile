help:
	@echo
	@echo 'deployment:  build, publish, tag'
	@echo 'versioning:  bump-patch, bump-minor, bump-major'
	@echo 'setup:       setup-deps, setup-env, setup-demo'

# Testing helpers --------------------------------------------------------------

clean:
	$(info cleaning demo directory)
	@find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__
	@rm -rvf build dist *.egg-info demo


# Deployment Helpers -----------------------------------------------------------

build: clean
	python3 setup.py sdist bdist_wheel --universal

publish:
	twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

tag:
	git tag `vbump | egrep -o '[0-9].*'`


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
	    'demo/Avengers Infinity War'
	@cd demo && touch \
	    "aladdin.1992.avi" \
	    "aladdin.2019.avi" \
	    "Avengers Infinity War/Avengers.Infinity.War.wmv" \
	    "Avengers Infinity War/Avengers.Infinity.War.srt" \
	    "game.of.thrones.01x05-eztv.mp4" \
	    "homework.txt" \
	    "made up show s01e10.mkv" \
	    "made up movie.mp4" \
	    "archer.2009.s10e07.webrip.x264-lucidtv.mp4" \
	    "Planet Earth II S01E06 - Cities (2016) (2160p).mp4" \
	    "O.J. - Made in America S01EP03 (2016) (1080p).mp4" \
	    "s.w.a.t.2017.s02e01.mkv"
