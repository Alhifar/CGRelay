from time import sleep
from kol.Session import Session
from kol.manager.ChatManager import ChatManager
from bs4 import BeautifulSoup
import requests
import re

class RelayBot(object):
	def __init__(self):
		self.session = Session()
		self.password = 'thepassword'
		self.forumPassword = 'theotherpassword'
		self.session.login( 'CGRelay', self.password )
		self.chatManager = ChatManager(self.session)
		self.SID = ''
	
	def forumLogin(self):
		loginPageResponse = requests.post('http://www.crimbogrotto.com/ucp.php', params={'mode': 'login'})
		loginPageSoup = BeautifulSoup(loginPageResponse.text)
		self.SID = loginPageSoup.find('input', {'name': 'sid'})['value']
		
		params = {'username': 'CGBot', 'password': self.forumPassword, 'sid': self.SID, 'redirect': './ucp.php?mode=login', 'login': 'Login'}
		r = requests.post('http://www.crimbogrotto.com/ucp.php?mode=login', params=params)
		print(r.url)
	
	def runBot(self):
		self.forumLogin()
		while True:
			chatMessages = self.chatManager.getNewChatMessages()
			for message in chatMessages:
				pass
				#do stuff
			sleep(1)

bot = RelayBot()
bot.runBot()