import sqlite3
import cv2

class DBHandler:
    def __init__(self, db_name="regions.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        self.update_database_structure()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS regions (
                    id INTEGER PRIMARY KEY,
                    filename TEXT NOT NULL,
                    x1 INTEGER,
                    y1 INTEGER,
                    x2 INTEGER,
                    y2 INTEGER,
                    action TEXT DEFAULT 'none',
                    image BLOB,
                    threshold REAL DEFAULT 0.9,
                    click_x INTEGER,
                    click_y INTEGER
                )
            """)

        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS image_recognitions (
                    id INTEGER PRIMARY KEY,
                    filename TEXT NOT NULL,
                    x1 INTEGER NOT NULL,
                    y1 INTEGER NOT NULL,
                    x2 INTEGER NOT NULL,
                    y2 INTEGER NOT NULL,
                    image BLOB,
                    threshold REAL DEFAULT 0.9,
                    recognized_text TEXT DEFAULT ''
                )
            """)

        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(regions)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'recognized_text' not in columns:
            with self.conn:
                self.conn.execute("ALTER TABLE regions ADD COLUMN recognized_text TEXT DEFAULT ''")
        
        if 'image_recognition_id' not in columns:
            with self.conn:
                self.conn.execute("ALTER TABLE regions ADD COLUMN image_recognition_id INTEGER REFERENCES image_recognitions(id)")
                
        self.conn.commit()
        
    def update_database_structure(self):
        cursor = self.conn.cursor()
        
        cursor.execute("PRAGMA table_info(regions)")
        columns = cursor.fetchall()
        column_info = {column[1]: column[3] for column in columns}
        
        if column_info.get("x1") == 0:
            return

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regions_temp (
                id INTEGER PRIMARY KEY,
                filename TEXT NOT NULL,
                x1 INTEGER,
                y1 INTEGER,
                x2 INTEGER,
                y2 INTEGER,
                action TEXT DEFAULT 'none',
                image BLOB,
                threshold REAL DEFAULT 0.9,
                click_x INTEGER,
                click_y INTEGER
            )
        """)

        cursor.execute("""
            INSERT INTO regions_temp (id, filename, x1, y1, x2, y2, action, image, threshold, click_x, click_y)
            SELECT id, filename, x1, y1, x2, y2, action, image, threshold, click_x, click_y FROM regions
        """)

        cursor.execute("DROP TABLE regions")

        cursor.execute("ALTER TABLE regions_temp RENAME TO regions")

        self.conn.commit()

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

    def insert_image_recognition(self, filename, x1, y1, x2, y2, image_data=None, threshold=0.9, recognized_text="", click_offset=(0, 0)):
        with self.conn:
            self.conn.execute("""
                INSERT INTO image_recognitions (filename, x1, y1, x2, y2, image, threshold, recognized_text, click_x, click_y)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (filename, x1, y1, x2, y2, image_data, threshold, recognized_text, click_offset[0], click_offset[1]))

    def insert_region_with_recognition(self, filename, x1, y1, x2, y2, image_data, threshold, recognized_text):
        with self.conn:
            cursor = self.conn.execute("""
                INSERT INTO image_recognitions (filename, x1, y1, x2, y2, image, threshold, recognized_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (filename, x1, y1, x2, y2, image_data, threshold, recognized_text))

            image_recognition_id = cursor.lastrowid

            self.conn.execute("""
                INSERT INTO regions (filename, x1, y1, x2, y2, image, threshold, image_recognition_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (filename, x1, y1, x2, y2, image_data, threshold, image_recognition_id))

    def close(self):
        self.conn.close()

    def insert_region(self, filename, x1, y1, x2, y2, image_data=None, threshold=0.9, click_offset=(0, 0)):
        with self.conn:
            self.conn.execute("""
                INSERT INTO regions (filename, x1, y1, x2, y2, image, threshold, click_x, click_y)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (filename, x1, y1, x2, y2, image_data, threshold, click_offset[0], click_offset[1]))
            
    def insert_region_from_import(self, filename, image, x1=None, y1=None, x2=None, y2=None, action=None, threshold=0.9, click_x=None, click_y=None):
        _, buffer = cv2.imencode('.png', image)
        image_data = buffer.tobytes()

        self.conn.execute("""
            INSERT INTO regions (filename, x1, y1, x2, y2, action, image, threshold, click_x, click_y)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (filename, x1, y1, x2, y2, action, image_data, threshold, click_x, click_y))
        self.conn.commit()
        
    def check_region_exists(self, filename):
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM regions WHERE filename = ?", (filename,))
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists