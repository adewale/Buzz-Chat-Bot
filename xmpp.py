# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.utils import html
from google.appengine.ext.webapp import xmpp_handlers

import logging
import urllib

class Tracker(object):
  def _valid_subscription(self, message_body):
    return self.extract_search_term(message_body) != ''

  def extract_search_term(self, message_body):
    search_term = message_body[len('/track'):]
    return search_term.strip()

  def _subscribe(self, message_sender, message_body):
    url = self._build_url(message_body)
    logging.info('Subscribing to: %s for user: %s' % (url, message_sender))
    return True

  def _build_url(self, message_body):
    search_term = urllib.quote(self.extract_search_term(message_body))
    return 'https://www.googleapis.com/buzz/v1/activities/track?q=%s' % search_term

  def track(self, message_sender, message_body):
    if self._valid_subscription(message_body):
      return self._subscribe(message_sender, message_body)
    else:
      return False

commands = [
  '/help Prints out this message\n',
  '/track [search term] Starts tracking the given search term\n'
]

class MessageBuilder(object):
  def __init__(self):
    self.lines = []

  def build_message(self):
    text = ''
    for index,line in enumerate(self.lines):

      text += html.escape(line)
      if (index+1) !=len(self.lines):
        text += '<br></br>'

    message = '''<html xmlns='http://jabber.org/protocol/xhtml-im'>
    <body xmlns="http://www.w3.org/1999/xhtml">
    %s
    </body>
    </html>''' % text
    message = message.strip()
    message = message.encode('ascii', 'xmlcharrefreplace')
    return message

  def add(self, line):
    self.lines.append(line)

class XmppHandler(xmpp_handlers.CommandHandler):
  def _reply(self, message_builder, message):
    message_to_send = message_builder.build_message()
    logging.info('Message that will be sent: %s' % message_to_send)
    message.reply(message_to_send, raw_xml=True)

  def help_command(self, message=None):
    logging.info('Received message from: %s' % message.sender)

    lines = ['We all need a little help sometimes']
    lines.extend(commands)

    message_builder = MessageBuilder()
    for line in lines:
      message_builder.add(line)
    self._reply(message_builder, message)

  def track_command(self, message=None):
    logging.info('Received message from: %s' % message.sender)

    tracker = Tracker()
    message_builder = MessageBuilder()
    if (tracker.track(message.sender, message.body)):
      message_builder.add('Tracking: %s' % tracker.extract_search_term(message.body))
      self._reply(message_builder, message)
    else:
      message_builder.add('Sorry there was a problem with your last track command <%s>' % message.body)
      self._reply(message_builder, message)