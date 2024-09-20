import sqlite3
from flask import g

DATABASE = 'plots.db'

def get_db():
    """Get a database connection from the Flask application context."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    """Initializes the database by creating necessary tables."""
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS plots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            plot_html TEXT NOT NULL
        )
    ''')
    db.commit()

def store_plot(timestamp, plot_html):
    """Store a plot in the database."""
    db = get_db()
    db.execute(
        'INSERT INTO plots (timestamp, plot_html) VALUES (?, ?)',
        (timestamp, plot_html)
    )
    db.commit()

def get_plot_by_timestamp(timestamp):
    """Retrieve a plot from the database by timestamp."""
    db = get_db()
    cursor = db.execute(
        'SELECT plot_html FROM plots WHERE timestamp = ?',
        (timestamp,)
    )
    row = cursor.fetchone()
    return row['plot_html'] if row else None

def get_all_timestamps():
    """Retrieve all timestamps from the database."""
    db = get_db()
    cursor = db.execute('SELECT timestamp FROM plots ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    return [row['timestamp'] for row in rows]

def close_connection(exception):
    """Close the database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()
