#!/usr/bin/python3
import json
import telepot
import logging
from telepot.delegate import per_chat_id, create_open, pave_event_space
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import time
import databases

class Sentance_Scheduler():

    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.db = databases.SQL3_Manager("DB{}.db".format(chat_id))
        global jobStore
        global config

    def sched_init(self, layer_times = None):
        if not layer_times:
            layer_times = {"rock": config['default_time']}
        #reset jobStore
        if self.chat_id in jobStore.keys():
            for job in jobStore[self.chat_id]:
                logger.info("sched_update: remove job : {}".format(job))
                job.remove()
            jobStore.pop(self.chat_id)

        for layer, times in layer_times.items():
            for time in times:
                self.add_task(self.chat_id, time, layer=layer)

    def print_all_tasks(self):
        logger.info("keys: {}".format(jobStore.keys()))
        if not self.chat_id in jobStore.keys():
            return 'There is no Notifications'

        result = "Notification Table:\n"

        jobs = jobStore[self.chat_id]

        logger.info("jobs: {}".format(jobs))
        if bool(jobs):
            for i, s in enumerate(jobs):
                result += '{0}.\n{1}\n{2}\n\n'.format(i + 1, s.name,
                                                                                 ":".join(str(s.next_run_time).split(":")[:2]))
        else:
            result += "empty\n"
        return result

    def add_task(self, chat_id, run_at, layer, pick_mode="RANDOM"):
        if not chat_id in jobStore.keys():
            jobStore[chat_id] = []
        if pick_mode == "RANDOM":
            job = mainSchedule.add_job(self.db.pick_randomly, 'cron', hour=run_at.hour, minute=run_at.minute, args=["rock"])
        elif pick_mode == "LOW_WEIGHT":
            job = mainSchedule.add_job(self.db.pick_weight, 'cron', hour=run_at.hour, minute=run_at.minute, args=[layer, chat_id])
        else:
            logger.error("Err: args err")
            return
        jobStore[chat_id].append(job)

    def modify_task(self):
        pass

    def remove_task(self):
        pass


class Reminder(telepot.helper.ChatHandler):
    MENU_START = 'Start Reminder'
    MENU_STATUS = 'Notification List'
    MENU_RESET = 'RESET'
    HOME = 'HOME'

    def __init__(self, *args, **kwargs):
        super(Reminder, self).__init__(*args, **kwargs)
        logger.info("Start Reminder")
        self.mScheduler = None
        global schedStore

    def open(self, initial_msg, seed):
        logger.info("Open()")
        self.do_HOME()
        return True  # prevent on_message() from being called on the initial message

    def do_HOME(self):
        self.sender.sendMessage("Yes, I'm Re-Reminder.")
        show_keyboard = {'keyboard': [
            [self.MENU_START], [self.MENU_STATUS], [self.MENU_RESET], [self.HOME]]}
        self.sender.sendMessage('Choose a option.', reply_markup=show_keyboard)

    def do_MENU_START(self):
        if self.chat_id in schedStore.keys():
            self.mScheduler = schedStore[self.chat_id]
            self.sender.sendMessage("Data Restoring has completed")
        else:
            self.mScheduler = Sentance_Scheduler(self.chatID)
            schedStore[self.chat_id] = self.mScheduler
            self.mScheduler.sched_init()
            self.sender.sendMessage("The New registration has completed")


    def do_MENU_STATUS(self):
        if not self.mScheduler:
            self.do_MENU_START()
            self.sender.sendMessage(self.mScheduler.print_all_tasks())
        else:
            self.sender.sendMessage(self.mScheduler.print_all_tasks())

    def do_MENU_RESET(self):
        logger.info("do_MENU_RESET()")
        if not self.mScheduler:
            self.sender.sendMessage("Nothing to do")
        else:
            self.mScheduler = None
            if self.chat_id in schedStore.keys():
                del schedStore[self.chat_id]
            self.sender.sendMessage("Your Info has Removed")

    def handle_text(self, cmd):
        if cmd == self.MENU_START:
            self.do_MENU_START()
        elif cmd == self.HOME:
            self.do_HOME()
        elif cmd == self.MENU_STATUS:
            self.do_MENU_STATUS()
        elif cmd == self.MENU_RESET:
            self.do_MENU_RESET()

    def on_chat_message(self, msg):
        logger.info("on_chat_message()")
        content_type, chat_type, chat_id = telepot.glance(msg)
        self.chatID = chat_id

        # Check ID
        if not chat_id in config['valid_chat_id']:
            self.sender.sendMessage("Permission Denied")
            return

        if content_type is 'text':
            self.handle_text(msg['text'])
            return

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

# logging
logger = logging.getLogger('reminder')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(ch)
ch = logging.FileHandler(filename="debug.log")
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(ch)

# Parse a config
config = ConfigParser().load("setting.json")
if not config:
    logging.error("Err: Nothing to be parsed")
valid_users = config['valid_chat_id']

# Start scheduler
mainSchedule = BackgroundScheduler(timezone=config['default_time_zone'])
mainSchedule.start()

# Job store for scheduler
jobStore = dict()
schedStore = dict()

bot = telepot.DelegatorBot(config['token'], [
    pave_event_space()(
        per_chat_id(), create_open, Reminder, timeout=10),
])
bot.message_loop(run_forever='Listening ...')
