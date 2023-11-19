# For development purposes, use the 'develop' target to install this package from the source repository (rather than the public python packages). This
# means that local changes to the code will automatically be used by the package on your machine.
# To do this type
#     make develop
# in this directory.
develop: venv
	${VENV}/pip3 install -e .

test: venv
	${VENV}/python3 -m pytest

lint:
	pylint --extension-pkg-whitelist=numpy --ignored-modules=numpy --extension-pkg-whitelist=astropy tart_tools

test_upload:
	python3 setup.py sdist
	twine upload --repository testpypi dist/*

upload:
	python3 setup.py sdist
	twine upload --repository pypi dist/*

include Makefile.venv

$(VENV):
	$(PY) -m venv --system-site-packages $(VENVDIR)
#       $(PY) -m venv $(VENVDIR)
	$(VENV)/python3 -m pip install --upgrade pip setuptools wheel
