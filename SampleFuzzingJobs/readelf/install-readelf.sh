#!/usr/bin/env bash
set -eu -o pipefail

mkdir -p /opt/binutils-2.28/binutils/
cp readelf /opt/binutils-2.28/binutils/readelf
chmod a+x /opt/binutils-2.28/binutils/readelf

tar -xzvf elfseeds.tgz -C /
chmod -R a+rwx /opt/seeds
