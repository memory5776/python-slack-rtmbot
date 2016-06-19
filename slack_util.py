#!/usr/bin/env python
from slackclient import SlackClient
import yaml

class Slack(object):
    def __init__(self, token):
        self.sc = SlackClient(token)
        self.user_info = {}
        self._build_user_info()

        self.channel_info = {}
        self._build_channel_info()

    def _build_channel_info(self):
        r = self.sc.api_call("channels.list")
        for channel in r["channels"]:
            self.channel_info[channel["name"]] = channel["id"]
        r = self.sc.api_call("groups.list")
        for channel in r["groups"]:
            self.channel_info[channel["name"]] = channel["id"]
        return 

    def _build_user_info(self):
        r = self.sc.api_call("users.list")
        if r['ok'] == False:
            print("cannot get user list")
        else:
            for user in r['members']:
                self.user_info[user['name']] = user['id']

    def post_message(self, channel, text, icon_emoji, username='schubot'):
        if icon_emoji == None:
            icon_emoji = ':rabbit:'
        self.sc.api_call("chat.postMessage", channel=channel, text=text, username=username, icon_emoji=icon_emoji)

    def get_channelname(self, channel_id):
        for name in self.channel_info:
            if channel_id == self.channel_info[name]:
                return name
        return 'N/A'
        # too slow, use cache instead
        #channel_info = self.sc.api_call("channels.info", channel=channel_id)
        #if channel_info['ok'] == False:
        #    print("cannot resolve channel name".format(channel_info['error']))
        #    return 'N/A'
        #channelname = channel_info['channel']['name']
        #return channelname
    
    def get_username(self, slack_id):
        for name in self.user_info:
            if slack_id == self.user_info[name]:
                return name
        return 'N/A'
        # too slow, use cache instead
        #user_info = self.sc.api_call("users.info", user=slack_id)
        #username = user_info['user']['name']
        #return username
    
