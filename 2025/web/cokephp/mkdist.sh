#!/bin/bash
set -eu

if [ -d distfiles ]; then
    rm -r distfiles
fi
cp -r challenge distfiles
find distfiles -maxdepth 3 -type d -name node_modules | xargs --no-run-if-empty rm -r

sed -i -E 's/IERAE\{.+\}/IERAE\{REDACTED\}/g' "distfiles/compose.yaml"
