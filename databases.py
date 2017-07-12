#!/usr/bin/python3
import sqlite3
import hashlib
from pathlib import Path

class SQL3_Manager():
    def __init__(self, file_name = None, table_name = "strings"):
        self.table_name = table_name
        isNewfile = False
        if file_name == None:
            file_name = "DB_default.db"
        db_file = Path(file_name)
        if not db_file.is_file():
            isNewfile = True
        self.con = sqlite3.connect(file_name)
        c = self.con.cursor()
        if isNewfile:
            c.execute("CREATE TABLE {}(ID INTEGER PRIMARY KEY AUTOINCREMENT, String text not null, Layer text not null, Weight int default 0)".format(self.table_name))
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
        c.execute('SELECT * FROM {} WHERE Layer=? ORDER BY RANDOM() LIMIT 1'.format(self.table_name), t)
        return c.fetchone()

    def pick_weight(self):
        pass

    def gen_hashID(self, string):
        m = hashlib.md5()
        m.update(string.strip().encode("utf-8"))
        return m.hexdigest()[:8]

    def add_string(self, string, layer = "rock"):
        c = self.con.cursor()
        t = (string, layer)
        c.execute("INSERT INTO {}(String,Layer) values (?,?)".format(self.table_name), t)
        self.con.commit()
        c.close()

    def parse_exel(self, filepath):
        pass


    def edit_string(self):
        pass

    def delete_string(self):
        pass

if __name__ == '__main__':
    db = SQL3_Manager()
    db.add_string("행복을 느끼기 위해서는 아무것도 필요없다. 내가 제어 할 수 있다.","rock")
    db.add_string("조심을 조심하라. 조심과 신중은 다르다.", "rock")
    db.add_string("유치원 아이들은 아무도 자기에게 노래를 못한다고 하는 사람이 없기 때문에 자기가 노래를 잘한다고 믿었던 것뿐이다.", "rock")
    print(db.pick_randomly("rock"))

