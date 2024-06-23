import os
import sqlite3
import time

from errors import DBException


class SQLiteDB:
    def __init__(self, materials_dir):
        """Setup SQL connection and returns cursor and connection"""
        self.materials_dir = materials_dir
        self.conn = None
        self.db = None

    def __enter__(self):
        try:
            db_path = os.path.join(self.materials_dir, "materials.db")
            self.conn = sqlite3.connect(db_path)
            self.db = self.conn.cursor()
            self.create_table()
            return self
        except sqlite3.Error as e:
            raise DBException(f"Could not make a connection. Error: {e}")

    def create_table(self):
        """Creates table if one doesn't already exist called materials"""
        try:
            self.db.execute("""CREATE TABLE IF NOT EXISTS materials 
                    (id INTEGER PRIMARY KEY, 
                    material_name TEXT, 
                    date_modified REAL, 
                    date_rendered REAL 
                    )""")
        except sqlite3.Error as e:
            raise DBException(f"Error creating table: {e}")

    def insert_new_materials_db(self):
        """Inserts new materials if not found in database, else it updates the date modified if db is outdated
        a task list is also generated and returned if the modified files need updating."""
        try:
            existing_materials_db = self.db.execute(
                "SELECT material_name, date_modified, date_rendered FROM materials"
            ).fetchall()

            existing_materials_dict = {
                material[0]: {
                    "date_modified": material[1],
                    "date_rendered": material[2],
                }
                for material in existing_materials_db
            }

            for material in os.listdir(self.materials_dir):
                if material.endswith(".mb"):
                    material_path = os.path.join(self.materials_dir, material)
                    date_modified_timestamp = os.path.getmtime(material_path)
                    material_data = existing_materials_dict.get(material)

                    if material_data is None:
                        self.db.execute(
                            "INSERT INTO materials (material_name, date_modified, date_rendered) VALUES (?, ?, ?)",
                            (material, date_modified_timestamp, 0.0),
                        )
                    elif date_modified_timestamp > material_data["date_modified"]:
                        self.db.execute(
                            "UPDATE materials SET date_modified = ? WHERE material_name = ?",
                            (date_modified_timestamp, material),
                        )

            self.conn.commit()
        except (sqlite3.Error, OSError) as e:
            raise DBException(f"Error inserting or updating materials: {e}")

    def check_swatches(self, output_path):
        """Checks the current swatches in the output directory and generates a task list if necessary."""
        try:
            swatch_task_list = []
            materials_in_db = self.db.execute(
                "SELECT material_name FROM materials"
            ).fetchall()
            materials_in_db_list = [material[0] for material in materials_in_db]

            swatches_in_dir = os.listdir(output_path)
            existing_swatches = [swatch[:-7] for swatch in swatches_in_dir]

            for material in materials_in_db_list:
                if material not in existing_swatches:
                    swatch_task_list.append(material)

            return swatch_task_list
        except OSError as e:
            raise DBException(f"Error checking swatches: {e}")

    def generate_tasks(self, output_path):
        """Generates a task list for materials that need rendering."""

        try:
            material_tasks_db = self.db.execute(
                "SELECT material_name, date_modified, date_rendered FROM materials WHERE date_modified > date_rendered"
            ).fetchall()

            material_tasks = [material[0] for material in material_tasks_db]
            missing_swatches = self.check_swatches(output_path)

            task_list = list(set(material_tasks) | set(missing_swatches))

            if not task_list:
                return_message = "All files are up to date, no tasks to render."
            else:
                return_message = f"There are {len(task_list)} new or updated materials in the task list: {', '.join(task_list)}."

            return task_list, return_message
        except sqlite3.Error as e:
            raise DBException(f"Error creating task list: {e}")

    def update_db(self, rendered_list):
        """Updates the data_rendered time for each material that is rendered from the task list."""
        try:
            date_rendered = time.time()

            self.db.executemany(
                "UPDATE materials SET date_rendered = ? WHERE material_name = ?",
                [(date_rendered, material) for material in rendered_list],
            )
            self.conn.commit()
            return None
        except sqlite3.Error as e:
            raise DBException(f"Error updating database: {e}")

    def delete_from_db(self):
        """Deletes materials from the database that are no longer in the materials directory."""
        try:
            materials_in_db = self.db.execute(
                "SELECT material_name FROM materials"
            ).fetchall()
            materials_in_db_list = [material[0] for material in materials_in_db]
            materials_in_dir = os.listdir(self.materials_dir)

            files_to_delete = [
                material
                for material in materials_in_db_list
                if material not in materials_in_dir
            ]

            if files_to_delete:
                deletion_placeholder = ", ".join("?" for material in files_to_delete)

                self.db.execute(
                    f"DELETE FROM materials WHERE material_name IN ({deletion_placeholder})",
                    files_to_delete,
                )
            self.conn.commit()
            return None
        except (sqlite3.Error, OSError) as e:
            raise DBException(f"Error deleting from database: {e}")

    def close_db(self):
        """Closes the connection and cursor once the script is complete."""
        try:
            self.db.close()
            self.conn.close()
        except sqlite3.Error as e:
            raise DBException(f"Error closing database: {e}")

    def update_log(self):
        """Updates the log by creating a table if it doesn't already exist, inserting new materials, and deleting missing ones."""
        try:
            self.insert_new_materials_db()
            self.delete_from_db()

            return self.conn, self.db
        except DBException as e:
            raise DBException(f"Error: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_db()
