#!/usr/bin/env bash
# Refresh the CURRENT Overleaf package (paper/overleaf-rev2-v2/) and rebuild
# its zip. The original paper/overleaf-rev2/ package is a frozen snapshot and
# is intentionally left untouched; package READMEs are hand-authored.
set -euo pipefail
REV2="$(cd "$(dirname "$0")/.." && pwd)"
PKG="$REV2/../overleaf-rev2-v2"
mkdir -p "$PKG/generated" "$PKG/figs" "$PKG/sections"
cp "$REV2/main.tex" "$PKG/"
cp "$REV2"/sections/*.tex "$PKG/sections/"
cp "$REV2"/generated/numbers.tex "$REV2"/generated/segment_table.tex \
   "$REV2"/generated/numbers.json "$REV2"/generated/numbers_manifest.json "$PKG/generated/"
cp "$REV2/refs.bib" "$PKG/"
cp "$REV2"/figs/*.pdf "$PKG/figs/"
rm -f "$PKG/../overleaf-rev2-v2-upload.zip"
(cd "$PKG" && zip -r -X ../overleaf-rev2-v2-upload.zip . -x '*.DS_Store' '*__MACOSX*' >/dev/null)
echo "Synced $PKG; rebuilt overleaf-rev2-v2-upload.zip"
