#!/bin/bash
set -euox pipefail

docker-compose up --build
chown -R ${SUDO_GID}:${SUDO_UID} distfiles
