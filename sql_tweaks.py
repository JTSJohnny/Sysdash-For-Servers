import sqlite3


def dict_factory(cursor, row):
    """Turn rows into dictionaries"""
    fields = [description[0] for description in cursor.description]
    return {field: value for field, value in zip(fields, row)}


def setup_db(path: str):
    """Setup SQLite for optimal performance"""
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = dict_factory

    # https://www.sqlite.org/pragma.html
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=10000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA foreign_keys = ON;")

    return conn
