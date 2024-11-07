import sqlite3

class DBHandler:
    def __init__(self, db_name="entries.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Requisitos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER,
                description TEXT,
                FOREIGN KEY(entry_id) REFERENCES Entries(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS GivenWhenThen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER,
                type TEXT,
                description TEXT,
                FOREIGN KEY(entry_id) REFERENCES Entries(id)
            )
        """)
        self.conn.commit()

    def insert_entry(self):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO Entries DEFAULT VALUES")
        entry_id = cursor.lastrowid
        self.conn.commit()
        return entry_id

    def insert_requisito(self, entry_id, description):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO Requisitos (entry_id, description) VALUES (?, ?)", (entry_id, description))
        self.conn.commit()

    def insert_gwt(self, entry_id, gwt_type, description):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO GivenWhenThen (entry_id, type, description) VALUES (?, ?, ?)", (entry_id, gwt_type, description))
        self.conn.commit()

    def get_all_ids(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM Entries")
        return [row[0] for row in cursor.fetchall()]

    def get_entry_data(self, entry_id):
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT description FROM Requisitos WHERE entry_id=?", (entry_id,))
        requisitos = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT type, description FROM GivenWhenThen WHERE entry_id=?", (entry_id,))
        gwt_data = cursor.fetchall()

        return requisitos, gwt_data

    def close(self):
        self.conn.close()