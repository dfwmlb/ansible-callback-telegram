from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: telegram
    callback_type: notification
    requirements:
      - whitelist in configuration
      - telebot (pip install pyTelegramBotApi)
      - prettytable (pip install prettytable)
      - latest requests (pip install requests --upgrade)
    short_description: Sends play events to a telegram channel
    version_added: "2.1"
    description:
        - This is an ansible callback plugin that sends status updates to a telegram channel during playbook execution.
        - Before 2.4 only environment variables were available for configuring this plugin
    options:
      tg_token:
        required: True
        description: telegram bot token
        env:
          - name: TG_TOKEN
        ini:
          - section: callback_telegram
            key: tg_token
      tg_chat_id:
        required: True
        description: telegram chat id to post in.
        env:
          - name: TG_CHAT_ID
        ini:
          - section: callback_telegram
            key: tg_chat_id
      socks5_uri:
        description: socks5 proxy uri to bypass rkn's restarictions
        env:
          - name: SOCKS5_URI
        ini:
          - section: callback_telegram
            key: socks5_uri
'''

import os
from datetime import datetime

from ansible import context
from ansible.module_utils._text import to_text
from ansible.module_utils.urls import open_url
from ansible.plugins.callback import CallbackBase

try:
    import telebot
    from telebot import apihelper
    HAS_TELEBOT = True
except ImportError:
    HAS_TELEBOT = False

try:
    import prettytable
    HAS_PRETTYTABLE = True
except ImportError:
    HAS_PRETTYTABLE = False

class CallbackModule(CallbackBase):
    """This is an ansible callback plugin that sends status
    updates to a telegram channel during playbook execution.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'telegram'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):

        super(CallbackModule, self).__init__(display=display)

        if not HAS_TELEBOT:
            self.disabled = True
            self._display.warning('The `telebot` python module is not '
                                  'installed. Disabling the Slack callback '
                                  'plugin.')

        if not HAS_PRETTYTABLE:
            self.disabled = True
            self._display.warning('The `prettytable` python module is not '
                                  'installed. Disabling the Slack callback '
                                  'plugin.')

        self.playbook_name = None
        self.play = None
        self.now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def set_options(self, task_keys=None, var_options=None, direct=None):

        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.tg_token = self.get_option('tg_token')
        self.tg_chat_id = self.get_option('tg_chat_id')
        self.socks5_uri = self.get_option('socks5_uri')

        if self.tg_token is None:
            self.disabled = True
            self._display.warning('tg_token was not provided. The '
                                  'tg_token can be provided using '
                                  'the `TG_TOKEN` environment '
                                  'variable.')

        if self.tg_chat_id is None:
            self.disabled = True
            self._display.warning('tg_chat_id was not provided. The '
                                  'tg_chat_id can be provided using '
                                  'the `TG_CHAT_ID` environment '
                                  'variable.')

    def send_msg(self, msg):
        apihelper.proxy = {'https': self.socks5_uri}
        bot = telebot.TeleBot(self.tg_token)
        bot.send_message(self.tg_chat_id, msg, parse_mode='HTML')

    def v2_playbook_on_start(self, playbook):
        
        self.playbook_name = os.path.abspath(playbook._file_name)

    def v2_playbook_on_play_start(self, play):
        self.play = play

        title = [
            '<u><b>Ansible:</b></u> <b>STARTED</b> ⚙️'
        ]

        msg_items = [' '.join(title)]
        msg_items.append('\n         time: ' + '<code>' + str(self.now) + '</code>')
        msg_items.append('playbook: ' + '<code>' + self.playbook_name + '</code>')
        msg_items.append('       hosts:')
        for host in play.hosts:
            msg_items.append('<code>     - ' + host + '</code>')
        msg_items.append('       tags:')
        for tag in play.only_tags:
            msg_items.append('<code>     - ' + tag + '</code>')
        msg = '\n'.join(msg_items)
        self.send_msg(msg=msg)

    def v2_runner_on_failed(self, result, ignore_errors=False):

        msg = []
        title = [
            '<u><b>Ansible:</b></u> <b>FAILED ❌</b>'
        ]
        msg_items = [' '.join(title)]
        msg_items.append('\n         time: ' + '<code>' + str(self.now) + '</code>')
        msg_items.append('playbook: ' + '<code>' + self.playbook_name + '</code>')
        msg_items.append('        host: ' + '<code>' + result._host.get_name() + '</code>')
        msg_items.append('      stderr: ' + '<code>' + result._result['stderr'] + '</code>')

        msg = '\n'.join(msg_items)

        self.send_msg(msg=msg)

    def v2_playbook_on_stats(self, stats):
        """Display info about playbook statistics"""

        hosts = sorted(stats.processed.keys())

        t = prettytable.PrettyTable(['Host', 'Ok', 'Changed', 'Unreachable',
                                     'Failures', 'Rescued', 'Ignored'])

        failures = False
        unreachable = False

        for h in hosts:
            s = stats.summarize(h)

            if s['failures'] > 0:
                failures = True
            if s['unreachable'] > 0:
                unreachable = True

            t.add_row([h] + [s[k] for k in ['ok', 'changed', 'unreachable',
                                            'failures', 'rescued', 'ignored']])

        msg = []
        title = '<u><b>Ansible:</b></u> <b>ENDED</b>'
        if failures or unreachable:
            msg_items = [
                title + ' ❌'
            ]
        else:
            msg_items = [
                title + ' ✅'
            ]
        msg_items.append('\n         time: ' + '<code>' + str(self.now) + '</code>')
        msg_items.append('playbook: ' + '<code>' + self.playbook_name + '</code>')
        msg_items.append('<code>\n%s\n</code>' % t)

        msg = '\n'.join(msg_items)

        self.send_msg(msg=msg)