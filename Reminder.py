import json
import random

import sqlite3
import telepot
from telepot.delegate import per_chat_id, create_open
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, time


class sqler():
    def __init__(self, db_name, q):  # creation
        self.db_name = db_name
        try:
            con = sqlite3.connect(db_name)
            cursor = con.cursor()
            cursor.execute(q)
            con.commit()
            con.close()
            print("sqler: db creation done")
        except Exception as err:
            print("SQLITE ERR:", err)

    def read_pick_one(self, table_name):
        try:
            con = sqlite3.connect(self.db_name)
            cursor = con.cursor()
            cursor.execute('select * from %s' % table_name)
            rows = cursor.fetchall()
            idx = random.randrange(len(rows))
            row = rows[idx]
            con.commit()
            con.close()
            return row[1]  # string
        except Exception as err:
            print("SQLITE ERR:", err)


class Reminder(telepot.helper.ChatHandler):  # Never Die
    root_table = {"myString": [time(7, 45), time(12, 00)]}

    def __init__(self, seed_tuple, timeout):
        super(Reminder, self).__init__(seed_tuple, timeout)
        print("Reminder __init__")
        self.scheduler = BackgroundScheduler()
        self.sqler = sqler("myDB.db", "CREATE TABLE myString(id int, sentence text)")
        self.init_scheduler()

        print("pickone:", self.sqler.read_pick_one("myString"))
        self.sender.sendMessage(self.sqler.read_pick_one("myString"))

    def open(self, initial_msg, seed):
        self.sender.sendMessage('Func: OPEN()')
        return True  # prevent on_message() from being called on the initial message

    def next_time(self, time):
        now = datetime.now()
        mtime = now.replace(hour=time.hour, minute=time.minute)
        if now > mtime:
            mtime = mtime.replace(day=now.day + 1)
        print("next time:", mtime)
        return mtime

    def init_scheduler(self):
        print("init scheduler")
        self.scheduler.remove_all_jobs()
        for table_name, times in self.root_table.items():
            for time in times:
                self.sched_add(self.next_time(time), table_name=table_name)
                print("job is registered!!")
        self.scheduler.start()
        print("Schduler Start")

    # (date, msg)  (date, func)  (date, func, args)
    def sched_add(self, run_date, func=None, table_name=None, args=None):
        if table_name:
            print("sched_add: DB mode")
            self.scheduler.add_job(self.push_msg_to_user, 'date', next_run_time=run_date, args=[table_name])
        elif func:
            print("sched_add: Func mode")
            mArgs = args
            self.scheduler.add_job(func, 'date', next_run_time=run_date, args=mArgs)
        else:
            print("Err: args err")
            return

    def push_msg_to_user(self, table_name):
        msg = self.sqler.read_pick_one(table_name)
        self.sender.sendMessage(msg)

    def handle_command(self, cmd):
        pass

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        self.sender.sendMessage('on_chat_message: main')

        if content_type is 'text':
            self.handle_command(msg['text'])
            return

    def on_close(self, exception):
        pass
        # if isinstance(exception, telepot.helper.WaitTooLong):
        #     self.sender.sendMessage('Game expired. The answer is %d' % self._answer)


class ConfigParser():
    def __init__(self):
        self.token = ""
        self.validusers = []

    def readConfig(self, file):
        configDic = self.parseConfig(file)
        if not bool(configDic):
            print("Err: The Config File Not Found!")
            return False
        self.token = configDic['common']['token']
        self.validusers = configDic['common']['valid_users']

    def parseConfig(self, filename):
        f = open(filename, 'r')
        js = json.loads(f.read())
        f.close()
        return js

    def getToken(self):
        return self.token

    def getValidUsers(self):
        return self.validusers


cp = ConfigParser()
cp.readConfig("setting.json")

print("DBG: 1")
bot = telepot.DelegatorBot(cp.getToken(), [
    (per_chat_id(), create_open(Reminder, timeout=120)),
])
bot.message_loop(run_forever=True)
print("MAIN GO")
