################################################################################
#                                                                              #
#                                 Makefile                                     #
#                                                                              #
# A collection of commands to help simplify and streamline development.        #
#                                                                              #
################################################################################

# Set the default to help if make is called with no target.
.DEFAULT_GOAL := help

################################################################################
#                                                                              #
# Print a help message showing all supported make recipes with a brief         #
# explanation of each.                                                         #
#                                                                              #
################################################################################
.PHONY: help
help:
	@printf '*********************** SUPPORTED COMMANDS ***********************\n'
	@printf '$$ make help       Print this message and exit.\n'
	@printf '$$ make env        Construct a virtual env with dependencies.\n'
	@printf '$$ make lint       Lint all the code using pylint.\n'
	@printf '$$ make test       Unit test SPaG using pytest.\n'
	@printf '$$ make distro     Build varying distributions of SPaG.\n'
	@printf '$$ make install    Install SPaG from source.\n'
	@printf '$$ make clean      Remove compiled, temp, and any installed files.\n'
	@printf '$$ make sanity     Perform sanity with the help of other recipes.\n'

################################################################################
#                                                                              #
# Construct a virtual environment with all the required dependencies for       #
# testing installed.                                                           #
#                                                                              #
################################################################################
.PHONY: env
env:
	pip install virtualenv==16.0.0
	virtualenv testing_venv
	. testing_venv/bin/activate; \
	pip install pylint==1.9.1 pytest==3.8.0 pytest-cov==2.6.0; \
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
	@find scripts spag tests -type f -name '*.py' -exec pylint --rcfile=.pylintrc '{}' +

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
# Install the project from source.                                             #
#                                                                              #
################################################################################
.PHONY: install
install: setup.py
	python setup.py install

################################################################################
#                                                                              #
# Create distributions from the current source.                                #
#                                                                              #
################################################################################
.PHONY: distro
distro: setup.py
	python setup.py sdist bdist bdist_wheel

################################################################################
#                                                                              #
# Remove and delete any temporary or compiled files as well as testing         #
# artifacts.                                                                   #
#                                                                              #
################################################################################
.PHONY: clean
clean:
	\rm -rf testing_venv
	\rm -rf spag.egg-info/ build/ dist/
	\rm -rf /usr/local/bin/generate.py
	\rm -rf /usr/local/lib/python2.7/dist-packages/spag-*
	\find . -type f -name '*~' -delete
	\find . -type f -name '*.o' -delete
	\find . -type f -name '*.swp' -delete
	\find . -type f -name '*.py[cod]' -delete
	\find . -type f -name '.coverage' -delete
	\find . -type d -name '__pycache__' -exec rm -rf '{}' +
	\find . -type d -name '.pytest_cache' -exec rm -rf '{}' +

################################################################################
#                                                                              #
# Run sanity testing on the code with the help of other recipes.               #
#                                                                              #
################################################################################
.PHONY: sanity
sanity: env
	-. testing_venv/bin/activate; make lint && make test; deactivate
	$(MAKE) clean
