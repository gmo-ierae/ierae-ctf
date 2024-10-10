#!/bin/bash
set -eu

CHALLENGE=futari-apis

if [ -d distfiles ]; then
    rm -r distfiles
fi

mkdir distfiles
cp -r challenge distfiles/$CHALLENGE

mv "distfiles/$CHALLENGE/compose.local.yaml" "distfiles/$CHALLENGE/compose.yaml"