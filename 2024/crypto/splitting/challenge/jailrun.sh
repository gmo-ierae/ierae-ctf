#!/bin/bash

cp challenge.sage /tmp/
cd /tmp/

/usr/local/bin/sage-entrypoint sage challenge.sage
