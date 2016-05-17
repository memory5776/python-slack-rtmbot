# -*- coding: utf-8 -*-
crontable = []
outputs = []
from slack_util import get_username_from_id, get_channelname_from_id, get_client
import sqlite3
from pprint import pprint
friend_await = {}
friend_sets = []

def cmd_1(cmd, channel_id, username, sc):
    conn = sqlite3.connect('example.db')
    c = conn.cursor()
    if channel_id in ['C0JKD2HMM', 'bot-dev-test', 'C0J4UTXL0']:
        if cmd in [u'!朽咪教我', u'!朽瞇教我', u'!舒米教我']:
            output_msg = u"!touch [user]: 碰一下 [user]\n!work [user]: 逼 [user] 工作\n!friend [user]: 跟 [user] 交朋友\n"
            sc.api_call( "chat.postMessage", channel="#bot-dev-test", text=output_msg, username='pybot', icon_emoji=':rabbit:')
        elif cmd in ['!flist']:
            c.execute('''create table if not exists friends (id INTEGER PRIMARY KEY AUTOINCREMENT, user_a TEXT, user_b TEXT, UNIQUE (user_a, user_b) ON CONFLICT IGNORE)''')
            c.execute('''select user_a, user_b from friends''')
            result = c.fetchall()
            output_msg = u"貴圈真亂\n"
            for row in result:
                output_msg = output_msg + u"{} <=> {}\n".format(row[0], row[1])
            sc.api_call( "chat.postMessage", channel="#bot-dev-test", text=output_msg, username='pybot', icon_emoji=':rabbit:')
        elif cmd in ['!freq']:
            c.execute('''SELECT * from chat_freq''')
            result = c.fetchall()
            output_msg = u"廢話次數統計\n"
            for row in result:
                output_msg = output_msg + u"{}: {}\n".format(row[0], row[1])
            sc.api_call( "chat.postMessage", channel="#bot-dev-test", text=output_msg, username='pybot', icon_emoji=':rabbit:')

            c.execute('''SELECT * from cmd_freq''')
            result = c.fetchall()
            output_msg = u"呼叫機器人次數統計\n"
            for row in result:
                output_msg = output_msg + u"{}: {}\n".format(row[0], row[1])
            sc.api_call( "chat.postMessage", channel="#bot-dev-test", text=output_msg, username='pybot', icon_emoji=':rabbit:')
    conn.close()

def cmd_2(cmd, target, channel_id, username, sc):
    #outputs.append([data['channel'], output_msg])
    conn = sqlite3.connect('example.db')
    c = conn.cursor()
    if channel_id in ['C0JKD2HMM', 'bot-dev-test', 'C0J4UTXL0']:
        if cmd == u'!touch':
            output_msg = u"@{} 碰ㄌ一下 @{} 沒想到就死去了".format(username, target)
            sc.api_call( "chat.postMessage", channel="#bot-dev-test", text=output_msg, username='pybot', icon_emoji=':rabbit:')
        elif cmd in ["!work", u"!工作"]:
            output_msg = u"@{} 在 @{} 的監督下辛勤地工作".format(target, username)
            sc.api_call( "chat.postMessage", channel="#bot-dev-test", text=output_msg, username='pybot', icon_emoji=':rabbit:')
        elif cmd in ["!friend"]:
            if username not in friend_await:
                friend_await[username] = []
            if target not in friend_await[username]:
                friend_await[username].append(target)
                output_msg = u"@{} 想跟 @{} 做朋友（輸入 !yfriend {} 同意）".format(username, target, username)
                sc.api_call( "chat.postMessage", channel="#bot-dev-test", text=output_msg, username='pybot', icon_emoji=':rabbit:')
            else:
                output_msg = u"@{} 人家還沒回應你在急屁急".format(username)
                sc.api_call( "chat.postMessage", channel="#bot-dev-test", text=output_msg, username='pybot', icon_emoji=':rabbit:')
        elif cmd in ["!yfriend"]:
            if target in friend_await:
                if username in friend_await[target]:
                    output_msg = u"@{} 接受了 @{} 的好友邀請，現在他們是好碰友".format(username, target)
                    sc.api_call( "chat.postMessage", channel="#bot-dev-test", text=output_msg, username='pybot', icon_emoji=':rabbit:')
                    #friend_sets.append(set([username, target]))
                    c.execute('''create table if not exists friends (id INTEGER PRIMARY KEY AUTOINCREMENT, user_a TEXT, user_b TEXT, UNIQUE (user_a, user_b) ON CONFLICT IGNORE)''')
                    c.execute('''INSERT INTO friends (user_a, user_b) VALUES (\'{}\', \'{}\');'''.format(username, target))
                    friend_await[target].remove(username)
                else:
                    output_msg = u"@{} 沒有想要跟你做朋友好ㄇ".format(target)
                    sc.api_call( "chat.postMessage", channel="#bot-dev-test", text=output_msg, username='pybot', icon_emoji=':rabbit:')
            else:
                output_msg = u"@{} 沒有想要跟你做朋友好ㄇ".format(target)
                sc.api_call( "chat.postMessage", channel="#bot-dev-test", text=output_msg, username='pybot', icon_emoji=':rabbit:')
    conn.commit()
    conn.close()

def process_message(data):
    #pprint(data)
    channel_id = data['channel']
    channelname = get_channelname_from_id(channel_id)
    if data.get('username', '') == 'pybot':
        return
    elif 'user' in data:
        user_id = data['user']
    else:
        return
    username = get_username_from_id(user_id)
    print("msg: {} from user: {}, channel: {} ({})".format(data['text'].encode('utf8'), username, channelname, channel_id))

    conn = sqlite3.connect('example.db')
    c = conn.cursor()
    if data['text'].startswith('!'):
        freq_table = 'cmd_freq'
    else:
        freq_table = 'chat_freq'
    c.execute('''create table if not exists {} (user TEXT PRIMARY KEY, count INT)'''.format(freq_table))
    c.execute('''INSERT OR REPLACE INTO {} (user, count)
                 VALUES ( \'{}\',
                     COALESCE((SELECT count FROM {} WHERE user = \'{}\'), 0)
                 );'''.format(freq_table, username, freq_table, username))
    c.execute('''UPDATE {} SET count = count + 1 WHERE user = \'{}\';'''.format(freq_table, username))
    c.execute('''SELECT * from {}'''.format(freq_table))
    #result = c.fetchall()
    #pprint(result)
    conn.commit()
    conn.close()
    msgs = data['text'].split(" ")
    sc = get_client()
    if len(msgs) == 2:
        cmd = msgs[0]
        target = msgs[1]
        cmd_2(cmd, target, channel_id, username, sc)
    else:
        cmd = msgs[0]
        cmd_1(cmd, channel_id, username, sc)

