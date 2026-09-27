#!/usr/bin/env bash
#
# Run Python checkers and formatters.

echo "Checking types ..."
pyright grizzled || exit 1

echo "Linting ..."
ruff check grizzled || exit 1

echo "Sorting imports in grizzled"
isort grizzled/*.py

echo "Formatting grizzled with black"
black grizzled/*.py
