import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def connect_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


def create_tables():

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id SERIAL PRIMARY KEY,
            file_name VARCHAR(255),
            file_path TEXT,
            rows_count INTEGER,
            columns_count INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            dataset_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id SERIAL PRIMARY KEY,
            session_id INTEGER,
            question TEXT,
            answer TEXT,
            generated_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS charts (
            id SERIAL PRIMARY KEY,
            query_id INTEGER,
            chart_type VARCHAR(50),
            chart_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unsafe_attempts (
            id SERIAL PRIMARY KEY,
            question TEXT,
            code TEXT,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Old table compatibility
    cursor.execute("""
        ALTER TABLE datasets
        ADD COLUMN IF NOT EXISTS rows_count INTEGER;
    """)

    cursor.execute("""
        ALTER TABLE datasets
        ADD COLUMN IF NOT EXISTS columns_count INTEGER;
    """)

    connection.commit()

    cursor.close()
    connection.close()


def save_dataset(file_name, file_path, rows_count, columns_count):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO datasets
        (file_name, file_path, rows_count, columns_count)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        file_name,
        file_path,
        rows_count,
        columns_count
    ))

    dataset_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()
    connection.close()

    return dataset_id


def create_session(dataset_id):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO sessions (dataset_id)
        VALUES (%s)
        RETURNING id
    """, (dataset_id,))

    session_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()
    connection.close()

    return session_id


def save_query(session_id, question, answer, generated_code):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO queries
        (session_id, question, answer, generated_code)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        session_id,
        question,
        answer,
        generated_code
    ))

    query_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()
    connection.close()

    return query_id


def save_chart(query_id, chart_type, chart_data):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO charts
        (query_id, chart_type, chart_data)
        VALUES (%s, %s, %s)
    """, (
        query_id,
        chart_type,
        chart_data
    ))

    chart_id = cursor.fetchone()[0] if cursor.description else None
    connection.commit()

    cursor.close()
    connection.close()

    return chart_id


def get_history():

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            q.id,
            q.question,
            q.answer,
            q.created_at,
            c.chart_type,
            c.chart_data
        FROM queries AS q
        LEFT JOIN LATERAL (
            SELECT chart_type, chart_data
            FROM charts
            WHERE query_id = q.id
            ORDER BY created_at DESC, id DESC
            LIMIT 1
        ) AS c ON TRUE
        ORDER BY q.created_at DESC
        LIMIT 50
    """)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return rows


def delete_query(query_id):

    connection = connect_db()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT id FROM queries WHERE id = %s FOR UPDATE",
            (query_id,)
        )

        if cursor.fetchone() is None:
            connection.rollback()
            return False

        cursor.execute(
            "DELETE FROM charts WHERE query_id = %s",
            (query_id,)
        )
        cursor.execute(
            "DELETE FROM queries WHERE id = %s",
            (query_id,)
        )
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def delete_all_queries():

    connection = connect_db()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            DELETE FROM charts
            WHERE query_id IN (SELECT id FROM queries)
        """)
        cursor.execute("DELETE FROM queries")
        deleted_count = cursor.rowcount
        connection.commit()
        return deleted_count
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()