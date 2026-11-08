#!/bin/bash
# matricula_dl.sh URL OUT  -- stáhne obrázek z img.data.matricula-online.eu (URL s csrf+ctrl z prohlížeče)
# Do OUT zapíše jen skutečný JPEG; při chybě vrátí 1 a starý OUT nechá být.
tok=$(echo "$1" | sed -E 's/.*csrf=([^&]+).*/\1/')
PY=python3; $PY -c "" 2>/dev/null || PY=python; $PY -c "" 2>/dev/null || PY="py -3"
tmp="$2.$$.part"
trap 'rm -f "$tmp"' EXIT
$PY -I "$(dirname "$0")/slusne.py" curl -s -f -m 120 -e "https://data.matricula-online.eu/" \
  -b "shared_csrftoken=$tok" "$1" -o "$tmp" || { echo "Matricula nevrátila obrázek ($2) – URL nejspíš vypršela, vezmi novou z prohlížeče" >&2; exit 1; }
[ "$(head -c 3 "$tmp" | od -An -tx1 | tr -d ' \n')" = ffd8ff ] || { echo "Matricula místo obrázku vrátila něco jiného ($2) – vezmi novou URL z prohlížeče" >&2; exit 1; }
mv -f "$tmp" "$2"
echo "$2 $(( $(wc -c < "$2") / 1024 )) kB"
