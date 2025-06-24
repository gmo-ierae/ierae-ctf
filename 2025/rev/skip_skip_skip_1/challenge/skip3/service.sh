#!/bin/bash
set -euox pipefail

socat TCP-LISTEN:${PORT},reuseaddr,fork SYSTEM:'export CASE_NUMBER=`date +%y%m%d-%H%M%S-%N` && export LOG_DIR=${LOG_BASE}/${CASE_NUMBER} && mkdir ${LOG_DIR} && ./challenge.py 2> ${LOG_DIR}/challenge.log'
