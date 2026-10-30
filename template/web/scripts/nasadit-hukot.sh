#!/usr/bin/env bash
# Nasazení na sdílený hosting s Apachem a SSH (hukot.net): postaví web, vyrobí .htaccess a nahraje dist/ do ~/www přes scp
# (rsync ani jednorázové „ssh host příkaz“ lshell na hukotu nepustí).
# S odpovědí v data/web.json (prihlaseni.odpoved) je web za přihlašovací branou, s "otevreny": true veřejný.
# Přístup v proměnných: HUKOT_USER (= název subdomény, např. dejiny.example.cz), HUKOT_KEY (soukromý klíč).
set -euo pipefail
cd "$(dirname "$0")/.."

: "${HUKOT_USER:?nastav HUKOT_USER (název subdomény)}"
HUKOT_HOST="${HUKOT_HOST:-ssh.vix.hukot.net}"
HUKOT_KEY="${HUKOT_KEY:-$HOME/.ssh/hukot}"

npm run data -- --nasazeni
npm run build

if [ -f netlify/edge-functions/brana.js ]; then   # export ji vyrobí jen s odpovědí
  HASH=$(grep -oE "[0-9a-f]{64}" netlify/edge-functions/brana.js)
  sed "s/{{HASH}}/$HASH/" htaccess.sablona > dist/.htaccess
  echo "Web je za přihlašovací branou."
else
  sed '/^# brána$/,/^# \/brána$/d' htaccess.sablona > dist/.htaccess
  echo "Web je veřejný (bez přihlášení)."
fi

# čistý ssh config: „Host *“ v ~/.ssh/config přidává cizí klíče a server pak odmítne (MaxAuthTries)
cd dist
scp -r -F /dev/null -i "$HUKOT_KEY" -o IdentitiesOnly=yes ./* .htaccess "$HUKOT_USER@$HUKOT_HOST:www/"
echo "Nahráno na https://$HUKOT_USER/"
