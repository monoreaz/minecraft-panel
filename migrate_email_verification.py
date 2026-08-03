from database import get_connection


def get_user_column_names(
    connection
):
    columns = connection.execute(
        "PRAGMA table_info(users)"
    ).fetchall()

    return {
        column["name"]
        for column in columns
    }


def migrate():
    connection = get_connection()

    try:
        column_names = (
            get_user_column_names(
                connection
            )
        )

        if (
            "email_verified"
            not in column_names
        ):
            connection.execute(
                """
                ALTER TABLE users
                ADD COLUMN email_verified
                INTEGER NOT NULL DEFAULT 1
                """
            )

            print(
                "Added users.email_verified"
            )

        else:
            print(
                "users.email_verified already exists"
            )

        connection.execute(
            """
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
            """
        )

        connection.commit()

        print(
            "Email verification migration completed"
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    migrate()