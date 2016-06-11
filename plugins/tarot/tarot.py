# -*- coding: utf-8 -*-
crontable = []
outputs = []
from slack_util import Slack
#from plugins.general.general import update_freq
import sqlite3
from pprint import pprint
import json
import random
import csv
friend_await = {}
friend_sets = []
tarot_cards = json.load(open('tarot.json'))
channel_map = {"general": "C0J4UTXL0"}
database = "example.db"

def tarot(user):
    msg = u"@{} 想問什麼呢？(!tarot love/work/health/money/joy/daily)".format(user).encode('utf-8')
    return msg

def cmd_1(cmd, channel_id, username, slack):
    bot_icon = None
    if cmd in ["!tarot"]:
        msg = tarot(username)
    else:
        return
    slack.post_message(channel_id, msg, bot_icon)

def tarot2(user, target):
    card = random.choice(tarot_cards)
    msg = "{}/{}\n".format(card["nameCN"].encode('utf-8'), card["nameEN"])
    msg += "image: {}\n".format(card["url"])
    msg += u"@{} 的".format(user).encode('utf-8')
    if target in ["love","愛情"]:
        msg += "愛情：{}\n".format(card["love"].encode('utf-8'))
    elif target in ["work","工作"]:
        msg += "工作：{}\n".format(card["work"].encode('utf-8'))
    elif target in ["health","健康"]:
        msg += "健康：{}\n".format(card["health"].encode('utf-8'))
    elif target in ["joy","娛樂"]:
        msg += "娛樂：{}\n".format(card["joy"].encode('utf-8'))
    elif target in ["money","財富"]:
        msg += "財富：{}\n".format(card["money"].encode('utf-8'))
    elif target in ["daily","今日"]:
        msg += "今日運勢：{}\n".format(card["daily"].encode('utf-8'))
    else:
        msg += "謎樣？：{}\n".format(card["conclusion"].encode('utf-8'))
    return msg


def cmd_2(cmd, target, channel_id, username, slack):
    bot_icon = None
    if cmd in ["!tarot"]:
        msg = tarot2(username, target)
    else:
        return
    slack.post_message(channel_id, msg, bot_icon)

def update_freq(text, user):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    if text.startswith('!'):
        freq_table = 'cmd_freq'
    else:
        freq_table = 'chat_freq'
    c.execute('''create table if not exists {} (user TEXT PRIMARY KEY, count INT)'''.format(freq_table))
    c.execute('''INSERT OR REPLACE INTO {} (user, count)
                 VALUES ( \'{}\',
                     COALESCE((SELECT count FROM {} WHERE user = \'{}\'), 0)
                 );'''.format(freq_table, user, freq_table, user))
    c.execute('''UPDATE {} SET count = count + 1 WHERE user = \'{}\';'''.format(freq_table, user))
    conn.commit()
    conn.close()

def get_user_id(data):
    if data.get('username', '') == 'schubot':
        return None
    elif 'user' in data:
        return data['user']
    else:
        return None

def process_message(data):
    slack = Slack()
    channel_id = data['channel']
    channelname = slack.get_channelname(channel_id)
    user_id = get_user_id(data)
    if not user_id:
        return
    user = slack.get_username(user_id)

    msgs = data['text'].split(" ")

    if len(msgs) == 2:
        cmd = msgs[0]
        target = msgs[1]
        cmd_2(cmd, target, channel_id, user, slack)
    else:
        cmd = msgs[0]
        cmd_1(cmd, channel_id, user, slack)

    update_freq(data['text'], user)

