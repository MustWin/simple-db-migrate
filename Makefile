# Makefile for simple-db-migrate

help:
	@echo
	@echo "Please use 'make <target>' where <target> is one of"
	@echo "  clean      to clean garbage left by builds and installation"
	@echo "  compile    to compile .py files (just to check for syntax errors)"
	@echo "  test       to execute all simple-db-migrate tests"
	@echo "  install    to install simple-db-migrate"
	@echo "  build      to build without installing simple-db-migrate"
	@echo "  dist       to create egg for distribution"
	@echo "  publish    to publish the package to PyPI"
	@echo

clean:
	@echo "Cleaning..."
	@rm -rf build dist simple_db_migrate.egg-info *.pyc **/*.pyc *~ *.migration *.foo
	@#removing test temp files
	@rm -rf `date +%Y`*

compile: clean
	@echo "Compiling source code..."
	@rm -rf simple_db_migrate/*.pyc
	@rm -rf tests/*.pyc
	@python -tt -m compileall simple_db_migrate
	@python -tt -m compileall tests

test: compile
	@make clean
	@echo "Starting tests..."
	@nosetests -s --verbose --with-coverage --cover-erase --cover-package=simple_db_migrate --cover-inclusive --cover-html tests
	@make clean

install:
	@/usr/bin/env python ./setup.py install

build:
	@/usr/bin/env python ./setup.py build

dist: clean
	@python setup.py sdist

publish: dist
	@python setup.py sdist upload

build_docker:
	sudo docker build --network=host -f Dockerfile . -t mikejihbe/simple-db-migrate:latest
	sudo docker push mikejihbe/simple-db-migrate:latest

build_sqlplus_docker:
	sudo docker build --network=host -f Dockerfile_sqlplus -t mikejihbe/sqlplus:latest .
	sudo docker push mikejihbe/sqlplus:latest

build_server_docker:
	sudo docker build --network=host -f Dockerfile_server -t mikejihbe/db-migrate-server:latest .
	sudo docker push mikejihbe/db-migrate-server:latest
