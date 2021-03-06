from time import sleep
from datetime import datetime
from kol.Session import Session
from kol.manager.ChatManager import ChatManager
from bs4 import BeautifulSoup
from datetime import date
import requests
import re
import logging
import traceback
import ConfigParser
import pytz
import os


class RelayBot(object):
    rooms = {'clan': 0, 'dread': 1, 'hobopolis': 2, 'slimetube': 3, 'talkie': 5, 'who': 6}
    channels = {0: 'clan', 1: 'dread', 2: 'hobopolis', 3: 'slimetube', 5: 'talkie'}
    memberlistPattern = re.compile(r'memberlist\.php')
    IRCMessagePattern = re.compile(r'(.+?): (.+)')

    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('{}/config.cfg'.format(os.path.dirname(os.path.realpath(__file__))))

        self.session = Session()
        self.password = self.config.get('Passwords', 'KoLPassword')
        self.session.login('CGRelay', self.password)
        self.chatManager = ChatManager(self.session)

        self.forumPassword = self.config.get('Passwords', 'forumPassword')
        self.cookies = {}
        self.lastMessageID = {0: 0, 1: 0, 2: 0, 3: 0, 5: 0}
        self.logger = logging.getLogger('RelayBot')
        self.initLogger()

    def initLogger(self):
        formatter = logging.Formatter('%(levelname)s: %(asctime)s - %(message)s')

        logLevel = logging.WARNING
        if self.config.has_option('Misc', 'logLevel'):
            if self.config.get('Misc', 'logLevel') == 'DEBUG':
                logLevel = logging.DEBUG
            elif self.config.get('Misc', 'logLevel') == 'INFO':
                logLevel = logging.INFO
            elif self.config.get('Misc', 'logLevel') == 'WARNING':
                logLevel = logging.WARNING
            elif self.config.get('Misc', 'logLevel') == 'ERROR':
                logLevel = logging.ERROR
            elif self.config.get('Misc', 'logLevel') == 'CRITICAL':
                logLevel = logging.CRITICAL
            self.logger.setLevel(logLevel)

        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        self.logger.addHandler(sh)

        fh = logging.FileHandler(
            '{}/logs/RelayBot_{}.log'.format(os.path.dirname(os.path.realpath(__file__)), date.today().strftime('%d%m%Y')))
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def forumLogin(self):
        data = {'mode': 'login', 'username': 'CGBot', 'password': self.forumPassword, 'login': 'Login'}
        r = requests.post('http://www.crimbogrotto.com/ucp.php', data=data)
        self.cookies = r.cookies

    def mchatRead(self, roomID):
        if self.lastMessageID[roomID] == 0:
            data = {'mode': 'read', 'room_id': roomID}
            r = requests.post('http://www.crimbogrotto.com/mchat.php', data=data, cookies=self.cookies)
            lastIDSoup = BeautifulSoup(r.text)
            self.lastMessageID[roomID] = int(lastIDSoup.find_all('div', class_='mChatHover')[-1]['id'][4:])
        data = {'mode': 'read', 'room_id': roomID, 'message_last_id': self.lastMessageID[roomID]}

        r = requests.post('http://www.crimbogrotto.com/mchat.php', data=data, cookies=self.cookies)
        mchatSoup = BeautifulSoup(r.text)

        # Each message is contained in div with class mChatHover
        for messageDiv in mchatSoup.find_all('div', class_='mChatHover'):
            name = messageDiv.find('a', href=RelayBot.memberlistPattern).string
            self.lastMessageID[roomID] = int(messageDiv['id'][4:])

            if name == 'CGBot':
                continue

            message = messageDiv.find('div', class_='mChatMessage')

            # Replace smilies with text of smilie (images are disallowed, so all images should be smilies)
            imgs = message.find_all('img')
            for img in imgs:
                new_tag = mchatSoup.new_tag('div')
                new_tag.string = img['alt']
                img.replace_with(new_tag)

            links = message.find_all('a')
            for link in links:
                new_tag = mchatSoup.new_tag('div')
                if link.string != link['href']:
                    new_tag.string = '{}( {} )'.format(link.string, link['href'])
                else:
                    new_tag.string = link.string
                link.replace_with(new_tag)

            # Collapse message to only plain text and adjust for correct bracketing based on message source
            messageText = message.get_text()
            openBracket = '['
            closeBracket = ']'

            if name == 'CGIRC':
                IRCMessageMatch = re.match(RelayBot.IRCMessagePattern, messageText)
                name = IRCMessageMatch.group(1)
                messageText = IRCMessageMatch.group(2)
                openBracket = '{'
                closeBracket = '}'

            toSend = '/{0} {1}{2}{3} {4}'.format(RelayBot.channels[roomID], openBracket, name, closeBracket,
                                                 messageText)
            self.chatManager.sendChatMessage(toSend)

    def mchatAdd(self, message, roomID):
        data = {'mode': 'add', 'room_id': roomID, 'message': message}
        requests.post('http://www.crimbogrotto.com/mchat.php', data=data, cookies=self.cookies)

    def postWho(self, message):
        toSend = ', '.join([user['userName'] for user in message[0]['users']])
        self.mchatAdd(toSend, RelayBot.rooms['who'])

    def runBot(self):
        self.forumLogin()
        needsWho = True
        koltz = pytz.timezone('America/Phoenix')
        currentTime = koltz.localize(datetime.now())
        while currentTime.hour != 21 or not (30 <= currentTime.minute <= 45):
            try:
                # Every 15 minutes, send /who once
                if needsWho and datetime.now().minute % 15 == 0:
                    self.postWho(self.chatManager.sendChatMessage('/who'))
                    needsWho = False
                elif not needsWho and datetime.now().minute % 15 != 0:
                    needsWho = True
            except Exception:
                self.logger.warning(traceback.format_exc())

            try:
                chatMessages = self.chatManager.getNewChatMessages()
                for message in chatMessages:
                    if ('channel' in message.keys()
                        and message['channel'] in RelayBot.rooms.keys()
                        and message['userName'] != 'CGRelay'):
                        toSend = '[b]{0}:[/b] {1}'.format(message['userName'], message['text'])
                        self.mchatAdd(toSend, RelayBot.rooms[message['channel']])
            except Exception:
                self.logger.warning(traceback.format_exc())

            try:
                for room in RelayBot.channels:
                    self.mchatRead(room)
            except Exception:
                self.logger.warning(traceback.format_exc())

            sleep(3)

            currentTime = koltz.localize(datetime.now())


bot = RelayBot()
bot.runBot()