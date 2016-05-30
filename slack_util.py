#!/usr/bin/env python
from slackclient import SlackClient
import yaml

config = yaml.load(open('rtmbot.conf', 'r'))
token = config.get('SLACK_TOKEN')

def get_channelname(channel_id):
    sc = SlackClient(token)
    channel_info = sc.api_call("channels.info", channel=channel_id)
    if channel_info['ok'] == False:
        print channel_info
        return 'N/A'
    channelname = channel_info['channel']['name']
    return channelname

def get_username(slack_id):
    sc = SlackClient(token)
    user_info = sc.api_call("users.info", user=slack_id)
    username = user_info['user']['name']
    return username

def get_client():
    return SlackClient(token)
