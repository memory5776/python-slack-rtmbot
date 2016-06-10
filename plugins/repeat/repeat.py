# -*- coding: utf-8 -*-
crontable = []
#crontable.append([60*60, "drop_item"])
outputs = []
from slack_util import Slack
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

class PokemonData(object):
    race_map = {}
    def __init__(self):
        with open('pokemon_race.csv') as csvfile:
            reader = csv.DictReader(csvfile)
            for i, row in enumerate(reader):
                self.race_map[int(row["id"])] = {
                    "zh_name": row["zh_name"],
                    "jap_name": row["jap_name"],
                    "eng_name": row["eng_name"],
                    "attr1": int(row["attr1"]),
                    "attr2": int(row["attr2"]) if row["attr2"] != '' else None,
                    "hp": int(row["hp"]),
                    "atk": int(row["atk"]),
                    "def": int(row["def"]),
                    "satk": int(row["satk"]),
                    "sdef": int(row["sdef"]),
                    "spd": int(row["spd"]),
                }

pd = PokemonData()

class Pokemon(object):
    def __init__(self):
        self.race = random.randrange(1, 252)
        self.level = 1
        self.exp = 0
        self.zh_name = pd.race_map[self.race]["zh_name"]
        self.jap_name = pd.race_map[self.race]["jap_name"]
        self.eng_name = pd.race_map[self.race]["eng_name"]
        self.attr1 = pd.race_map[self.race]["attr1"]
        self.attr2 = pd.race_map[self.race]["attr2"]
        # race value
        self.r_value = {
            "hp": pd.race_map[self.race]["hp"],
            "atk": pd.race_map[self.race]["atk"],
            "def": pd.race_map[self.race]["def"],
            "satk": pd.race_map[self.race]["satk"],
            "sdef": pd.race_map[self.race]["sdef"],
            "spd": pd.race_map[self.race]["spd"],
        }
        # individual value
        self.i_value = {
            "hp": random.randrange(0, 32),
            "atk": random.randrange(0, 32),
            "def": random.randrange(0, 32),
            "satk": random.randrange(0, 32),
            "sdef": random.randrange(0, 32),
            "spd": random.randrange(0, 32),
        }


def get_active_users(slack, channel_name):
    active_users = []
    r = slack.sc.api_call("channels.info", channel=channel_map[channel_name])
    if r["ok"] == True:
        members = r["channel"]["members"]
        for user in members:
            r2 = slack.sc.api_call("users.getPresence", user=user)
            if r2["ok"] == True:
                if r2["presence"] == "away":
                    pass
                elif r2["presence"] == "active":
                    active_users.append(user)
    return active_users

def get_pokemon(user):
    p = Pokemon()
    bot_icon = ":" + str(p.race).zfill(3) + ":"
    msg = u"@{} 使用 China Ball 抓到了 {}！\nHP: {}(+{}), 攻: {}(+{}), 防: {}(+{}), 速: {}(+{})\n但馬上就跑了。".encode('utf-8').format(user, p.zh_name, p.r_value['hp'], p.i_value['hp'], p.r_value['atk'], p.i_value['atk'], p.r_value['def'], p.i_value['def'], p.r_value['spd'], p.i_value['spd'],)
    return bot_icon, msg

def drop_item():
    slack = Slack()
    active_users = get_active_users(slack, "general")
    if len(active_users) == 0:
        return
    #lucky_user = random.choice(active_users)
    users = ["@" + slack.get_username(user) for user in active_users]
    usernames = ", ".join(users)

    slack.post_message("bot-dev-test", u"以下幸運兒獲得了 5 塊金幣！\n {}".format(usernames).encode('utf-8'))


def help():
    msg = [
        u"!touch [user]: 碰一下 [user]",
        u"!work [user]: 逼 [user] 工作",
        u"!friend [user]: 跟 [user] 交朋友",
        u"!tarot: 抽塔羅牌"
    ]
    return "\n".join(msg).encode('utf-8')

def flist():
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('''create table if not exists friends (id INTEGER PRIMARY KEY AUTOINCREMENT, user_a TEXT, user_b TEXT, UNIQUE (user_a, user_b) ON CONFLICT IGNORE)''')
    c.execute('''select user_a, user_b from friends''')
    result = c.fetchall()
    conn.close()

    msg = []
    msg.append(u"貴圈真亂".encode('utf-8'))
    for row in result:
        msg.append("{} <=> {}".format(row[0], row[1]))
    return "\n".join(msg)

def freq():
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('''SELECT * from chat_freq order by count desc''')
    result = c.fetchall()
    msg = []
    msg.append(u"話多排行榜:".encode('utf8'))
    for row in result:
        msg.append("{}: {}".format(row[0], row[1]))

    c.execute('''SELECT * from cmd_freq order by count desc''')
    result = c.fetchall()
    conn.close()
    msg.append(u"愛玩機器人排行榜".encode('utf-8'))
    for row in result:
        msg.append("{}: {}".format(row[0], row[1]))
    return "\n".join(msg)

def tarot(user):
    msg = u"@{} 想問什麼呢？(!tarot love/work/health/money/joy/daily)".format(user).encode('utf-8')
    return msg


#TODO: unify cmd_1 and cmd_2 by **kwargs
def cmd_1(cmd, channel_id, username, slack):
    bot_icon = None
    if cmd in ['!help', u'!朽咪教我', u'!朽瞇教我', u'!舒米教我']:
        msg = help()
    elif cmd in ['!flist']:
        msg = flist()
    elif cmd in ['!freq']:
        msg = freq()
    elif cmd in ["!tarot"]:
        msg = tarot(username)
    elif cmd in ["!pokemon"]:
        bot_icon, msg = get_pokemon(username)
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

def touch(user, target):
    msg = u"@{} 碰ㄌ一下 @{} 沒想到就死去了".format(user, target).encode('utf-8')
    return msg

def work(user, target):
    msg = u"@{} 在 @{} 的監督下辛勤地工作".format(target, user).encode('utf-8')
    return msg

def friend(user, target):
    global friend_await
    if user not in friend_await:
        friend_await[user] = []
    if target not in friend_await[user]:
        friend_await[user].append(target)
        msg = u"@{} 想跟 @{} 做朋友（輸入 !yfriend {} 同意）".format(user, target, user)
    else:
        msg = u"@{} 人家還沒回應你在急屁急".format(user)
    return msg

def yfriend(user, target):
    if target in friend_await:
        if user in friend_await[target]:
            conn = sqlite3.connect(database)
            c = conn.cursor()
            msg = u"@{} 接受了 @{} 的好友邀請，現在他們是好碰友".format(user, target)
            #friend_sets.append(set([user, target]))
            c.execute('''create table if not exists friends (id INTEGER PRIMARY KEY AUTOINCREMENT, user_a TEXT, user_b TEXT, UNIQUE (user_a, user_b) ON CONFLICT IGNORE)''')
            c.execute('''INSERT INTO friends (user_a, user_b) VALUES (\'{}\', \'{}\');'''.format(user, target))
            friend_await[target].remove(user)
            conn.commit()
            conn.close()
        else:
            msg = u"@{} 沒有想要跟你做朋友好ㄇ".format(target)
    else:
        msg = u"@{} 沒有想要跟你做朋友好ㄇ".format(target)
    return msg

def cmd_2(cmd, target, channel_id, username, slack):
    bot_icon = None
    if cmd == u'!touch':
        msg = touch(username, target)
    elif cmd in ["!work", u"!工作"]:
        msg = work(username, target)
    elif cmd in ["!friend"]:
        msg = friend(username, target)
    elif cmd in ["!yfriend"]:
        msg = yfriend(username, target)
    elif cmd in ["!tarot"]:
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
    #c.execute('''SELECT * from {}'''.format(freq_table))
    #result = c.fetchall()
    #pprint(result)
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
    #pprint(data)
    slack = Slack()
    channel_id = data['channel']
    channelname = slack.get_channelname(channel_id)
    user_id = get_user_id(data)
    if not user_id:
        return
    user = slack.get_username(user_id)
    print("msg: {} from user: {}, channel: {} ({})".format(data['text'].encode('utf8'), user, channelname, channel_id))

    msgs = data['text'].split(" ")

    if len(msgs) == 2:
        cmd = msgs[0]
        target = msgs[1]
        cmd_2(cmd, target, channel_id, user, slack)
    else:
        cmd = msgs[0]
        cmd_1(cmd, channel_id, user, slack)

    update_freq(data['text'], user)

