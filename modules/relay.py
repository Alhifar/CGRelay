from willie import module
from willie import web
from willie import tools
import willie.irc as irc
import re
import HTMLParser
from bs4 import BeautifulSoup

#logger = tools.OutputRedirect("/home/crimbogrotto/.willie/logs/relaylog.log")

#Patterns for relay()
actionPattern = re.compile(r'^\x01ACTION')
colorPattern = re.compile(r'^\x03\d+(?:,\d+)?')
nonAsciiPattern = re.compile(r'[^\x00-\x7f]')
hiddenPattern = re.compile(r'(?i)irc:.*')

KoLMessagePattern = re.compile(r'^(.+?): (.+)$')
memberlistPattern = re.compile(r'memberlist\.php')


@module.rule('.*')
@module.disallow_privmsg
def relay(bot, trigger):
    #global logger
    sid = bot.getForumSID()
    message = re.sub(actionPattern, '', trigger.group(0))  #Remove ACTION from /me messages
    message = re.sub(colorPattern, '', message)  # Remove color codes
    message = re.sub(nonAsciiPattern, '', message)  #remove non-ascii characters 'cause forum chat and kol chat are dumb
    message = re.sub(hiddenPattern, '', message)  #messages starting with "irc:" are hidden from kol chat
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
        lastIDSoup = BeautifulSoup(text)
        bot.memory['lastMChatID'] = int(lastIDSoup.find_all('div', class_='mChatHover')[-1]['id'][4:])

    params = 'mode=read&room_id=0&message_last_id={0!s}&sid={1}'.format(bot.memory['lastMChatID'], sid)
    text = web.post('http://www.crimbogrotto.com/mchat.php', params)
    mchatSoup = BeautifulSoup(text)
    # Each message is contained in div with class mChatHover
    for messageDiv in mchatSoup.find_all('div', class_='mChatHover'):
        sender = messageDiv.find('a', href=memberlistPattern).string
        bot.memory['lastMChatID'] = int(messageDiv['id'][4:])

        if sender == 'CGIRC':
            continue

        message = messageDiv.find('div', class_='mChatMessage')

        # Replace smilies with text of smilie (images are disallowed, so all images should be smilies)
        imgs = message.find_all('img')
        for img in imgs:
            new_tag = mchatSoup.new_tag('div')
            new_tag.string = img['alt']
            img.replace_with(new_tag)

        links = message.find_all('a')
        for link in links:
            new_tag = mchatSoup.new_tag('div')
            if link.string != link['href']:
                new_tag.string = '{} ({})'.format(link['href'], link.string)
            else:
                new_tag.string = link.string
            link.replace_with(new_tag)

        # Collapse message to only plain text and adjust for correct bracketing based on message source
        messageText = message.get_text()
        openBracket = '['
        closeBracket = ']'

        if sender == 'CGBot':
            KoLMessageMatch = re.match(KoLMessagePattern, messageText)
            sender = KoLMessageMatch.group(1)
            messageText = KoLMessageMatch.group(2)
            openBracket = '{'
            closeBracket = '}'
        if message == '':
            return
        parser = HTMLParser.HTMLParser()
        toSend = u'{0}{1}{2}: {3}'.format(openBracket, sender, closeBracket, parser.unescape(messageText))
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
    lastIDSoup = BeautifulSoup(whoText)
    whoMessage = lastIDSoup.find_all('div', class_='mChatHover')[-1].text
    bot.msg(trigger.nick, whoMessage.decode('utf-8'), relay=False)


def configure(config):
    config.add_section('relay')
    interactive_add('relay', 'forum_password', 'What is the forum password?')