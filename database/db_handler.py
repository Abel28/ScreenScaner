import sqlite3

class DBHandler:
    def __init__(self, db_name="regions.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS regions (
                    id INTEGER PRIMARY KEY,
                    filename TEXT NOT NULL,
                    x1 INTEGER NOT NULL,
                    y1 INTEGER NOT NULL,
                    x2 INTEGER NOT NULL,
                    y2 INTEGER NOT NULL,
                    action TEXT DEFAULT 'none'
                )
            """)

    def insert_region(self, filename, x1, y1, x2, y2, action='none'):
        with self.conn:
            self.conn.execute("""
                INSERT INTO regions (filename, x1, y1, x2, y2, action)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (filename, x1, y1, x2, y2, action))

    def get_all_regions(self):
        with self.conn:
            return self.conn.execute("SELECT * FROM regions").fetchall()

    def update_action(self, region_id, action):
        with self.conn:
            self.conn.execute("""
                UPDATE regions SET action = ? WHERE id = ?
            """, (action, region_id))

    def delete_region(self, filename):
        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM regions WHERE filename = ?", (filename,))
            conn.commit()
        except Exception as e:
            print(f"Error al eliminar la región de la base de datos: {e}")
        finally:
            cursor.close()
            conn.close()


    def close(self):
        self.conn.close()
