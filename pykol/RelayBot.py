from time import sleep
from datetime import datetime
from kol.Session import Session
from kol.manager.ChatManager import ChatManager
from bs4 import BeautifulSoup
import requests
import re

class RelayBot(object):
	rooms = {'clan': 0, 'dread': 1, 'hobopolis': 2, 'slimetube': 3, 'talkie': 5, 'who': 6}
	channels = {0: 'clan', 1: 'dread', 2: 'hobopolis', 3: 'slimetube', 5: 'talkie'}
	memberlistPattern = re.compile('memberlist.php')
	IRCMessagePattern = re.compile('(.+): (.+)')
	
	def __init__(self):
		self.session = Session()
		with open( 'passwords', 'r' ) as f:
			self.password = f.readline().strip()
			self.forumPassword = f.readline().strip()
		self.session.login( 'CGRelay', self.password )
		self.chatManager = ChatManager(self.session)
		self.cookies = {}
		self.lastMessageID = {0: 0, 1: 0, 2: 0, 3: 0, 5: 0}
	
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
		toSend = ''
		
		for user in message['users']:
			toSend += '{}, '.format( user['userName'] )
		
		self.mchatAdd( toSend[:-2], RelayBot.rooms['who'] )
	
	def runBot(self):
		self.forumLogin()
		while True:
			# Every 15 minutes, send /who
			if datetime.now().minute % 15 == 0:
				self.postWho( self.chatManager.sendChatMessage('/who') )
				
			chatMessages = self.chatManager.getNewChatMessages()
			for message in chatMessages:
				if ('channel' in message.keys()
				and message['channel'] in RelayBot.rooms.keys()
				and message['userName'] != 'CGRelay'):
					toSend = '[b]{0}:[/b] {1}'.format(message['userName'], message['text'])
					self.mchatAdd(toSend, RelayBot.rooms[message['channel']])
			
			for room in RelayBot.channels:
				self.mchatRead(room)
			
			sleep(3)

bot = RelayBot()
bot.runBot()