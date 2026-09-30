import sqlite3


def connect_db():

    return sqlite3.connect("assistant.db")


def create_database():

    connection = connect_db()
    cursor = connection.cursor()

    # Datasets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            rows INTEGER,
            columns INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Sessions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Queries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            question TEXT,
            model TEXT,
            code TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Charts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS charts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id INTEGER,
            chart_type TEXT,
            chart_path TEXT
        )
    """)

    # Unsafe attempts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unsafe_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def create_session():

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO sessions DEFAULT VALUES"
    )

    session_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return session_id


def save_dataset(filename, rows, columns):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO datasets
        (filename, rows, columns)
        VALUES (?, ?, ?)
        """,
        (
            filename,
            rows,
            columns
        )
    )

    connection.commit()
    connection.close()


def save_query(
    session_id,
    question,
    model,
    code,
    result
):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO queries
        (session_id, question, model, code, result)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            session_id,
            question,
            model,
            code,
            result
        )
    )

    query_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return query_id


def save_unsafe_attempt(code, reason):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO unsafe_attempts
        (code, reason)
        VALUES (?, ?)
        """,
        (
            code,
            reason
        )
    )

    connection.commit()
    connection.close()


def get_history():

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            question,
            model,
            code,
            result,
            created_at
        FROM queries
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    connection.close()

    return rows


create_database()