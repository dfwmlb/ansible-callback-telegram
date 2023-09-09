# Ansible Callback plugin for Telegram
Used for your ansible playbook notification delivery
Its highly recommended to use socks5 proxy to bypass [RKN](https://en.wikipedia.org/wiki/Roskomnadzor)'s restrictions but its not required (installed tor with socks5 proxy are perfect)

## Requiremets
This plugin requires python libs:
  - pyTelegramBotApi
  - prettytable

## Install
1. Install python libraries and upgrade requests lib to latest

    ```sh
    $ pip install pyTelegramBotApi
    $ pip install prettytable
    $ pip install requests --upgrade
    ```

2. Download plugin and put it to ansible

    ```sh
    $ cd /path/to/your/ansible/plugins/callback
    $ curl -O https://raw.githubusercontent.com/dfwmlb/ansible-callback-telegram/master/telegram.py
    ```

3. Add configuration to your ansible.cfg

    ```sh
    callback_whitelist = telegram

    [callback_telegram]
    tg_token = ENTER_TOKEN
    tg_chat_id = ENTER_CHAT_ID
    socks5_uri = socks5://localhost:9050
    ```

## Screens
<p align="center">
  <img src="./img/telegram_py.png">
</p>