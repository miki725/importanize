.PHONY: clean-pyc clean-build docs clean

NOSE_FLAGS=-sv --with-doctest --rednose --exclude=test_data
COVER_CONFIG_FLAGS=--with-coverage --cover-package=importanize,tests --cover-tests --cover-erase
COVER_REPORT_FLAGS=--cover-html --cover-html-dir=htmlcov
COVER_FLAGS=${COVER_CONFIG_FLAGS} ${COVER_REPORT_FLAGS}

help:  ## show help
	@grep -E '^[a-zA-Z_\-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		cut -d':' -f1- | \
		sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## install all dependecies
	pip install -U -r requirements-dev.txt

clean: clean-build clean-pyc clean-test  ## clean everything except tox

clean-build:  ## clean build and distribution artifacts
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info

clean-pyc:  ## clean pyc files
	-@find . -path ./.tox -prune -o -name '*.pyc' -follow -print0 | xargs -0 rm -f
	-@find . -path ./.tox -prune -o -name '*.pyo' -follow -print0 | xargs -0 rm -f
	-@find . -path ./.tox -prune -o -name '__pycache__' -type d -follow -print0 | xargs -0 rm -rf

clean-test:  ## clean test artifacts like converage
	rm -rf .coverage coverage*
	rm -rf htmlcov/

clean-all: clean  ## clean everything including tox
	rm -rf .tox/

lint: clean  ## lint whole library
	if python -c "import sys; exit(1) if sys.version[:3] < '3.6' else exit(0)"; \
	then \
		pre-commit run --all-files ; \
	fi

test: clean  ## run all tests
	nosetests ${NOSE_FLAGS} tests/

coverage: clean  ## run all tests with coverage
	nosetests ${NOSE_FLAGS} ${COVER_FLAGS} tests/

test-all: clean  ## run all tests with tox with different python/django versions
	tox

check: lint clean coverage   ## check library which runs lint and tests

release: clean  ## push release to pypi
	python setup.py sdist bdist_wheel upload

dist: clean  ## create distribution of the library
	python setup.py sdist bdist_wheel
	ls -l dist
