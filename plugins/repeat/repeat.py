# -*- coding: utf-8 -*-
crontable = []
outputs = []


def process_message(data):
    from pprint import pprint
    pprint(data)
    channel = data['channel']
    msg = data['text']
    cmds = data['text'].split(" ")
    #pprint(cmds)
    user = data['user']
    if channel in ['G15LH27K4', 'C0JKD2HMM']:
        import time
        from slackclient import SlackClient

        token = "xoxp-18161314915-18164619686-24844646147-cbf51c2e1d"
        sc = SlackClient(token)
        user_info = sc.api_call("users.info", user=user)
        user_name = user_info['user']['name']
        print("msg from {}".format(user_name))
        if cmds[0] == u'!touch':
            output_msg = u"@{} 碰ㄌ一下 {} 沒想到就死去了".format(user_name, cmds[1])
            #outputs.append([data['channel'], output_msg])
            sc.api_call(
                "chat.postMessage", channel="#bot-dev-test", text=output_msg,
                    username='pybot', icon_emoji=':robot_face:'
                    )
