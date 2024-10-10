#!/bin/bash
set -eu

CHALLENGE=passwordless

if [ -d distfiles ]; then
    rm -r distfiles
fi

mkdir distfiles
cp -r challenge distfiles/$CHALLENGE

mv "distfiles/$CHALLENGE/compose.local.yml" "distfiles/$CHALLENGE/compose.yml"
