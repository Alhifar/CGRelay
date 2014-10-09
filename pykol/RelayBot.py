from time import sleep
from kol.Session import Session
from kol.manager.ChatManager import ChatManager
from bs4 import BeautifulSoup
import requests
import re

class RelayBot(object):
	rooms = {'clan': 0, 'dread': 1, 'hobopolis': 2, 'slimetube': 3, 'talkie': 5}
	channels = {0: 'clan', 1: 'dread', 2: 'hobopolis', 3: 'slimetube', 5: 'talkie'}
	
	def __init__(self):
		self.session = Session()
		self.password = 'thepassword'
		self.forumPassword = 'theotherpassword'
		self.session.login( 'CGRelay', self.password )
		self.chatManager = ChatManager(self.session)
		self.cookies = {}
		self.lastMessageID = 0
	
	def forumLogin(self):		
		data = {'mode': 'login', 'username': 'CGBot', 'password': self.forumPassword, 'login': 'Login'}
		r = requests.post('http://www.crimbogrotto.com/ucp.php', data=data)
		self.cookies = r.cookies
	
	def mchatGet(self, roomID):
		if self.lastMessageID > 0:
			data = {'mode': 'read', 'room_id': roomID, 'message_last_id': self.lastMessageID}
		else:
			data = {'mode': 'read', 'room_id': roomID}
		r = requests.post('http://www.crimbogrotto.com/mchat.php', data=data, cookies = self.cookies)
		mchatSoup = BeautifulSoup(r.text)
		with open('temp.txt', 'w') as f:
			f.write(mchatSoup.find_all('div', class_='mChatHover'))
		
	
	def mchatPost(self, message, roomID):
		data = {'mode': 'add', 'room_id': roomID, 'message': message}
		r = requests.post('http://www.crimbogrotto.com/mchat.php', data=data, cookies = self.cookies)
	
	def runBot(self):
		self.forumLogin()
		while True:
			chatMessages = self.chatManager.getNewChatMessages()
			for message in chatMessages:
				if 'channel' in message.keys() and message['channel'] in RelayBot.rooms.keys():
					toSend = '[b]{0}:[/b] {1}'.format(message['userName'], message['text'])
					self.mchatPost(toSend, RelayBot.rooms[message['channel']])
			sleep(1)

bot = RelayBot()
bot.forumLogin()
bot.mchatGet(0)