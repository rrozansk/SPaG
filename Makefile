################################################################################
#                                                                              #
#                                 Makefile                                     #
#                                                                              #
# A collection of commands to help simplify and streamline development.        #
#                                                                              #
################################################################################

# Set the default to help if make is called with no target.
.DEFAULT_GOAL := help

# Set the default python version to run against for the env target.
PYTHON_VERSION := python3.7

################################################################################
#                                                                              #
# Print a help message showing all supported make recipes with a brief         #
# explanation of each.                                                         #
#                                                                              #
################################################################################
.PHONY: help
help:
	@printf '****************************** SUPPORTED COMMANDS ******************************\n'
	@printf '$$ make help             Print this message and exit.\n'
	@printf '$$ make env              Construct a virtual env with dependencies.\n'
	@printf '$$ make lint             Lint all the code using pylint.\n'
	@printf '$$ make test             Unit test SPaG using pytest and generate a report.\n'
	@printf '$$ make distro           Build varying distributions of SPaG.\n'
	@printf '$$ make install          Install SPaG from source.\n'
	@printf '$$ make clean            Remove compiled, temp, and any installed files.\n'
	@printf '$$ make sanity           Perform the linting and testing targets.\n'
	@printf '$$ make test3.5          Perform sanity with python3.5.\n'
	@printf '$$ make test3.6          Perform sanity with python3.6.\n'
	@printf '$$ make test3.7          Perform sanity with python3.7.\n'
	@printf '$$ make all              Perform sanity on all SPaG supported python versions.\n'
	@printf '$$ make test_upload      Test repository upload with test PyPI.\n'
	@printf '$$ make upload           Upload built distributions to PyPI.\n'
	@printf '$$ make test_download    Test SPaG download and install from test PyPI.\n'
	@printf '$$ make download         Download and install SPaG from PyPI.\n'

################################################################################
#                                                                              #
# Construct a virtual environment with all the required dependencies for       #
# testing installed.                                                           #
#                                                                              #
################################################################################
.PHONY: env
env: requirements.txt
	pip install virtualenv
	virtualenv --python=${PYTHON_VERSION} testing_venv
	. testing_venv/bin/activate; \
	pip install -r requirements.txt; \
	make install; \
	deactivate

################################################################################
#                                                                              #
# Lint the python code using pytest and the defined .pylintrc specification    #
# located at the root of the repository.                                       #
#                                                                              #
################################################################################
.PHONY: lint
lint: .pylintrc
	@find . -type d \( -name 'testing_venv' -o -name 'SPaG.egg-info' \
	-o -name 'build' -o -name 'dist' -o -name 'examples' \) \
	-prune -o -type f -name '*.py' -exec pylint --rcfile=.pylintrc '{}' +

################################################################################
#                                                                              #
# Test the python code using pytest and the configuration file (pytest.ini)    #
# present at the root of the repository.                                       #
#                                                                              #
################################################################################
.PHONY: test
test: pytest.ini
	@pytest -c pytest.ini

################################################################################
#                                                                              #
# Create distributions from the current source.                                #
#                                                                              #
################################################################################
.PHONY: distro
distro: setup.py
	python setup.py sdist bdist_wheel

################################################################################
#                                                                              #
# Install the project from source.                                             #
#                                                                              #
################################################################################
.PHONY: install
install: setup.py
	python setup.py install

################################################################################
#                                                                              #
# Remove and delete any temporary or compiled files as well as testing         #
# artifacts.                                                                   #
#                                                                              #
################################################################################
.PHONY: clean
clean:
	\rm -rf testing_venv
	\rm -rf SPaG.egg-info/ build/ dist/
	\find . -type f -name '*~' -delete
	\find . -type f -name '*.o' -delete
	\find . -type f -name '*.swp' -delete
	\find . -type f -name 'out_*' -delete
	\find . -type f -name '.spagrc' -delete
	\find . -type f -name '*.py[cod]' -delete
	\find . -type f -name '.coverage' -delete
	\find . -type d -name '__pycache__' -exec rm -rf '{}' +
	\find . -type d -name '.pytest_cache' -exec rm -rf '{}' +
	\find /usr/local/bin/ -type f -name 'spag_cli' -delete
	\find /usr/local/lib/python* -type d -name 'SPaG-*' -exec rm -rf '{}' +

################################################################################
#                                                                              #
# Run sanity testing on the code with the help of other recipes.               #
#                                                                              #
################################################################################
.PHONY: sanity
sanity: env
	-. testing_venv/bin/activate; make lint && make test; deactivate
	$(MAKE) clean

################################################################################
#                                                                              #
# Run sanity with python version 3.5 with the help of other recipes.           #
#                                                                              #
################################################################################
.PHONY: test3.5
test3.5:
	-$(MAKE) sanity -e PYTHON_VERSION=python3.5
	mv test_report.html test_report_py3.5.html

################################################################################
#                                                                              #
# Run sanity with python version 3.6 with the help of other recipes.           #
#                                                                              #
################################################################################
.PHONY: test3.6
test3.6:
	-$(MAKE) sanity -e PYTHON_VERSION=python3.6
	mv test_report.html test_report_py3.6.html

################################################################################
#                                                                              #
# Run sanity with python version 3.7 with the help of other recipes.           #
#                                                                              #
################################################################################
.PHONY: test3.7
test3.7:
	-$(MAKE) sanity -e  PYTHON_VERSION=python3.7
	mv test_report.html test_report_py3.7.html

################################################################################
#                                                                              #
# Run sanity on all supported python versions with the help of other recipes.  #
#                                                                              #
################################################################################
.PHONY: all
all:
	-$(MAKE) test3.5
	-$(MAKE) test3.6
	-$(MAKE) test3.7

################################################################################
#                                                                              #
# Test built SPaG package distributions are uploaded properly by pushing them  #
# to the test PyPI repository.                                                 #
# NOTE: Requires authentication. Must be an authorized maintainer.             #
#                                                                              #
################################################################################
.PHONY: test_upload
test_upload: distro
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

################################################################################
#                                                                              #
# Upload built SPaG package distributions to the PyPI repository.              #
# NOTE: Requires authentication. Must be an authorized maintainer.             #
#                                                                              #
################################################################################
.PHONY: upload
upload: distro
	twine upload dist/*

################################################################################
#                                                                              #
# Test SPaG package download and installation from the test PyPI repository.   #
#                                                                              #
################################################################################
.PHONY: test_download
test_download:
	pip install --index-url https://test.pypi.org/simple/ SPaG

################################################################################
#                                                                              #
# Download and install the SPaG package distribution from the PyPI repository. #
#                                                                              #
################################################################################
.PHONY: download
download:
	pip install SPaG
