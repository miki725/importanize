.PHONY: clean-pyc clean-build docs clean

PYTEST_FLAGS=-sv --doctest-modules --ignore=tests/test_data
COVER_FLAGS=--cov=importanize --cov-report=term-missing

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
	pytest ${PYTEST_FLAGS} tests/ importanize/

coverage: clean  ## run all tests with coverage
	pytest ${PYTEST_FLAGS} ${COVER_FLAGS} tests/ importanize/

test-all: clean  ## run all tests with tox with different python/django versions
	tox

check: lint clean coverage   ## check library which runs lint and tests

release: clean  ## push release to pypi
	python setup.py sdist bdist_wheel upload

dist: clean  ## create distribution of the library
	python setup.py sdist bdist_wheel
	ls -l dist

watch:  ## watch file changes to run a command, e.g. make watch py.test tests/
	@if ! type "fswatch" 2> /dev/null; then \
		echo "Please install fswatch" ; \
	else \
		echo "Watching $(PWD) to run: $(WATCH_ARGS)" ; \
		while true; do \
			$(WATCH_ARGS) ; \
			fswatch -1 -r --exclude '.*(git|~)' . > /dev/null; \
			sleep 1; \
		done \
	fi;

# If the first argument is "watch"...
ifeq (watch,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "watch"
  WATCH_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(WATCH_ARGS):;@:)
endif
