from time import sleep
from datetime import datetime
from kol.Session import Session
from kol.manager.ChatManager import ChatManager
from bs4 import BeautifulSoup
import requests
import re
import logging
import traceback
import ConfigParser

class RelayBot(object):
	rooms = {'clan': 0, 'dread': 1, 'hobopolis': 2, 'slimetube': 3, 'talkie': 5, 'who': 6}
	channels = {0: 'clan', 1: 'dread', 2: 'hobopolis', 3: 'slimetube', 5: 'talkie'}
	memberlistPattern = re.compile('memberlist.php')
	IRCMessagePattern = re.compile('(.+): (.+)')
	
	def __init__(self):
		self.config = ConfigParser.RawConfigParser()
		self.config.read( '{}/config.cfg'.format( os.path.dirname( os.path.realpath(__file__) ) ) )
		
		self.session = Session()
		self.password = self.config.get( 'Passwords', 'KoLPassword' )
		self.session.login( 'CGRelay', self.password )
		self.chatManager = ChatManager(self.session)
		
		self.forumPassword = self.config.get( 'Passwords', 'forumPassword' )
		self.cookies = {}
		self.lastMessageID = {0: 0, 1: 0, 2: 0, 3: 0, 5: 0}
		
		self.logger = logging.getLogger('RelayBot')
		self.logger.basicConfig( format='%(levelname)s: %(asctime)s - %(message)s' )
		if self.config.has_option( 'Misc', 'logLevel' ):
			self.logger.setLevel( self.config.get( 'DEFAULT', 'logLevel' ) )
	
	def forumLogin(self):		
		data = {'mode': 'login', 'username': 'CGBot', 'password': self.forumPassword, 'login': 'Login'}
		r = requests.post( 'http://www.crimbogrotto.com/ucp.php', data=data )
		self.cookies = r.cookies
	
	def mchatRead(self, roomID):
		if self.lastMessageID[roomID] == 0:
			data = {'mode': 'read', 'room_id': roomID}
			r = requests.post( 'http://www.crimbogrotto.com/mchat.php', data=data, cookies = self.cookies )
			lastIDSoup = BeautifulSoup(r.text)
			self.lastMessageID[roomID] = int( lastIDSoup.find_all('div', class_='mChatHover')[-1]['id'][4:] )
		data = {'mode': 'read', 'room_id': roomID, 'message_last_id': self.lastMessageID[roomID]}
		
		r = requests.post( 'http://www.crimbogrotto.com/mchat.php', data=data, cookies = self.cookies )
		mchatSoup = BeautifulSoup(r.text)
		for messageDiv in mchatSoup.find_all( 'div', class_='mChatHover' ):
			name = messageDiv.find( 'a', href=RelayBot.memberlistPattern ).string
			self.lastMessageID[roomID] = int( messageDiv['id'][4:] )
			
			if name == 'CGBot':
				continue
			
			message = messageDiv.find('div', class_='mChatMessage').get_text()
			openBracket = '['
			closeBracket = ']'
			
			if name == 'CGIRC':
				IRCMessageMatch = re.match( RelayBot.IRCMessagePattern, message )
				name = IRCMessageMatch.group(1)
				message = IRCMessageMatch.group(2)
				openBracket = '{'
				closeBracket = '}'
				
			toSend = '/{0} {1}{2}{3} {4}'.format( RelayBot.channels[roomID], openBracket, name, closeBracket, message )
			self.chatManager.sendChatMessage(toSend)
	
	def mchatAdd(self, message, roomID):
		data = {'mode': 'add', 'room_id': roomID, 'message': message}
		r = requests.post( 'http://www.crimbogrotto.com/mchat.php', data=data, cookies = self.cookies )
	
	def postWho(self, message):
		toSend = ', '.join( [user['userName'] for user in message[0]['users']] )
		self.mchatAdd( toSend, RelayBot.rooms['who'] )
	
	def runBot(self):
		self.forumLogin()
		needsWho = True
		while True:
			try:
				# Every 15 minutes, send /who once
				if needsWho and datetime.now().minute % 15 == 0:
					self.postWho( self.chatManager.sendChatMessage('/who') )
					needsWho = False
				else if datetime.now().minute % 15 != 0:
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

bot = RelayBot()
bot.runBot()