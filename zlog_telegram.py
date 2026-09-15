import logging
from typing import Dict, Optional, List, Tuple
from urllib.parse import quote_plus
from json import loads
import requests
from dataclasses import dataclass, field

import reply


@dataclass
class Line:
    msg: str
    nick: Optional[str]


@dataclass
class Chat:
    window: str
    nick: str
    active: bool = True
    history: List[Line] = field(default_factory=list)

    @property
    def query(self) -> bool:
        return self.window.replace('#', '') == self.nick


inactive = Chat('', '')


class ZlogTelegram:
    def __init__(self, token: str, chat_id: str, offset: int):
        self.token: str = token
        self.chat_id: str = chat_id
        self.chats: Dict[Tuple[str, str], Chat] = {}
        self._active: Tuple[str, str] = ('', '')
        self.offset: int = offset
        logging.basicConfig(filename='/home/znc/zlog_telegram/zlog_telegram.log', level=logging.ERROR)

    @property
    def active(self) -> Tuple[str, str]:
        return self._active

    @active.getter
    def active(self) -> Chat:
        active: Chat
        active = self.chats[self._active] if self._active else inactive
        return active

    @active.setter
    def active(self, chat: Tuple[str, str]):
        if self._active != chat and self._active != ('', ''):
            self.chats[self._active].active = False
        self.chats[chat].active = True
        self._active = chat

    def add_chat(self, window: str, nick: str):
        chat_id = (window, nick)
        self.chats[chat_id] = Chat(window, nick)
        self.active = chat_id

    def send(self, message: str):
        url = f'https://api.telegram.org/bot{self.token}' \
              f'/sendMessage?chat_id={self.chat_id}' \
              f'&text={quote_plus(message)}'

        resp = requests.get(url)
        if not resp.ok:
            logging.error(resp.text)

    # def fetch(self):
    #     url = f'https://api.telegram.org/bot{self.token}/getUpdates?offset={self.offset}'
    #     res = requests.post(url).json()
    #     print(res)
    #     if res['result']:
    #         self.offset = res['result'][-1]['update_id'] + 1
    #         messages: list = []
    #         for msg in res['result']:
    #             messages.append(reply.consume(msg['message'], msg['update_id']))
    #         return messages

    def fetch(self):
        url = f'https://api.telegram.org/bot{self.token}/getUpdates?offset={self.offset}'
        resp = requests.get(url)
        if not resp.ok:
            logging.error(f"HTTP Error {resp.status_code}: {resp.text}")
            return
        res = resp.json()

        
        # Improved error handling
        if not res.get('ok'):
            logging.error(f"Telegram API error: {res.get('description', 'No description provided')}")
            print('check errror log')
            return None
        
        if 'result' in res and res['result']:
            self.offset = res['result'][-1]['update_id'] + 1
            messages = [reply.consume(msg['message'], msg['update_id']) for msg in res['result']]
            return messages
        return None
    
    def push(self, message: str):
        chat = self.active
        composed = f'<{chat.nick}> {message}'
        if not chat.query:
            composed = f'{chat.window}: {composed}'

        self.send(composed)
        self.active.history.append(Line(message, chat.nick))
