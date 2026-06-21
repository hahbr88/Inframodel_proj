# Stop Order

1. Stop HAProxy standby node.
2. Stop HAProxy active node.
3. Stop db3.
4. Stop db2.
5. Stop db1 last.

Keeping db1 as the last clean Galera node makes the next bootstrap path predictable for this lab.
