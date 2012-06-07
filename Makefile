# Copyright (C) 2003-2012, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

# This Makefile requires GNU Make.

SHELL=/bin/sh
PROJECT_DIR=$(shell pwd)
VERSION=$(shell cat VERSION)

TEST_DIR=${PROJECT_DIR}/test

SOURCE_DIR=${PROJECT_DIR}/ftputil

DOC_DIR=${PROJECT_DIR}/doc
STYLESHEET_PATH=${DOC_DIR}/default.css
DOC_SOURCES=$(subst d/,${DOC_DIR}/, d/ftputil.txt)
DOC_TARGETS=$(subst d/,${DOC_DIR}/, d/ftputil.html d/ftputil_ru.html)

SED=sed -i'' -r -e

PYTHONPATH=${PROJECT_DIR}:${TEST_DIR}

#TODO Some platforms call that script rst2html.py - allow both.
RST2HTML=rst2html

# Name test files. Make sure the long-running tests come last.
TEST_FILES=$(shell ls -1 ${TEST_DIR}/test_*.py | \
			 grep -v "test_real_ftp.py" | \
			 grep -v "test_public_servers.py" ) \
		   ${TEST_DIR}/test_real_ftp.py \
		   ${TEST_DIR}/test_public_servers.py

.PHONY: dist extdist test pylint docs clean register patch debdistclean debdist

# Patch various files to refer to a new version.
patch:
	@echo "Patching files"
	${SED} "s/^__version__ = '.*'/__version__ = \'`cat VERSION`\'/" \
		${SOURCE_DIR}/ftputil_version.py
	${SED} "s/^:Version:   .*/:Version:   ${VERSION}/" \
		${DOC_DIR}/ftputil.txt
	${SED} "s/^:Date:      .*/:Date:      `date +"%Y-%m-%d"`/" \
		${DOC_DIR}/ftputil.txt
	#TODO Add rules for Russian translation.
	${SED} "s/^Version: .*/Version: ${VERSION}/" PKG-INFO
	${SED} "s/(\/wiki\/Download\/ftputil-).*(\.tar\.gz)/\1${VERSION}\2/" \
		PKG-INFO

# Documentation
vpath %.txt ${DOC_DIR}

docs: ${DOC_SOURCES} ${DOC_TARGETS}

${DOC_DIR}/ftputil_ru.html: ${DOC_DIR}/ftputil_ru_utf8.txt
	${RST2HTML} --stylesheet-path=${STYLESHEET_PATH} --embed-stylesheet \
		--input-encoding=utf-8 $< $@

%.html: %.txt
	${RST2HTML} --stylesheet-path=${STYLESHEET_PATH} --embed-stylesheet $< $@

# Quality assurance
test:
	@echo "=== Running tests for ftputil ${VERSION} ===\n"
	if which python2.4; then \
		PYTHONPATH=${PYTHONPATH} python2.4 ${TEST_DIR}/test_python2_4.py; \
	else \
		echo "Tests specific for Python 2.4 have been skipped."; \
	fi
	for file in $(TEST_FILES); \
	do \
		echo $$file ; \
		PYTHONPATH=${PYTHONPATH} python $$file ; \
	done

pylint:
	pylint --rcfile=pylintrc ${PYLINT_OPTS} ${SOURCE_DIR}/*.py | less

# Prepare everything for making a distribution tarball.
dist: clean patch test pylint docs
	python setup.py sdist

extdist: test dist register

# Register package on PyPI.
register:
	@echo "Registering new version with PyPI"
	python setup.py register

# Remove files with `orig` suffix (caused by `hg revert`).
cleanorig:
	find ${PROJECT_DIR} -name '*.orig' -exec rm {} \;

# Remove generated files (but no distribution packages).
clean:
	rm -f ${DOC_TARGETS}
	# Use absolute path to ensure we delete the right directory.
	rm -rf ${PROJECT_DIR}/build

# Help testing test installations. Note that `pip uninstall`
# doesn't work if the package wasn't installed with pip.
remove_from_env:
	rm -rf ${VIRTUAL_ENV}/doc/ftputil
	rm -rf ${VIRTUAL_ENV}/lib/python2.7/site-packages/ftputil
