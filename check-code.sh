#!/usr/bin/env bash
#
# Run Python checkers and formatters.

echo "Sorting imports in grizzled"
for d in grizzled test
do
    isort "$d"/**/*.py
done

echo "Formatting grizzled and test with black"
for d in grizzled test
do
    black "$d"/*.py
done

echo "Checking types ..."
for d in grizzled test
do
    pyright "$d" || exit 1
done

echo "Linting ..."
for d in grizzled test
do
    ruff check "$d" || exit 1
done


p=$(type -p pycheck)
if [ -z "$p" ]
then
    echo "WARNING: pycheck not found"
else
    echo "Running pycheck ..."
    $p grizzled/**/*.py || exit 1
    $p test/**/*.py || exit 1
fi
