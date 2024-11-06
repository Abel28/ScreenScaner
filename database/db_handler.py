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
                    action TEXT DEFAULT 'none',
                    image BLOB,
                    threshold REAL DEFAULT 0.8,
                    click_x INTEGER DEFAULT 0,
                    click_y INTEGER DEFAULT 0
                )
            """)

    def insert_region(self, filename, x1, y1, x2, y2, image_data=None, threshold=0.8, click_offset=(0, 0)):
        with self.conn:
            self.conn.execute("""
                INSERT INTO regions (filename, x1, y1, x2, y2, image, threshold, click_x, click_y)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (filename, x1, y1, x2, y2, image_data, threshold, click_offset[0], click_offset[1]))

    def get_all_regions(self):
        with self.conn:
            return self.conn.execute("SELECT * FROM regions").fetchall()

    def update_action(self, region_id, action):
        with self.conn:
            self.conn.execute("""
                UPDATE regions SET action = ? WHERE id = ?
            """, (action, region_id))

    def delete_region(self, filename):
        with self.conn:
            cursor = self.conn.cursor()
            try:
                cursor.execute("DELETE FROM regions WHERE filename = ?", (filename,))
                self.conn.commit()
            except Exception as e:
                print(f"Error al eliminar la región de la base de datos: {e}")
            finally:
                cursor.close()

    def delete_region(self, filename):
        with self.conn:
            cursor = self.conn.cursor()
            try:
                cursor.execute("DELETE FROM regions WHERE filename = ?", (filename,))
                self.conn.commit()
            except Exception as e:
                print(f"Error al eliminar la región de la base de datos: {e}")
            finally:
                cursor.close()

    def get_image_data(self, filename):
        """
        Recupera los datos de la imagen y el offset guardado en la base de datos.

        Args:
            filename (str): El nombre del archivo de la región en la base de datos.

        Returns:
            tuple: (image_data, click_x, click_y) o (None, None, None) si no se encuentra.
        """
        with self.conn:
            cursor = self.conn.execute("""
                SELECT image, click_x, click_y FROM regions WHERE filename = ?
            """, (filename,))
            result = cursor.fetchone()
            
            if result:
                image_data, click_x, click_y = result
                return image_data, click_x, click_y
            else:
                return None, None, None
        
    def get_image_data_and_threshold(self, filename):
        with self.conn:
            cursor = self.conn.execute("""
                SELECT image, threshold FROM regions WHERE filename = ?
            """, (filename,))
            result = cursor.fetchone()
            
            if result:
                image_data, threshold = result
                return image_data, threshold
            else:
                return None, None

    def update_threshold(self, filename, new_threshold):
        with self.conn:
            self.conn.execute("""
                UPDATE regions
                SET threshold = ?
                WHERE filename = ?
            """, (new_threshold, filename))

    def update_offset(self, filename, click_x, click_y):
        with self.conn:
            self.conn.execute("""
                UPDATE regions SET click_x = ?, click_y = ? WHERE filename = ?
            """, (click_x, click_y, filename))

    def close(self):
        self.conn.close()
