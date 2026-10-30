#!/bin/sh
# Stellt die auszuliefernden Website-Dateien in einem Ordner zusammen.
# Aufruf: ./build.sh [zielordner]   (Standard: _site)
set -eu
cd "$(dirname "$0")"
OUT="${1:-_site}"

rm -rf "$OUT"
mkdir -p "$OUT"
cp index.html styles.css impressum.html datenschutz.html "$OUT"/
cp -R images "$OUT"/
echo "Build fertig: $OUT"
