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
import yaml
friend_await = {}
friend_sets = []
channel_map = {"general": "C0J4UTXL0"}
database = "example.db"

config = yaml.load(open('rtmbot.conf', 'r'))
ADMIN = config.get('ADMIN')

orinpix_pokemon_candidate = [25, 35, 36, 39, 40, 113, 151, 173, 174, 175, 176]
COIN_NEED_POKEMON = 5

arena_standby = {}
SKILL_LIST = json.load(open('skill_list.json'))
SKILL_LIST = [skill.encode('utf-8') for skill in SKILL_LIST]

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
                    "catchable": int(row["catchable"]) if row["catchable"] != "" else 0,
                    #"probability_type": row["probability_type"],
                    "kill_basic_exp": int(row["kill_basic_exp"]),
                    "level_exp_type": row["level_exp_type"],
                }

pd = PokemonData()

class Pokemon(object):
    def __init__(self, race=0):
        if race == 0:
            catchable_race = [key for key in pd.race_map if pd.race_map[key]["catchable"] == 1]
            #type_b = [key for key in pd.race_map if pd.race_map[key]["catchable"] == 1 and pd.race_map[key]["probability_type"] == "B"]
            #type_c = [key for key in pd.race_map if pd.race_map[key]["catchable"] == 1 and pd.race_map[key]["probability_type"] == "C"]
            #candidates = catchable_race + type_b + type_c + type_c
            candidates = catchable_race
            self.race = random.choice(candidates)
        else:
            self.race = race
        self.level = 1
        self.exp = 0
        # individual value
        self.i_value = {
            "hp": random.randrange(0, 32),
            "atk": random.randrange(0, 32),
            "def": random.randrange(0, 32),
            "satk": random.randrange(0, 32),
            "sdef": random.randrange(0, 32),
            "spd": random.randrange(0, 32),
        }

class SummonedPokemon(object):
    def __init__(self, id):
        ''' initialize an existed pokemon from database'''
        conn = sqlite3.connect(database)
        c = conn.cursor()
        c.execute('''SELECT race, level, exp, i_hp, i_atk, i_def, i_satk, i_sdef, i_spd FROM pokemons WHERE id = {}'''.format(id))
        r = c.fetchall()[0]
        conn.close()
        self.race, self.level, self.exp = r[0:3]
        self.i_value = {
            "hp": r[3],
            "atk": r[4],
            "def": r[5],
            "satk": r[6],
            "sdef": r[7],
            "spd": r[8],
        }
        self.c_value = {
            "max_hp": self.get_cur_value('hp'),
            "hp": self.get_cur_value('hp'),
            "atk": self.get_cur_value('atk'),
            "def": self.get_cur_value('def'),
            "satk": self.get_cur_value('satk'),
            "sdef": self.get_cur_value('sdef'),
            "spd": self.get_cur_value('spd'),
        }

    def get_cur_value(self, ability):
        if ability == 'hp':
            value = (pd.race_map[self.race][ability] * 2 + self.i_value[ability]) * ( self.level / 100.0) + self.level + 10
            return int(value) + 1
        else:
            value = (pd.race_map[self.race][ability] * 2 + self.i_value[ability]) * ( self.level / 100.0) + 5
            return int(value) + 1

def get_pokemon(user, channel_id):
    slack = Slack()
    if user == 'orinpix':
        p = Pokemon(random.choice(orinpix_pokemon_candidate))
        zh_name = pd.race_map[p.race]["zh_name"]
        bot_icon = ":" + str(p.race).zfill(3) + ":"
        msg = u"@{} 使用黃金寶貝球抓到了 {}！\n".encode('utf-8').format(user, zh_name)
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
    zh_name = pd.race_map[p.race]["zh_name"]
    r_hp = pd.race_map[p.race]["hp"]
    r_atk = pd.race_map[p.race]["atk"]
    r_def = pd.race_map[p.race]["def"]
    r_spd = pd.race_map[p.race]["spd"]
    msg = u"@{} 使用寶貝球抓到了 {}！\nHP: {}(+{}), 攻: {}(+{}), 防: {}(+{}), 速: {}(+{})".encode('utf-8').format(user, zh_name, r_hp, p.i_value['hp'], r_atk, p.i_value['atk'], r_def, p.i_value['def'], r_spd, p.i_value['spd'],)

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
    for i, pokemon in enumerate(result):
        race, level, exp, i_hp, i_atk, i_def, i_satk, i_sdef, i_spd = pokemon
        msg.append(u"{}:{}:".format(i+1, str(race).zfill(3)).encode('utf-8'))
    conn.close()
    return " ".join(msg)

def pokemon_give_new(user, race):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    p = Pokemon(race)
    zh_name = pd.race_map[p.race]["zh_name"]
    r_hp = pd.race_map[p.race]["hp"]
    r_atk = pd.race_map[p.race]["atk"]
    r_def = pd.race_map[p.race]["def"]
    r_spd = pd.race_map[p.race]["spd"]
    print('get pokemon #{}'.format(p.race))
    bot_icon = ":" + str(p.race).zfill(3) + ":"
    msg = u"@{} 給你一隻 {}！\nHP: {}(+{}), 攻: {}(+{}), 防: {}(+{}), 速: {}(+{})".encode('utf-8').format(user, zh_name, r_hp, p.i_value['hp'], r_atk, p.i_value['atk'], r_def, p.i_value['def'], r_spd, p.i_value['spd'],)

    c.execute('''create table if not exists pokemons (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, race INTEGER, level INTEGER, exp INTEGER, i_hp INTEGER, i_atk INTEGER, i_def INTEGER, i_satk INTEGER, i_sdef INTEGER, i_spd INTEGER)''')
    c.execute('''INSERT INTO pokemons (user, race, level, exp, i_hp, i_atk, i_def, i_satk, i_sdef, i_spd) VALUES (\'{}\', {}, {}, {}, {}, {}, {}, {}, {}, {});'''.format(user, p.race, p.level, p.exp, p.i_value['hp'], p.i_value['atk'], p.i_value['def'], p.i_value['satk'], p.i_value['sdef'], p.i_value['spd']))
    conn.commit()
    conn.close()
    return msg

def _atk(sp1, sp2):
    skill_base = 50
    base_damage = ((2.0 * sp1.level + 10.0) / 250.0) * (sp1.c_value["atk"] * 1.0 / sp2.c_value["def"]) * skill_base + 2
    print("((2.0 * sp1.level + 10) / 250.0) = {}, (sp1.c_value[\"atk\"] * 1.0 / sp2.c_value[\"def\"]): {}".format(((2.0 * sp1.level + 10) / 250.0), (sp1.c_value["atk"] * 1.0 / sp2.c_value["def"])))
    is_critical = False
    if random.random() < 0.1: # 10% change critical
        is_critical = True
        critical_modifier = 2
    else:
        is_critical = False
        critical_modifier = 1
    modifier = critical_modifier * (random.random() / 100 * 15 + 0.85)
    final_damage = max(int(base_damage * modifier), 1)
    print("base_damage: {}, modifier: {}, final_damage: {}".format(base_damage, modifier, final_damage))
    import sys
    sys.stdout.flush()
    return (is_critical, final_damage)

def _duel(team1, team2, msg):
    pokemon1_id = team1[1]
    pokemon2_id = team2[1]
    sp1 = SummonedPokemon(pokemon1_id)
    sp2 = SummonedPokemon(pokemon2_id)
    pokemon1_name = pd.race_map[sp1.race]['zh_name']
    pokemon2_name = pd.race_map[sp2.race]['zh_name']

    while sp1.c_value["hp"] > 0 and sp2.c_value["hp"] > 0:
        (is_critical, final_damage) = _atk(sp1, sp2)
        msg += u"{} 對 {} 使出 {} 造成 {} 點{}傷害。\n{} hp: {} -> {}\n".encode('utf-8').format(pokemon1_name, pokemon2_name, random.choice(SKILL_LIST), final_damage, "暴擊" if is_critical else "", pokemon2_name, sp2.c_value["hp"], sp2.c_value["hp"] - final_damage)
        sp2.c_value["hp"] -= final_damage
        if sp2.c_value["hp"] <= 0:
            msg += u"{} 死去\n".encode('utf-8').format(pokemon2_name)
            return team1, msg

        (is_critical, final_damage) = _atk(sp2, sp1)
        msg += u"{} 對 {} 使出 {} 造成 {} 點{}傷害。\n{} hp: {} -> {}\n".encode('utf-8').format(pokemon2_name, pokemon1_name, random.choice(SKILL_LIST), final_damage, "暴擊" if is_critical else "", pokemon1_name, sp1.c_value["hp"], sp1.c_value["hp"] - final_damage)
        sp1.c_value["hp"] -= final_damage
        if sp1.c_value["hp"] <= 0:
            msg += u"{} 死去\n".encode('utf-8').format(pokemon1_name)
            return team2, msg
    #return random.choice([team1, team2])

def fight(user, target, pokemon_index):
    global arena_standby, pd
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('''SELECT id, race, level, exp, i_hp, i_atk, i_def, i_satk, i_sdef, i_spd FROM pokemons WHERE user = \"{}\"'''.format(user))
    result = c.fetchall()
    if pokemon_index > len(result):
        msg =  u"@{} 你沒有那麼多神奇寶貝！".format(user).encode('utf-8')        
    elif user == target:
        msg =  u"@{} 你不是武藤遊戲，無法跟自己決鬥。".format(user).encode('utf-8')
    else:
        picked_pokemon = result[pokemon_index -1]
        id, race, level, exp, i_hp, i_atk, i_def, i_satk, i_sdef, i_spd = picked_pokemon
        pokemon_name = pd.race_map[race]['zh_name']
        if (target, user) in arena_standby:
            msg = u"@{} 接受了 @{} 的挑戰並使用 {} 應戰！\n".format(user, target, unicode(pokemon_name, 'utf-8')).encode('utf-8')
            team1 = (target, arena_standby[(target, user)])
            team2 = (user, id)
            winnner, msg = _duel(team1, team2, msg)
            c.execute('''SELECT race FROM pokemons WHERE id = {}'''.format(winnner[1]))
            winner_pokemon_name = pd.race_map[c.fetchall()[0][0]]['zh_name']
            msg += u"勝利者是 @{} 與他的 {}！".format(winnner[0], unicode(winner_pokemon_name, 'utf-8')).encode('utf-8')
            arena_standby.pop((target, user))
        else:
            msg = u"@{} 使用 {} 跟 @{} 提出決鬥！（從 `!pokemons` 裡面選擇一個用 `!fight` 應戰）".format(user, unicode(pokemon_name, 'utf-8'), target, user).encode('utf-8')
            arena_standby[(user, target)] = id
    conn.close()
    return msg

def unary_command(cmd, channel_id, username, slack):
    bot_icon = None
    if cmd in ["!pokemon"]:
        bot_icon, msg = get_pokemon(username, channel_id)
    elif cmd in ["!pokemons"]:
        msg = pokemons(username)
    else:
        return
    slack.post_message(channel_id, msg, bot_icon)

def binary_command(cmd, target, channel_id, username, slack):
    bot_icon = None
    if cmd in ['!anything']:
        return
    else:
        return
    slack.post_message(channel_id, msg, bot_icon)

def trinary_command(cmd, target, something, channel_id, user, slack):
    bot_icon = None
    if cmd in ['!pokemon_give_new']:
        race = int(something)
        if user == ADMIN:
            msg = pokemon_give_new(target, race)
        else:
            return
    elif cmd in ['!fight']:
        try:
            pokemon_index = int(something)
            msg = fight(user, target, pokemon_index)
        except Exception, e:
            import traceback
            traceback.print_exc()
            msg = u"@{} 錯誤！{}".format(user, e).encode('utf-8')
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

    if data['text'].startswith("!"):
        msgs = data['text'].split(" ")
        if len(msgs) == 2:
            cmd = msgs[0]
            target = msgs[1]
            binary_command(cmd, target, channel_id, user, slack)
        elif len(msgs) == 3:
            cmd = msgs[0]
            target = msgs[1]
            something = msgs[2]
            trinary_command(cmd, target, something, channel_id, user, slack)
        elif len(msgs) == 1:
            cmd = msgs[0]
            unary_command(cmd, channel_id, user, slack)

    update_freq(data['text'], user)

