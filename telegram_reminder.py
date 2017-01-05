import json
import random
import sqlite3
import telepot
from telepot.delegate import per_chat_id, create_open
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, time

class Sqler():
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
    root_table = {"myString": [time(7, 45), time(12, 00), time(15,00), time(20, 00)]}
    MENU_START = '알림 시작'
    MENU_STATUS = '알림 상태'
    HOME = '홈으로'
    global scheduler

    def __init__(self, seed_tuple, timeout):
        super(Reminder, self).__init__(seed_tuple, timeout)

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
        self.sender.sendMessage("등록 완료")

    def sched_print(self):
        if not scheduler.get_jobs():
            return '등록된 알림이 없습니다.'
        result = "알림 항목:\n"
        for i, s in enumerate(scheduler.get_jobs()):
            result += '{0}. 저장소 이름: {1}\n설정 시간:\n{2}\n\n'.format(i + 1, s.name,
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
        sentence = self.sqler.read_pick_one(table_name)
        now = datetime.now()
        min = ""
        if now.minute == 0:
            min = str(now.minute) + "분: "
        msg = str(now.hour)+"시 " + min + sentence
        self.sender.sendMessage(msg)

    def do_HOME(self):
        self.sender.sendMessage('네. Remindbot입니다. 설정된 시간에 메세지를 전달합니다.')
        show_keyboard = {'keyboard': [[self.MENU_START], [self.MENU_STATUS], [self.HOME]]}
        self.sender.sendMessage('메뉴를 선택해주세요.', reply_markup=show_keyboard)

    def do_MENU_START(self):
        self.sqler = Sqler("myDB.db", "CREATE TABLE myString(id int, sentence text)")
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
valid_user = cp.getValidUsers()
scheduler = BackgroundScheduler()
scheduler.start()

bot = telepot.DelegatorBot(cp.getToken(), [
    (per_chat_id(), create_open(Reminder, timeout=120)),
])
bot.message_loop(run_forever=True)