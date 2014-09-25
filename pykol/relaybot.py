from time import sleep
from kol.Session import Session
from kol.request.GetChatMessagesRequest import GetChatMessagesRequest
from kol.request.SendChatRequest import SendChatRequest

import urllib

session = Session()
password = 'thepassword'
session.login( 'CGRelay', password )
while True:
	chatRequest = getChatMessagesRequest(session)
	responseData = chatRequest.doRequest()

	chatMessages = responseData['chatMessages']

	for message in chatMessages:
		print message
	sleep(1)