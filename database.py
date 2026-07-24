import sqlite3


DATABASE_FILE = "/home/artur/minecraft-panel/minecraft.db"


def get_connection():

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


def init_database():

    connection = get_connection()

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

    connection.close()


def add_server(
    name: str,
    version: str,
    port: int,
    path: str
):

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO servers
        (name, version, port, path)
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

    connection.close()


def get_server_by_name(name: str):

    connection = get_connection()

    server = connection.execute(
        """
        SELECT *
        FROM servers
        WHERE name = ?
        """,
        (name,)
    ).fetchone()

    connection.close()

    if server is None:

        return None

    return dict(server)


def get_all_servers():

    connection = get_connection()

    servers = connection.execute(
        """
        SELECT *
        FROM servers
        ORDER BY id
        """
    ).fetchall()

    connection.close()

    return [
        dict(server)
        for server in servers
    ]


def remove_server(name: str):

    connection = get_connection()

    connection.execute(
        """
        DELETE FROM servers
        WHERE name = ?
        """,
        (name,)
    )

    connection.commit()

    connection.close()