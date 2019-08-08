#!/bin/bash

set -ex

VERSION=$(cat version)

sed -i "" -e "s/    version=\"[[:digit:]]*\.[[:digit:]]*\.[[:digit:]]*\",/    version=\"$VERSION\",/g" setup.py
sed -i "" -e "s/SDK_VERSION = '[[:digit:]]*\.[[:digit:]]*\.[[:digit:]]*'/SDK_VERSION = '$VERSION'/g" berbix/__init__.py

git add setup.py berbix/__init__.py version
git commit -m "Updating Berbix Python SDK version to $VERSION"
git tag -a $VERSION -m "Version $VERSION"
git push --follow-tags

rm -rf dist

python setup.py sdist bdist_wheel
twine upload dist/*
