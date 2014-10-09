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
		self.SID = ''
		self.cookies = {}
	
	def forumLogin(self):
		loginPageResponse = requests.post('http://www.crimbogrotto.com/ucp.php', params={'mode': 'login'})
		loginPageSoup = BeautifulSoup(loginPageResponse.text)
		self.SID = loginPageSoup.find('input', {'name': 'sid'})['value']
		
		data = {'mode': 'login', 'username': 'CGBot', 'password': self.forumPassword, 'sid': self.SID, 'login': 'Login'}
		r = requests.post('http://www.crimbogrotto.com/ucp.php', data=data)
		self.cookies = r.cookies
	
	def mchatGet(self, roomID):
		data = {'mode': 'read', 'room_id': roomID, 'message_last_id': lastID, 'sid': self.SID}
		#mchat.php?mode=read&room_id=" + room_id + "&message_last_id=" + lid + "&sid=" + sid
	
	def mchatPost(self, message, roomID):
		data = {'mode': 'add', 'room_id': roomID, 'message': message}
		r = requests.post('http://www.crimbogrotto.com/mchat.php', data=data, cookies = self.cookies)
		with open('temp.txt', 'w') as f:
			f.write(str(r.status_code) + "\n" + r.text)
	
	def runBot(self):
		self.forumLogin()
		while True:
			chatMessages = self.chatManager.getNewChatMessages()
			for message in chatMessages:
				if 'channel' in message.keys() and message['channel'] in rooms.keys():
					toSend = '[b]{0}:[/b] {1}'.format(message['userName'], message['text'])
					self.mchatPost(toSend, rooms[message['channel']])
			sleep(1)

bot = RelayBot()
bot.runBot()