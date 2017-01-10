#!/usr/bin/python3
import json
import telepot
import pymongo
from telepot.delegate import per_chat_id, create_open, pave_event_space
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import time


class DB_Manager():

    def __init__(self, db, collection):  # creation
        self.db = pymongo.MongoClient()[db]
        self.col = db['m'+str(collection)]

    def pick_random(self, layer):
        return self.col.aggregate([{'$match': {'layer': layer}}, {'$sample': {'size': 1}}])['Contents']

    def pick_weight(self, layer, weight_index="weight"):
        print("TODO: WEIGHT PICK!")
        pass

    def delete_string(self):
        pass

    def edit_string(self):
        pass


class Sentance_Scheduler():

    def __init__(self, chat_id, cb_handler, layer_times=None):
        self.time_table = {}
        self.chat_id = chat_id
        self.db = DB_Manager("sentences", chat_id)
        self.t_handler = cb_handler
        if layer_times:
            self.sched_update(layer_times)
        else:
            self.sched_update({"rock": cp.getDefaultTime()})

    def sched_update(self, layer_times):
        self.time_table.update(layer_times)
        for layer, times in self.time_table.items():
            for time in times:
                self.task_add(self.chat_id, time, layer=layer)

    def task_all_print(self):
        if not mainSchdule.get_jobs():
            return 'There is no Notifications'
        result = "Notification Table:\n"
        for i, s in enumerate(mainSchdule.get_jobs()):
            result += '{0}. Repositary name: {1}\nSetting time:\n{2}\n\n'.format(i + 1, s.name,
                                                                                 ":".join(str(s.next_run_time).split(":")[:2]))
        return result

    def task_add(self, chat_id, run_at, layer, args=None, pick_mode="RANDOM"):
        if pick_mode == "RANDOM":
            mainSchdule.add_job(self.db.pick_random(layer), 'cron', hour=run_at.hour, minute=run_at.minute)
        elif pick_mode == "LOW_WEIGHT":
            mainSchdule.add_job(self.db.pick_weight(layer), 'cron', hour=run_at.hour, minute=run_at.minute, args=[layer, chat_id],
                                name=layer)
        else:
            print("Err: args err")
            return

    def task_modify(self):
        pass



class Reminder(telepot.helper.ChatHandler):
    MENU_START = 'Start Notification'
    MENU_STATUS = 'Notification Status'
    HOME = 'HOME'

    def __init__(self, *args, **kwargs):
        super(Reminder, self).__init__(*args, **kwargs)

    def open(self, initial_msg, seed):
        self.do_HOME()
        return True  # prevent on_message() from being called on the initial message

    def do_HOME(self):
        self.sender.sendMessage("Yes, I'm Red-Reminder.")
        show_keyboard = {'keyboard': [
            [self.MENU_START], [self.MENU_STATUS], [self.HOME]]}
        self.sender.sendMessage('Choose a option.', reply_markup=show_keyboard)

    def do_MENU_START(self):
        self.mScheduller = Sentance_Scheduler(self.chat_id, self.sched_cb_handler)
        self.sender.sendMessage("The registration has completed")

    def do_MENU_STATUS(self):
        self.sender.sendMessage(self.sched_print())

    def handle_text(self, cmd):
        if cmd == self.MENU_START:
            self.do_MENU_START()
        if cmd == self.HOME:
            self.do_HOME()
        if cmd == self.MENU_STATUS:
            self.do_MENU_STATUS()

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        self.chat_id = chat_id

        # Check ID
        if not chat_id in valid_users:
            self.sender.sendMessage("Permission Denied")
            return

        if content_type is 'text':
            self.handle_text(msg['text'])
            return

    def sched_cb_handler(self, **kwargs):
        for k, v in kwargs:
            if k == 'text':
                self.sender.sendMessage(v)
        pass

    def on_close(self, exception):
        pass


class ConfigParser():

    def __init__(self):
        self.token = ""
        self.valid_chat_id = []
        self.default_time = []

    def readConfig(self, file):
        configDic = self.parseConfig(file)
        if not bool(configDic):
            print("Err: The Config File Not Found!")
            return False
        self.token = configDic['common']['token']
        self.valid_chat_id = configDic['common']['valid_users']
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
        return self.valid_chat_id

    def getDefaultTime(self):
        return self.default_time


# Parse a config
cp = ConfigParser()
cp.readConfig("setting.json")
valid_users = cp.getValidUsers()

# Start scheduler
mainSchdule = BackgroundScheduler()
mainSchdule.start()

bot = telepot.DelegatorBot(cp.getToken(), [
    pave_event_space()(
        per_chat_id(), create_open, Reminder, timeout=120),
])
bot.message_loop(run_forever='Listening ...')
