import sqlite3


DATABASE_FILE = "/home/artur/minecraft-panel/minecraft.db"


def get_connection():
    connection = sqlite3.connect(
        DATABASE_FILE,
        timeout=10
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_database():
    connection = get_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            email_verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
            DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS servers (
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
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS
            email_verification_codes (
            user_id INTEGER PRIMARY KEY,
            code_hash TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            last_sent_at INTEGER NOT NULL,
            failed_attempts INTEGER
            NOT NULL DEFAULT 0,

        FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE CASCADE
        )
    """)
        connection.commit()

    finally:
        connection.close()


def add_user(
    username: str,
    email: str,
    password_hash: str,
    email_verified: bool = False
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO users (
                username,
                email,
                password_hash,
                email_verified
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                username,
                email,
                password_hash,
                int(email_verified)
            )
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()

def get_user_by_id(user_id: int):
    connection = get_connection()

    try:
        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if user is None:
            return None

        return dict(user)

    finally:
        connection.close()


def get_user_by_username(username: str):
    connection = get_connection()

    try:
        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ? COLLATE NOCASE
            """,
            (username,)
        ).fetchone()

        if user is None:
            return None

        return dict(user)

    finally:
        connection.close()


def get_user_by_email(email: str):
    connection = get_connection()

    try:
        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ? COLLATE NOCASE
            """,
            (email,)
        ).fetchone()

        if user is None:
            return None

        return dict(user)

    finally:
        connection.close()


def add_server(
    user_id: int,
    name: str,
    version: str,
    port: int,
    path: str
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO servers (
                user_id,
                name,
                version,
                port,
                path
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name,
                version,
                port,
                path
            )
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def get_server_by_id(
    server_id: int,
    user_id: int
):
    connection = get_connection()

    try:
        server = connection.execute(
            """
            SELECT *
            FROM servers
            WHERE id = ?
              AND user_id = ?
            """,
            (
                server_id,
                user_id
            )
        ).fetchone()

        if server is None:
            return None

        return dict(server)

    finally:
        connection.close()


def get_server_by_name(
    name: str,
    user_id: int
):
    connection = get_connection()

    try:
        server = connection.execute(
            """
            SELECT *
            FROM servers
            WHERE name = ? COLLATE NOCASE
              AND user_id = ?
            """,
            (
                name,
                user_id
            )
        ).fetchone()

        if server is None:
            return None

        return dict(server)

    finally:
        connection.close()


def get_servers_by_user(user_id: int):
    connection = get_connection()

    try:
        servers = connection.execute(
            """
            SELECT *
            FROM servers
            WHERE user_id = ?
            ORDER BY id
            """,
            (user_id,)
        ).fetchall()

        return [
            dict(server)
            for server in servers
        ]

    finally:
        connection.close()


def get_all_server_ports():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT port
            FROM servers
            """
        ).fetchall()

        return [
            row["port"]
            for row in rows
        ]

    finally:
        connection.close()


def remove_server(
    server_id: int,
    user_id: int
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM servers
            WHERE id = ?
              AND user_id = ?
            """,
            (
                server_id,
                user_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()

def count_servers_by_user(user_id: int):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT COUNT(*) AS server_count
            FROM servers
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        return row["server_count"]

    finally:
        connection.close()   

def update_user_username(
    user_id: int,
    username: str
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE users
            SET username = ?
            WHERE id = ?
            """,
            (
                username,
                user_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def update_user_email(
    user_id: int,
    email: str,
    email_verified: bool = False
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE users
            SET email = ?,
                email_verified = ?
            WHERE id = ?
            """,
            (
                email,
                int(email_verified),
                user_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def update_user_password_hash(
    user_id: int,
    password_hash: str
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (
                password_hash,
                user_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()

def save_email_verification_code(
    user_id: int,
    code_hash: str,
    expires_at: int,
    last_sent_at: int
):
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO email_verification_codes (
                user_id,
                code_hash,
                expires_at,
                last_sent_at,
                failed_attempts
            )
            VALUES (?, ?, ?, ?, 0)

            ON CONFLICT(user_id)
            DO UPDATE SET
                code_hash = excluded.code_hash,
                expires_at = excluded.expires_at,
                last_sent_at = excluded.last_sent_at,
                failed_attempts = 0
            """,
            (
                user_id,
                code_hash,
                expires_at,
                last_sent_at
            )
        )

        connection.commit()

    finally:
        connection.close()


def get_email_verification_code(
    user_id: int
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM email_verification_codes
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def increment_verification_attempts(
    user_id: int
):
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE email_verification_codes
            SET failed_attempts =
                failed_attempts + 1
            WHERE user_id = ?
            """,
            (user_id,)
        )

        connection.commit()

    finally:
        connection.close()


def delete_email_verification_code(
    user_id: int
):
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM email_verification_codes
            WHERE user_id = ?
            """,
            (user_id,)
        )

        connection.commit()

    finally:
        connection.close()


def mark_user_email_verified(
    user_id: int
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE users
            SET email_verified = 1
            WHERE id = ?
            """,
            (user_id,)
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def delete_user(user_id: int):
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        connection.commit()

    finally:
        connection.close()