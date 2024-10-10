#!/bin/bash
set -eu

CHALLENGE=simple-proxy

if [ -d distfiles ]; then
    rm -r distfiles
fi

mkdir distfiles
cp -r challenge "distfiles/$CHALLENGE"

echo "IERAE{dummy}" > "distfiles/$CHALLENGE/web/flag.txt"
mv "distfiles/$CHALLENGE/compose.local.yaml" "distfiles/$CHALLENGE/compose.yaml"
