#!/usr/bin/python3
import json
import random
import sqlite3
import telepot
import pymongo
from telepot.delegate import per_chat_id, create_open, pave_event_space
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, time


class DB_Manager():

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

    def cherry_pick_string(self, table_name):
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

    def delete_string(self):
        pass

    def edit_string(self):
        pass

    def add_user(self):
        '''
        userid / main time period /
        '''
        pass


class Reminder(telepot.helper.ChatHandler):  # Never Die
    root_table = {"myString": cp.getDefaultTime()}
    MENU_START = 'Start Notification'
    MENU_STATUS = 'Notification Status'
    HOME = 'HOME'
    global scheduler

    def __init__(self, *args, **kwargs):
        super(Reminder, self).__init__(*args, **kwargs)

    def open(self, initial_msg, seed):
        self.do_HOME()
        return True  # prevent on_message() from being called on the initial message

    def next_time(self, time):
        now = datetime.now()
        mtime = now.replace(hour=time.hour, minute=time.minute)
        if now > mtime:
            mtime = mtime.replace(day=now.day + 1)
        return mtime

    def init_scheduler(self):
        scheduler.remove_all_jobs()
        for table_name, times in self.root_table.items():
            for time in times:
                self.sched_add(time, table_name=table_name)
        self.sender.sendMessage("The registration has completed")

    def sched_print(self):
        if not scheduler.get_jobs():
            return 'There is no Notifications'
        result = "Notification Table:\n"
        for i, s in enumerate(scheduler.get_jobs()):
            result += '{0}. Repositary name: {1}\nSetting time:\n{2}\n\n'.format(i + 1, s.name,
                                                                                 ":".join(str(s.next_run_time).split(":")[:2]))
        return result

    # (date, msg)  (date, func)  (date, func, args)
    def sched_add(self, run_at, func=None, table_name=None, args=None):
        if table_name:
            print("sched_add: DB mode")
            scheduler.add_job(self.push_msg_to_user_from_table, 'cron', hour=run_at.hour, minute=run_at.minute, args=[table_name],
                              name=table_name)
        elif func:
            print("sched_add: Func mode")
            mArgs = args
            scheduler.add_job(func, 'date', next_run_time=run_at, args=mArgs)
        else:
            print("Err: args err")
            return

    def push_msg_to_user_from_table(self, table_name):
        sentence = self.sqler.cherry_pick_string(table_name)
        self.sender.sendMessage(sentence)

    def do_HOME(self):
        self.sender.sendMessage("Yes, I'm Red-Reminder.")
        show_keyboard = {'keyboard': [
            [self.MENU_START], [self.MENU_STATUS], [self.HOME]]}
        self.sender.sendMessage('Choose a option.', reply_markup=show_keyboard)

    def do_MENU_START(self):
        self.sqler = DB_Manager(
            "myDB.db", "CREATE TABLE myString(id int, sentence text)")
        self.init_scheduler()

    def do_MENU_STATUS(self):
        self.sender.sendMessage(self.sched_print())

    def handle_command(self, cmd):
        if cmd == self.MENU_START:
            self.do_MENU_START()
        if cmd == self.HOME:
            self.do_HOME()
        if cmd == self.MENU_STATUS:
            self.do_MENU_STATUS()

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)

        # Check ID
        if not chat_id in valid_user:
            self.sender.sendMessage("Permission Denied")
            return

        if content_type is 'text':
            self.handle_command(msg['text'])
            return

    def on_close(self, exception):
        pass


class ConfigParser():

    def __init__(self):
        self.token = ""
        self.validusers = []
        self.default_time = []

    def readConfig(self, file):
        configDic = self.parseConfig(file)
        if not bool(configDic):
            print("Err: The Config File Not Found!")
            return False
        self.token = configDic['common']['token']
        self.validusers = configDic['common']['valid_users']
        for t in configDic['common']['default_time']:
            hour = int(t.split(":")[0])
            minute = int(t.split(":")[1])
            self.default_time.append(time(hour, minute))
        self.default_time = list(set(self.default_time))

    def parseConfig(self, filename):
        f = open(filename, 'r')
        js = json.loads(f.read())
        f.close()
        return js

    def getToken(self):
        return self.token

    def getValidUsers(self):
        return self.validusers

    def getDefaultTime(self):
        return self.default_time

cp = ConfigParser()
cp.readConfig("setting.json")
valid_user = cp.getValidUsers()
scheduler = BackgroundScheduler()
scheduler.start()

bot = telepot.DelegatorBot(cp.getToken(), [
    pave_event_space()(
        per_chat_id(), create_open, Reminder, timeout=120),
])
bot.message_loop(run_forever='Listening ...')
