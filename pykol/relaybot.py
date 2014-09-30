from time import sleep
from kol.Session import Session
from kol.manager.ChatManager import ChatManager
import requests
import re

class RelayBot(object):
	def __init__(self):
		self.session = Session()
		self.password = 'thepassword'
		self.forumPassword = 'theotherpassword'
		session.login( 'CGRelay', password )
		self.chatManager = ChatManager(session)
		self.SID = ''
	def forumLogin():
		params = {'mode': 'login', 'username': 'CGBot', 'password': self.forumPassword}
			r = requests.post('http://www.crimbogrotto.com/ucp.php', params=params)
			m = re.match(r'\?sid=([^"]+)"', r.text)
			self.SID = m.group(0)
	def runBot():
		forumLogin()
		while True:
			chatMessages = self.chatManager.getNewChatMessages()
			for message in chatMessages:
				#do stuff
			sleep(1)