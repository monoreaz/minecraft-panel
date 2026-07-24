import sqlite3
import sys


DATABASE_FILE = "/home/artur/minecraft-panel/minecraft.db"


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python migrate_server_ownership.py "
            "<owner_username>"
        )
        raise SystemExit(1)

    owner_username = sys.argv[1]

    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row

    try:
        user = connection.execute(
            """
            SELECT id, username
            FROM users
            WHERE username = ? COLLATE NOCASE
            """,
            (owner_username,)
        ).fetchone()

        if user is None:
            print(
                f"User '{owner_username}' was not found"
            )
            raise SystemExit(1)

        server_table = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'servers'
            """
        ).fetchone()

        if server_table is None:
            print("The servers table was not found")
            raise SystemExit(1)

        columns = connection.execute(
            "PRAGMA table_info(servers)"
        ).fetchall()

        column_names = {
            column["name"]
            for column in columns
        }

        if "user_id" in column_names:
            print(
                "The servers table already has a user_id column"
            )
            return

        connection.execute(
            "PRAGMA foreign_keys = OFF"
        )

        connection.execute(
            "BEGIN IMMEDIATE"
        )

        connection.execute(
            """
            ALTER TABLE servers
            RENAME TO servers_old
            """
        )

        connection.execute(
            """
            CREATE TABLE servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT COLLATE NOCASE NOT NULL,
                version TEXT NOT NULL,
                port INTEGER UNIQUE NOT NULL,
                path TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                UNIQUE (user_id, name)
            )
            """
        )

        connection.execute(
            """
            INSERT INTO servers (
                id,
                user_id,
                name,
                version,
                port,
                path
            )
            SELECT
                id,
                ?,
                name,
                version,
                port,
                path
            FROM servers_old
            """,
            (user["id"],)
        )

        connection.execute(
            "DROP TABLE servers_old"
        )

        connection.commit()

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        foreign_key_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if foreign_key_errors:
            print("Foreign key validation failed")

            for error in foreign_key_errors:
                print(tuple(error))

            raise SystemExit(1)

        server_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM servers
            WHERE user_id = ?
            """,
            (user["id"],)
        ).fetchone()[0]

        print("Migration completed successfully")
        print(
            f"Owner: {user['username']} "
            f"(user ID: {user['id']})"
        )
        print(
            f"Assigned servers: {server_count}"
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
