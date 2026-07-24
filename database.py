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
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                version TEXT NOT NULL,
                port INTEGER UNIQUE NOT NULL,
                path TEXT NOT NULL
            )
        """)

        connection.commit()

    finally:
        connection.close()


def add_user(
    username: str,
    email: str,
    password_hash: str
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO users (
                username,
                email,
                password_hash
            )
            VALUES (?, ?, ?)
            """,
            (
                username,
                email,
                password_hash
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
    name: str,
    version: str,
    port: int,
    path: str
):
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO servers (
                name,
                version,
                port,
                path
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                version,
                port,
                path
            )
        )

        connection.commit()

    finally:
        connection.close()


def get_server_by_name(name: str):
    connection = get_connection()

    try:
        server = connection.execute(
            """
            SELECT *
            FROM servers
            WHERE name = ?
            """,
            (name,)
        ).fetchone()

        if server is None:
            return None

        return dict(server)

    finally:
        connection.close()


def get_all_servers():
    connection = get_connection()

    try:
        servers = connection.execute(
            """
            SELECT *
            FROM servers
            ORDER BY id
            """
        ).fetchall()

        return [
            dict(server)
            for server in servers
        ]

    finally:
        connection.close()


def remove_server(name: str):
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM servers
            WHERE name = ?
            """,
            (name,)
        )

        connection.commit()

    finally:
        connection.close()