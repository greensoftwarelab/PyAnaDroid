# !/bin/bash

rm -rf dist/*
python3 -m incremental.update anadroid --patch
git add anadroid/_version.py
git commit -m "bump _version"
python3 setup.py sdist
python3 -m twine upload dist/*
git push origin main