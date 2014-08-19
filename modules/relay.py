from willie import module
from willie import web
from willie import tools
import willie.irc as irc
from datetime import datetime,timedelta
import re
import HTMLParser

logger = tools.OutputRedirect("/home/crimbogrotto/.willie/logs/relaylog.log")

cacheUpdateTime = timedelta(minutes=5)

cachedSID = ""
lastSIDUpdate = datetime.fromtimestamp(0)

lastMChatID = 0
lastMChatUpdate = datetime.fromtimestamp(0)

forumPassword = '@PASSWORD@'

def login():
	text = web.post( "http://www.crimbogrotto.com/ucp.php?","mode=login&username=CGIRC&password=" + forumPassword + "&redirect=./ucp.php?mode=login&redirect=index.php&login=Login");
	SIDMatch = re.search( r'\?sid=([^"]+)"',text )
	global cachedSID
	cachedSID = SIDMatch.group(1)
	global lastSIDUpdate 
	lastSIDUpdate = datetime.now()
	return cachedSID
	

def getSID():
	nextSIDUpdate = lastSIDUpdate + cacheUpdateTime
	if datetime.now() < nextSIDUpdate:
		global cachedSID
		return cachedSID
	else:
		return login()
	
	
@module.rule('.*')
@module.disallow_privmsg
def relay(bot, trigger):
	#global logger
	sid = getSID()
	message = re.sub( r'^\x01ACTION', '', trigger.group(0) )
	#message = re.sub( r'^\x01\d+(?:,\d+)?', '', message )# Trying to get rid of color codes
	toPost = web.quote( "[b]" + trigger.nick + ":[/b] " + message )
	text = web.post( "http://www.crimbogrotto.com/mchat.php", "room_id=0&mode=add&sid=" + sid + "&message=" + toPost )
	return
	
@module.interval(3)
def getFromRelay(bot):
	#global logger
	if not "#crimbogrotto" in bot.channels:
		return
	sid = getSID()
	global lastMChatID
	if lastMChatID == 0:
			text = web.post( "http://www.crimbogrotto.com/mchat.php","mode=read&room_id=0&sid=" + sid )
			messageIter = re.finditer( r'<div.+?mess(\d+).+?>.+?<a href=.+?>([^<]+)</a>.+?</span>.+?<div class="mChatMessage">(.+?)</div></div>', text)
			for messageMatch in messageIter:
				lastMChatID = int(messageMatch.group(1))

	text = web.post( "http://www.crimbogrotto.com/mchat.php","mode=read&room_id=0&message_last_id="+str(lastMChatID)+"&sid=" + sid )
	messageIter = re.finditer( r'<div.+?mess(\d+).+?>.+?<a href=.+?>([^<]+)</a>.+?</span>.+?<div class="mChatMessage">(.+?)</div></div>', text)
	parser = HTMLParser.HTMLParser()
	for messageMatch in messageIter:
		if messageMatch.group(2) != "CGIRC":
			sender = messageMatch.group(2)
			message = messageMatch.group(3)
			message = re.sub( r'<img src="\./images/smilies.+?alt="([^"]+?)".+?/>', r'\1', message )
			message = re.sub( r'<a.*?href=\"(.+?)".*?>.*?</a>', r'\1', message )
			message = re.sub( r'<.*?>', '', message )
			openBracket = "{"
			closeBracket = "}"
			if sender == "CGBot":
				nameMatch = re.match( r'^(.+?): (.+)$', message )
				sender = nameMatch.group(1)
				message = nameMatch.group(2)
				openBracket = "["
				closeBracket = "]"
			bot.msg("#crimbogrotto", openBracket + sender + closeBracket + ": " + parser.unescape(message), 1, False )
			lastMChatID = int(messageMatch.group(1))
	return

@module.commands('who')
@module.require_privmsg
def who(bot, trigger):
	sid = bot.getForumSID()
	whoText = web.post( "http://www.crimbogrotto.com/mchat.php","mode=read&room_id=6&sid=" + sid )
	lastWhoID = 0
	messageIter = re.finditer( r'<div.+?mess(\d+).+?>.+?<a href=.+?>([^<]+)</a>.+?</span>.+?<div class="mChatMessage">(.+?)</div></div>', whoText)
	messageMatch = None
	for messageMatch in messageIter:
		pass
	bot.reply( messageMatch.group(3) )