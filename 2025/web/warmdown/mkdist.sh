#!/bin/bash
set -eu

if [ -d distfiles ]; then
    rm -r distfiles
fi
cp -r challenge distfiles
find distfiles -maxdepth 3 -type d -name node_modules | xargs --no-run-if-empty rm -r

mv "distfiles/compose.local.yaml" "distfiles/compose.yaml"
