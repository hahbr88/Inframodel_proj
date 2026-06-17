#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

set -a
# shellcheck disable=SC1091
source .env
set +a

root_password="$(cat secrets/root_password.txt)"

docker exec galera-node1 mariadb -uroot -p"$root_password" "$MARIADB_DATABASE" -e "
CREATE TABLE IF NOT EXISTS galera_test (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  node_name VARCHAR(64) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
INSERT INTO galera_test(node_name) VALUES ('galera-node1');
"

for container in galera-node1 galera-node2 galera-node3; do
    echo "=== $container ==="
    docker exec "$container" mariadb -uroot -p"$root_password" "$MARIADB_DATABASE" \
      -e "SELECT * FROM galera_test ORDER BY id DESC LIMIT 5;"
done
