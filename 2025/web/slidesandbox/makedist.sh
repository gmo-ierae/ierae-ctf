#!/bin/bash
set -eu

CHALLENGE=slidesandbox

if [ -d distfiles ]; then
    rm -r distfiles
fi

mkdir distfiles
cp -r challenge "distfiles/$CHALLENGE"
find distfiles -maxdepth 4 -type d -name node_modules | xargs --no-run-if-empty rm -r

sed -i '' -E 's/IERAE\{.*\}/IERAE\{dummy\}/g' "distfiles/$CHALLENGE/compose.yaml"