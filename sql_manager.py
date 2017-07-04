#!/usr/bin/python3
import sqlite3
from pathlib import Path

class SQLITE_Manager():
    def __init__(self, file_name=None, table_name=None):
        isNewfile = False
        if file_name == None:
            file_name = "Strings.db"
        db_file = Path(file_name)
        if not db_file.is_file():
            isNewfile = True
        self.con = sqlite3.connect(file_name)
        c = self.con.cursor()
        if isNewfile:
            c.execute("CREATE TABLE strings(ID INTEGER PRIMARY KEY AUTOINCREMENT, String text not null, Layer text not null, Weight int default 0)")
        self.set_layer('rock')
        self.con.commit()
        c.close()

    def __deinit__(self):
        self.con.close()

    def set_layer(self, layer):
        self.layer = layer

    def pick_randomly(self, layer):
        c = self.con.cursor()
        t = (layer,)
        c.execute('SELECT * FROM strings WHERE Layer=? ORDER BY RANDOM() LIMIT 1', t)
        return c.fetchone()

    def pick_weight(self):
        pass

    def add_string(self, string, layer):
        c = self.con.cursor()
        t = (string, layer)
        c.execute("INSERT INTO strings(String,Layer) values (?,?)", t)
        self.con.commit()
        c.close()

    def edit_string(self):
        pass

    def delete_string(self):
        pass


if __name__ == '__main__':
    db = SQLITE_Manager("Strings.db")
    db.add_string("String test","rock")
    db.add_string("String test2", "rock")
    db.add_string("String test3", "rock")
    print(db.pick_randomly("rock"))

