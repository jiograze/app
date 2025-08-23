"""
Database migration to add missing tables and columns
"""

def migrate(connection):
    cursor = connection.cursor()
    
    # Create search_suggestions table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_text TEXT NOT NULL,
        search_type TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(query_text, search_type)
    )
    """)
    
    # Create search_index table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_index (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        vector BLOB,
        created_at TEXT NOT NULL,
        updated_at TEXT,
        FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
    )
    """)
    
    # Add missing columns to search_history if they don't exist
    try:
        cursor.execute("ALTER TABLE search_history ADD COLUMN query_text TEXT")
    except:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE search_history ADD COLUMN result_count INTEGER")
    except:
        pass  # Column already exists
    
    connection.commit()
    cursor.close()
