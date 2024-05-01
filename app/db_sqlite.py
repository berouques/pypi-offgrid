import sqlite3
import json

class DBSQLite:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.create_tables()

    def create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS packages (
                    name TEXT PRIMARY KEY,
                    info TEXT,
                    releases TEXT,
                    urls TEXT,
                    last_serial INTEGER
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS simple_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pkg_name TEXT UNIQUE,
                    links TEXT
                )
                """
            )
            
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    value TEXT
                )
                """
            )
            

    def get_prefs_value(self, key, default_value):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))

            row = cursor.fetchone()

            if row is not None:
                return row[0]
            else:
                return default_value

    def set_prefs_value(self, key, value):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

            conn.commit()


            
            
    def get_project_summary(self, pkg_name: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT info FROM packages WHERE name = ?", (pkg_name,))

            row = cursor.fetchone()

            if row is not None:
                info = json.loads(row[0])

                if 'summary' in info:
                    return info['summary']
                else:
                    return None
            else:
                return None
        pass            
            
            
    def delete_package(self, pkg_name: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Удалить из таблицы simple_links
            cursor.execute("DELETE FROM simple_links WHERE pkg_name = ?", (pkg_name,))

            # Удалить из таблицы packages
            cursor.execute("DELETE FROM packages WHERE name = ?", (pkg_name,))
            

    def save_simple_links(self, pkg_name: str, links: dict):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            serialized_links = json.dumps(links)
            data = (pkg_name, serialized_links)

            cursor.execute(
                """
                INSERT INTO simple_links (pkg_name, links)
                VALUES (?, ?)
                ON CONFLICT(pkg_name) DO UPDATE SET links = excluded.links
                """,
                data
            )


    def get_simple_links(self, project_name: str) -> list:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT links FROM simple_links WHERE pkg_name = ?", (project_name,))
            row = cursor.fetchone()

            if row is not None:
                links = json.loads(row[0])
                return [{link_text: link_href} for link_text, link_href in links.items()]
            else:
                return None


    def get_simple_links_old(self, project_name: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT links FROM simple_links WHERE pkg_name = ?", (project_name,))
            row = cursor.fetchone()

            if row is not None:
                return json.loads(row[0])
            else:
                return None

    def get_simple_all_names(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pkg_name FROM simple_links")
            rows = cursor.fetchall()
            return [row[0] for row in rows]


    def get_simple_advanced(self, pkg_mask=None, page_size=None, page_number=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = "SELECT pkg_name FROM simple_links"
            data = ()

            pkg_mask = pkg_mask.strip()

            if pkg_mask=='*':
                pkg_mask = None

            if pkg_mask is not None:
                query += " WHERE pkg_name LIKE ?"
                data += ('%' + pkg_mask + '%',)

            if page_size is not None and page_number is not None:
                query += " LIMIT ? OFFSET ?"
                data += (page_size, (page_number - 1) * page_size)

            cursor.execute(query, data)

            rows = cursor.fetchall()

            return [row[0] for row in rows]

        
        

    def save_package_json(self, pkg_name: str, pypi_json: dict):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            data = (pkg_name, json.dumps(pypi_json['info']), json.dumps(pypi_json['releases']), json.dumps(pypi_json['urls']), pypi_json['last_serial'])

            cursor.execute(
                """
                INSERT INTO packages (name, info, releases, urls, last_serial)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET info = excluded.info, releases = excluded.releases, urls = excluded.urls, last_serial = excluded.last_serial
                """,
                data
            )


    def get_project_info(self, pkg_name: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT info, releases, urls, last_serial FROM packages WHERE name = ?", (pkg_name,))

            row = cursor.fetchone()

            if row is not None:
                return json.loads(row[0])
            else:
                return None
            

