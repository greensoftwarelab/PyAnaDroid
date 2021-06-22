# !/bin/bash

rm -rf dist/*
python -m incremental.update anadroid --patch
git add anadroid/_version.py
git commit -m "bump _version"
python setup.py sdist
python -m twine upload dist/*
git push origin dev