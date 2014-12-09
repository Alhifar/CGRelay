from willie import module
from willie import web
# from willie import tools
import willie.irc as irc
import re
import HTMLParser

#logger = tools.OutputRedirect("/home/crimbogrotto/.willie/logs/relaylog.log")

#Patterns for relay()
actionPattern = re.compile(r'^\x01ACTION')
colorPattern = re.compile(r'^\x03\d+(?:,\d+)?')
nonAsciiPattern = re.compile(r'[^\x00-\x7f]')
hiddenPattern = re.compile(r'(?i)irc:.*')

#Patterns for getFromRelay()
mchatPattern = re.compile(
    r'<div.+?mess(\d+).+?>.+?<a href=.+?>([^<]+)</a>.+?</span>.+?<div class="mChatMessage">(.+?)</div></div>')
smiliesPattern = re.compile(r'<img src="\./images/smilies.+?alt="([^"]+?)".+?/>')
linkPattern = re.compile(r'<a.*?href=\"(.+?)".*?>(.*?)</a>')
tagPattern = re.compile(r'<.*?>')
CGBotMessagePattern = re.compile(r'^(.+?): (.+)$')

#Pattern for who()
whoPattern = re.compile(
    r'<div.+?mess(\d+).+?>.+?<a href=.+?>([^<]+)</a>.+?</span>.+?<div class="mChatMessage">(.+?)</div></div>')


@module.rule('.*')
@module.disallow_privmsg
def relay(bot, trigger):
    #global logger
    sid = bot.getForumSID()
    message = actionPattern.sub('', trigger.group(0))  #Remove ACTION from /me messages
    message = colorPattern.sub('', message)  # Remove color codes
    message = nonAsciiPattern.sub('', message)  #remove non-ascii characters 'cause forum chat and kol chat are dumb
    message = hiddenPattern.sub('', message)  #messages starting with "irc:" are hidden from kol chat
    if message == '':
        return
    toPost = web.quote(u'[b]{0}:[/b] {1}'.format(trigger.nick, message))
    web.post('http://www.crimbogrotto.com/mchat.php',
             'room_id=0&mode=add&sid={0}&message={1}'.format(sid, toPost))
    return


@module.commands('announce_broadcast')
def postBroadcastLine(bot, trigger=None):
    with open('/williedata/currentSong', 'r') as songFile:
        currentSong = songFile.read()
    bot.msg('#crimbogrotto', 'Listen to CG Radio, now playing {0}!'.format(currentSong))
    bot.msg('#crimbogrotto', r'http://grooveshark.com/#!/thecgradio/broadcast')


@module.interval(900)
def postIRCWho(bot, trigger=None):
    sid = bot.getForumSID()
    users = bot.privileges['#crimbogrotto'].keys()
    web.post('http://www.crimbogrotto.com/mchat.php',
             'room_id=7&mode=add&sid={0}&message={1}'.format(sid, ', '.join(users)))


@module.interval(3)
def getFromRelay(bot):
    #global logger
    if not "#crimbogrotto" in bot.channels:
        return
    sid = bot.getForumSID()
    if not 'lastMChatID' in bot.memory.keys():
        text = web.post('http://www.crimbogrotto.com/mchat.php', 'mode=read&room_id=0&sid={0}'.format(sid))
        messageList = mchatPattern.findall(text)
        bot.memory['lastMChatID'] = int(messageList[-1][0])

    params = 'mode=read&room_id=0&message_last_id={0!s}&sid={1}'.format(bot.memory['lastMChatID'], sid)
    text = web.post('http://www.crimbogrotto.com/mchat.php', params)
    messageIter = mchatPattern.finditer(text)
    parser = HTMLParser.HTMLParser()
    for messageMatch in messageIter:
        if messageMatch.group(2) != 'CGIRC':
            sender = messageMatch.group(2)
            message = messageMatch.group(3)
            message = smiliesPattern.sub(r'\1', message)  #Replace smilies from forum
            linkMatch = linkPattern.match(message)
            if linkMatch:
                if linkMatch.group(1) != linkMatch.group(2):
                    message = linkPattern.sub(r'\2 (\1)', message)  #Replace links with url and text
                else:
                    message = linkPattern.sub(r'\1', message)
            message = tagPattern.sub('', message)  #Remove all other tags
            openBracket = '{'
            closeBracket = '}'
            if sender == 'CGBot':
                nameMatch = CGBotMessagePattern.match(message)
                sender = nameMatch.group(1)
                message = nameMatch.group(2)
                openBracket = '['
                closeBracket = ']'
            if message == '':
                return
            toSend = u'{0}{1}{2}: {3}'.format(openBracket, sender, closeBracket, parser.unescape(message))
            bot.msg('#crimbogrotto', toSend, 10, False)
            bot.memory['lastMChatID'] = int(messageMatch.group(1))
    return


@module.rule('(?i).*?denis.*?')
def denisKick(bot, trigger):
    if trigger.nick != 'CGBot' and trigger.nick != 'Alhifar':
        bot.write(['KICK', trigger.sender, trigger.nick, 'Bad {0}'.format(trigger.nick)])


@module.commands('who')
@module.require_privmsg
def who(bot, trigger):
    sid = bot.getForumSID()
    whoText = web.post('http://www.crimbogrotto.com/mchat.php', 'mode=read&room_id=6&sid={0}'.format(sid))
    messageList = whoPattern.findall(whoText)
    bot.msg(trigger.nick, messageList[-1][2].decode('utf-8'), relay=False)


def configure(config):
    config.add_section('relay')
    interactive_add('relay', 'forum_password', 'What is the forum password?')