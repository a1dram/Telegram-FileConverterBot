import sqlite3


class DataBase:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def add_user_id(self, user_id):
        try:
            with self.connection:
                return self.connection.execute("""INSERT INTO users ('user_id') VALUES (?)""", (user_id,))

        except sqlite3.IntegrityError:
            pass

    def add_user_name(self, user_id, name):
        with self.connection:
            return self.connection.execute("""UPDATE users SET user_name = ? WHERE user_id = ?""", (name, user_id))

    def add_language(self, user_id, language):
        with self.connection:
            return self.connection.execute("""UPDATE users SET language = ? WHERE user_id = ?""", (language, user_id))

    def add_file_id(self, user_id, file_id):
        with self.connection:
            return self.connection.execute("""UPDATE users SET file_id = ? WHERE user_id = ?""",
                                           (file_id, user_id))

    def add_wait_quality(self, user_id, wait_answer):
        with self.connection:
            return self.connection.execute("""UPDATE users SET wait_quality = ? WHERE user_id = ?""",
                                           (wait_answer, user_id))

    def add_file_type(self, user_id, file_type):
        with self.connection:
            return self.connection.execute("""UPDATE users SET file_type = ? WHERE user_id = ?""",
                                           (file_type, user_id))

    def add_file_format(self, user_id, file_format):
        with self.connection:
            return self.connection.execute("""UPDATE users SET file_format = ? WHERE user_id = ?""",
                                           (file_format, user_id))

    def add_file_quality(self, user_id, file_quality):
        with self.connection:
            return self.connection.execute("""UPDATE users SET quality = ? WHERE user_id = ?""",
                                           (file_quality, user_id))

    def add_file_title(self, user_id, title):
        with self.connection:
            return self.connection.execute("""UPDATE users SET title = ? WHERE user_id = ?""",
                                           (title, user_id))

    def add_new_file_title(self, user_id, new_title):
        with self.connection:
            return self.connection.execute("""UPDATE users SET new_title = ? WHERE user_id = ?""",
                                           (new_title, user_id))

    def add_audiotrack(self, user_id, audiotrack):
        with self.connection:
            return self.connection.execute("""UPDATE users SET add_audiotrack = ? WHERE user_id = ?""",
                                           (audiotrack, user_id))

    def get_user_id(self, user_id):
        with self.connection:
            try:
                result = self.connection.execute("""SELECT user_id FROM users WHERE user_id = ?""",
                                                 (user_id,)).fetchmany(1)[0]

                return bool(len(result))

            except IndexError:
                return False

    def get_language(self, user_id):
        with self.connection:
            try:
                return self.connection.execute(
                    """SELECT language FROM users WHERE user_id = ?""", (user_id,)).fetchone()[0]
            except:
                pass

    def get_file_type(self, user_id):
        with self.connection:
            return self.connection.execute("""SELECT file_type FROM users WHERE user_id = ?""",
                                           (user_id,)).fetchone()[0]

    def get_wait_quality(self, user_id):
        with self.connection:
            return self.connection.execute("""SELECT wait_quality FROM users WHERE user_id = ?""",
                                           (user_id,)).fetchone()[0]

    def get_audiotrack(self, user_id):
        with self.connection:
            return self.connection.execute("""SELECT add_audiotrack FROM users WHERE user_id = ?""",
                                           (user_id,)).fetchone()[0]

    def get_file_id(self, user_id):
        with self.connection:
            return self.connection.execute("""SELECT file_id FROM users WHERE user_id = ?""",
                                           (user_id,)).fetchone()[0]

    def get_file_format(self, user_id):
        with self.connection:
            return self.connection.execute("""SELECT file_format FROM users WHERE user_id = ?""",
                                           (user_id,)).fetchone()[0]

    def get_file_quality(self, user_id):
        with self.connection:
            return self.connection.execute("""SELECT quality FROM users WHERE user_id = ?""",
                                           (user_id,)).fetchone()[0]

    def get_file_title(self, user_id):
        with self.connection:
            return self.connection.execute("""SELECT title FROM users WHERE user_id = ?""",
                                           (user_id,)).fetchone()[0]

    def get_new_file_title(self, user_id):
        with self.connection:
            return self.connection.execute("""SELECT new_title FROM users WHERE user_id = ?""",
                                           (user_id,)).fetchone()[0]


db = DataBase('FileConventerBot.db')
