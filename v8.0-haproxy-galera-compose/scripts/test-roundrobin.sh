#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

set -a
# shellcheck disable=SC1091
source .env
set +a

app_password="$(cat secrets/app_password.txt)"

for i in $(seq 1 10); do
    printf '%02d ' "$i"
    docker exec db1 mariadb \
        -hhaproxy \
        -P3306 \
        -u"$MARIADB_USER" \
        -p"$app_password" \
        "$MARIADB_DATABASE" \
        --batch \
        --skip-column-names \
        -e "SELECT @@hostname;"
done
