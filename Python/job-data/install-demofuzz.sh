#!/usr/bin/env bash
set -eux -o pipefail

mkdir -p /app
chmod -R a+rwx /app

chmod a+x demofuzz.exe
cp demofuzz.exe /app/

mkdir -p /seeds
chmod -R a+rwx /seeds

du -b data.bin
cp data.bin /seeds
