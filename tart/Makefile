
develop:
	pip3 install -e .

lint:
	pylint tart

test:
	pytest-3 -k TestVisibility

test_upload:
	python3 setup.py sdist
	twine upload --repository testpypi dist/*

upload:
	python3 setup.py sdist
	twine upload --repository pypi dist/*
