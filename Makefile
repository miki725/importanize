.PHONY: clean-pyc clean-build docs clean
INSTALL_FILE ?= requirements-dev.txt
PYTEST_FLAGS=-svv --doctest-modules --ignore=tests/test_data

ifeq ($(shell python --version | grep -i pypy | wc -l),1)
	COVERAGE_FLAGS=--show-missing
else
	COVERAGE_FLAGS=--show-missing --fail-under=100
endif

importanize_files=$(shell find importanize -name "[!_]*.py" | cut -d/ -f2-)
test_files=$(shell find tests -maxdepth 1 -name "test_[!_]*.py" | cut -d/ -f2- | cut -d_ -f2-)
independentant_test_files=$(filter-out $(importanize_files),$(test_files))

help:  ## show help
	@grep -E '^[a-zA-Z_\-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		cut -d':' -f1- | \
		sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## install all requirements including for testing
	pip install -U -r $(INSTALL_FILE)
	pip freeze

clean: clean-build clean-pyc  ## clean everything except tox

clean-build:  ## clean build and distribution artifacts
	@rm -rf build/
	@rm -rf dist/

clean-pyc:  ## clean pyc files
	-@find . -path ./.tox -prune -o -name '*.pyc' -follow -print0 | xargs -0 rm -f
	-@find . -path ./.tox -prune -o -name '*.pyo' -follow -print0 | xargs -0 rm -f
	-@find . -path ./.tox -prune -o -name '__pycache__' -type d -follow -print0 | xargs -0 rm -rf

clean-coverage: clean  ## clean test artifacts like converage
	rm -rf .coverage coverage*
	rm -rf htmlcov/

clean-all: clean  ## clean everything including tox
	rm -rf .tox/

lint: clean  ## lint whole library
	if python -c "import sys; exit(1) if sys.version[:3] < '3.6' or getattr(sys, 'pypy_version_info', None) else exit(0)"; \
	then \
		pre-commit run --all-files ; \
	fi

test: clean  ## run all tests
	pytest ${PYTEST_FLAGS} ${PYTEST_DEBUG_FLAGS} importanize/ tests/

coverage/%:
	pytest ${PYTEST_FLAGS} ${PYTEST_DEBUG_FLAGS} \
		--cov=importanize \
		--cov-append \
		--cov-report= \
		tests/$(if $(findstring /,$*),$(shell echo $* | cut -d/ -f1)/test_$(shell echo $* | cut -d/ -f2),test_$*) \
		importanize/$*
	coverage report $(COVERAGE_FLAGS) --include=importanize/$*

coverage: clean-coverage  ## run all tests with coverage
	$(MAKE) $(addprefix coverage/,$(importanize_files))
	coverage report $(COVERAGE_FLAGS)
	coverage xml
	# running independant tests which do not correlate to a source file
	pytest $(addprefix tests/test_,$(independentant_test_files))

test-all: clean  ## run all tests with tox with different python/django versions
	tox

check: lint coverage   ## check library which runs lint and tests

dist: clean  ## build python package ditribution
	python setup.py sdist bdist_wheel
	ls -l dist

release: clean dist  ## package and upload a release
	twine upload dist/*

watch:  ## watch file changes to run a command, e.g. make watch py.test tests/
	@if ! type "fswatch" 2> /dev/null; then \
		echo "Please install fswatch" ; \
	else \
		echo "Watching $(PWD) to run: $(WATCH_ARGS)" ; \
		while true; do \
			reset; \
			$(WATCH_ARGS) ; \
			fswatch -1 -r --exclude '.*(git|~)' . > /dev/null; \
			sleep 1; \
		done \
	fi;

# If the first argument is "watch"...
ifeq (watch,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "watch"
  WATCH_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
endif
