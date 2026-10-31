#!/bin/sh
# Stellt die auszuliefernden Website-Dateien in einem Ordner zusammen.
# Aus images/ und fonts/ kommen nur Dateien mit, auf die HTML oder CSS verweisen.
# Aufruf: ./build.sh [zielordner]   (Standard: _site)
set -eu
cd "$(dirname "$0")"
OUT="${1:-_site}"
PAGES="index.html impressum.html datenschutz.html styles.css"

rm -rf "$OUT"
mkdir -p "$OUT"
cp $PAGES "$OUT"/

for f in images/* fonts/*; do
  [ -f "$f" ] && [ "$f" != fonts/OFL.txt ] || continue
  if grep -qF "$f" $PAGES; then
    mkdir -p "$OUT/$(dirname "$f")"
    cp "$f" "$OUT/$f"
  else
    echo "  nicht verwendet, ausgelassen: $f"
  fi
done

# Lizenz der Schrift (SIL OFL) gehört zu den Schriftdateien
cp fonts/OFL.txt "$OUT"/fonts/

echo "Build fertig: $OUT"
