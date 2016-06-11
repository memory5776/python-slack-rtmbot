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
channel_map = {"general": "C0J4UTXL0"}
database = "example.db"

orinpix_pokemon_candidate = [25, 35, 36, 39, 40, 113, 151, 173, 174, 175, 176]
COIN_NEED_POKEMON = 5

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
    def __init__(self, race=0):
        if race == 0:
            self.race = random.randrange(1, 252)
        else:
            self.race = race
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

        self.cur_value = {
            "hp": self.update_status('hp'), # max hp
            "atk": self.update_status('atk'),
            "def": self.update_status('def'),
            "satk": self.update_status('satk'),
            "sdef": self.update_status('sdef'),
            "spd": self.update_status('spd'),
        }
        self.cur_hp = self.cur_value['hp']

    def update_status(self, ability):
        if ability == 'hp':
            return (self.i_value[ability] * 2 + self.i_value[ability]) * ( self.level / 100.0) + self.level + 10
        else:
            return (self.i_value[ability] * 2 + self.i_value[ability]) * ( self.level / 100.0) + 5

def get_pokemon(user, channel_id):
    slack = Slack()
    if user == 'orinpix':
        p = Pokemon(random.choice(orinpix_pokemon_candidate))
        bot_icon = ":" + str(p.race).zfill(3) + ":"
        msg = u"@{} 使用黃金寶貝球抓到了 {}！\n".encode('utf-8').format(user, p.zh_name)
        return bot_icon, msg

    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('''SELECT coins FROM coins WHERE user = \'{}\';'''.format(user))
    result = c.fetchall()
    if result[0][0] < COIN_NEED_POKEMON:
        return ":rabbit:", u"@{} 沒錢能轉蛋了！".format(user).encode('utf-8')

    print('deduce money by 5')
    c.execute('''UPDATE coins SET coins = coins - {} WHERE user = \'{}\';'''.format(COIN_NEED_POKEMON, user))
    # gacha!
    p = Pokemon()
    print('get pokemon #{}'.format(p.race))
    bot_icon = ":" + str(p.race).zfill(3) + ":"
    msg = u"@{} 使用寶貝球抓到了 {}！\nHP: {}(+{}), 攻: {}(+{}), 防: {}(+{}), 速: {}(+{})".encode('utf-8').format(user, p.zh_name, p.r_value['hp'], p.i_value['hp'], p.r_value['atk'], p.i_value['atk'], p.r_value['def'], p.i_value['def'], p.r_value['spd'], p.i_value['spd'],)

    print('start writing DB')
    # write DB
    c.execute('''create table if not exists pokemons (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, race INTEGER, level INTEGER, exp INTEGER, i_hp INTEGER, i_atk INTEGER, i_def INTEGER, i_satk INTEGER, i_sdef INTEGER, i_spd INTEGER)''')
    c.execute('''INSERT INTO pokemons (user, race, level, exp, i_hp, i_atk, i_def, i_satk, i_sdef, i_spd) VALUES (\'{}\', {}, {}, {}, {}, {}, {}, {}, {}, {});'''.format(user, p.race, p.level, p.exp, p.i_value['hp'], p.i_value['atk'], p.i_value['def'], p.i_value['satk'], p.i_value['sdef'], p.i_value['spd']))
    conn.commit()
    conn.close()
    print('write DB done')
    return bot_icon, msg

def pokemons(user):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('''SELECT race, level, exp, i_hp, i_atk, i_def, i_satk, i_sdef, i_spd FROM pokemons WHERE user = \"{}\"'''.format(user))
    result = c.fetchall()
    msg = []
    for pokemon in result:
        race, level, exp, i_hp, i_atk, i_def, i_satk, i_sdef, i_spd = pokemon
        msg.append(u":{}:".format(str(race).zfill(3)).encode('utf-8'))
    conn.close()
    return " ".join(msg)

#TODO: unify cmd_1 and cmd_2 by **kwargs
def cmd_1(cmd, channel_id, username, slack):
    bot_icon = None
    if cmd in ["!pokemon"]:
        bot_icon, msg = get_pokemon(username, channel_id)
    elif cmd in ["!pokemons"]:
        msg = pokemons(username)
    else:
        return
    slack.post_message(channel_id, msg, bot_icon)

def cmd_2(cmd, target, channel_id, username, slack):
    bot_icon = None
    if cmd in ['!anything']:
        return
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

    msgs = data['text'].split(" ")

    if len(msgs) == 2:
        cmd = msgs[0]
        target = msgs[1]
        cmd_2(cmd, target, channel_id, user, slack)
    else:
        cmd = msgs[0]
        cmd_1(cmd, channel_id, user, slack)

    update_freq(data['text'], user)

