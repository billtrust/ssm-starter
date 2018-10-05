.PHONY: test

install:
	pip install -r requirements.txt

install-dev-deps:
	pip install -r requirements.dev.txt

setup:
	python setup.py install

test:
	make setup
	nosetests -v --exe -w ./test
	#unittest autodiscover equivalent:
	#python -m unittest discover -s ./test -p '*_test.py'

publish-test:
	rm -r dist/*
	python setup.py sdist
	twine upload -r pypitest dist/*

publish:
	rm -r dist/*
	python setup.py sdist
	twine upload dist/*
