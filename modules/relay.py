from willie import module
from willie import web
from willie import tools
import willie.irc as irc
from datetime import datetime,timedelta
import re
import HTMLParser

#logger = tools.OutputRedirect("/home/crimbogrotto/.willie/logs/relaylog.log")
class Relay:
	broadcastInterval = 60
	
	@module.rule('.*')
	@module.disallow_privmsg
	def relay(bot, trigger):
		#global logger
		sid = bot.getForumSID()
		message = re.sub( r'^\x01ACTION', '', trigger.group(0) ) #Remove ACTION from /me messages
		message = re.sub( r'^\x03\d+(?:,\d+)?', '', message ) # Remove color codes
		message = re.sub( r'[^\x00-\x7f]', '', message ) #remove non-ascii characters 'cause forum chat and kol chat are dumb
		message = re.sub( r'(?i)irc:.*', '', message ) #messages starting with "irc:" are hidden from kol chat
		if message == '':
			return
		toPost = web.quote( u'[b]{0}:[/b] {1}'.format(trigger.nick, message) )
		text = web.post( "http://www.crimbogrotto.com/mchat.php", "room_id=0&mode=add&sid={0}&message={1}".format(sid, toPost) )
		return

	@module.interval(60*broadcastInterval)
	def postBroadcastLine(bot):
		bot.msg('#crimbogrotto', r'http://grooveshark.com/#!/thecgradio/broadcast' )

	@module.commands('set_broadcast_interval')
	def setBroadcastInterval(bot, trigger):
		this.broadcastInterval = int(trigger.group(2))
		bot.reply('Set broadcast announcement interval to {}'.format(this.broadcastInterval))

	@module.interval(3)
	def getFromRelay(bot):
		#global logger
		if not "#crimbogrotto" in bot.channels:
			return
		sid = bot.getForumSID()
		if not 'lastMChatID' in bot.memory.keys():
				text = web.post( 'http://www.crimbogrotto.com/mchat.php','mode=read&room_id=0&sid={0}'.format(sid) )
				messageIter = re.finditer( r'<div.+?mess(\d+).+?>.+?<a href=.+?>([^<]+)</a>.+?</span>.+?<div class="mChatMessage">(.+?)</div></div>', text)
				for messageMatch in messageIter:
					bot.memory['lastMChatID'] = int(messageMatch.group(1))

		text = web.post( 'http://www.crimbogrotto.com/mchat.php','mode=read&room_id=0&message_last_id={0!s}&sid={1}'.format(bot.memory['lastMChatID'], sid) )
		messageIter = re.finditer( r'<div.+?mess(\d+).+?>.+?<a href=.+?>([^<]+)</a>.+?</span>.+?<div class="mChatMessage">(.+?)</div></div>', text)
		parser = HTMLParser.HTMLParser()
		for messageMatch in messageIter:
			if messageMatch.group(2) != "CGIRC":
				sender = messageMatch.group(2)
				message = messageMatch.group(3)
				message = re.sub( r'<img src="\./images/smilies.+?alt="([^"]+?)".+?/>', r'\1', message ) #Replace smilies from forum
				message = re.sub( r'<a.*?href=\"(.+?)".*?>.*?</a>', r'\1', message ) #Replace links with just url
				message = re.sub( r'<.*?>', '', message ) #Remove all other tags
				openBracket = "{"
				closeBracket = "}"
				if sender == "CGBot":
					nameMatch = re.match( r'^(.+?): (.+)$', message )
					sender = nameMatch.group(1)
					message = nameMatch.group(2)
					openBracket = "["
					closeBracket = "]"
				if message == '':
					return
				bot.msg("#crimbogrotto", u'{0}{1}{2}: {3}'.format(openBracket, sender, closeBracket, parser.unescape(message)), 10, False )
				bot.memory['lastMChatID'] = int(messageMatch.group(1))
		return

	@module.commands('who')
	@module.require_privmsg
	def who(bot, trigger):
		sid = bot.getForumSID()
		whoText = web.post( 'http://www.crimbogrotto.com/mchat.php','mode=read&room_id=6&sid={0}'.format(sid) )
		lastWhoID = 0
		messageIter = re.finditer( r'<div.+?mess(\d+).+?>.+?<a href=.+?>([^<]+)</a>.+?</span>.+?<div class="mChatMessage">(.+?)</div></div>', whoText)
		messageMatch = None
		for messageMatch in messageIter:
			pass
		bot.reply( messageMatch.group(3) )

	def configure(config):
		config.add_section('relay')
		interactive_add('relay', 'forum_password', 'What is the forum password?')