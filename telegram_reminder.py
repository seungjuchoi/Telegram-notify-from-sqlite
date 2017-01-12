#!/usr/bin/python3
import json
import telepot
import pymongo
from telepot.delegate import per_chat_id, create_open, pave_event_space
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import time


class DB_Manager():

    def __init__(self, db, collection, cb_handler):  # creation
        self.db = pymongo.MongoClient()[db]
        self.col = self.db['M'+str(collection)]
        self.handler = cb_handler

    def pick_random(self, layer='rock'):
        text = list(self.col.aggregate([{'$match': {'layer': layer}}, {'$sample': {'size': 1}}]))[0]['Contents']
        self.handler(text)

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
        self.db = DB_Manager("sentences", chat_id, cb_handler)
        self.t_handler = cb_handler
        if layer_times:
            self.sched_update(layer_times)
        else:
            self.sched_update({"rock": cp['default_time']})

    def sched_update(self, layer_times):
        self.time_table.update(layer_times)
        for layer, times in self.time_table.items():
            for time in times:
                self.task_add(self.chat_id, time, layer=layer)

    def task_all_print(self):
        if not mainSchedule.get_jobs():
            return 'There is no Notifications'
        result = "Notification Table:\n"
        for i, s in enumerate(mainSchedule.get_jobs()):
            result += '{0}. Repositary name: {1}\nSetting time:\n{2}\n\n'.format(i + 1, s.name,
                                                                                 ":".join(str(s.next_run_time).split(":")[:2]))
        return result

    def task_add(self, chat_id, run_at, layer, args=None, pick_mode="RANDOM"):
        if pick_mode == "RANDOM":
            mainSchedule.add_job(self.db.pick_random, 'cron', hour=run_at.hour, minute=run_at.minute)
        elif pick_mode == "LOW_WEIGHT":
            mainSchedule.add_job(self.db.pick_weight, 'cron', hour=run_at.hour, minute=run_at.minute, args=[layer, chat_id],
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
        self.sender.sendMessage("Yes, I'm Re-Reminder.")
        show_keyboard = {'keyboard': [
            [self.MENU_START], [self.MENU_STATUS], [self.HOME]]}
        self.sender.sendMessage('Choose a option.', reply_markup=show_keyboard)

    def do_MENU_START(self):
        self.mScheduller = Sentance_Scheduler(self.chatID, self.sched_cb_handler)
        self.sender.sendMessage("The registration has completed")

    def do_MENU_STATUS(self):
        self.sender.sendMessage(self.mScheduller.task_all_print())

    def handle_text(self, cmd):
        if cmd == self.MENU_START:
            self.do_MENU_START()
        if cmd == self.HOME:
            self.do_HOME()
        if cmd == self.MENU_STATUS:
            self.do_MENU_STATUS()

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        self.chatID = chat_id

        # Check ID
        if not chat_id in cp['valid_chat_id']:
            self.sender.sendMessage("Permission Denied")
            return

        if content_type is 'text':
            self.handle_text(msg['text'])
            return

    def sched_cb_handler(self, t):
        #TODO: handle a rich parameter
        self.sender.sendMessage(t)

    def on_close(self, exception):
        pass


class ConfigParser():

    def load(self, file):
        f = open(file, 'r')
        configDic = json.loads(f.read())
        f.close()
        if not bool(configDic):
            return False
        outDic={}
        outDic['token'] = configDic['common']['token']
        outDic['valid_chat_id'] = configDic['common']['valid_chat_id']
        outDic['default_time'] = self.getDefaultTime(configDic)
        outDic['default_time_zone'] = configDic['common']['default_time_zone']
        return outDic

    def getDefaultTime(self, configDic):
        self.default_times = []
        for t in configDic['common']['default_time']:
            hour = int(t.split(":")[0])
            minute = int(t.split(":")[1])
            self.default_times.append(time(hour, minute))
        return list(set(self.default_times))

# Parse a config
cp = ConfigParser().load("setting.json")
if not cp:
    print("Err: The Config File Not Found!")
valid_users = cp['valid_chat_id']

# Start scheduler
mainSchedule = BackgroundScheduler(timezone=cp['default_time_zone'])
mainSchedule.start()

bot = telepot.DelegatorBot(cp['token'], [
    pave_event_space()(
        per_chat_id(), create_open, Reminder, timeout=120),
])
bot.message_loop(run_forever='Listening ...')
