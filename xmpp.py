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

class XmppHandler(xmpp_handlers.CommandHandler):
  def help_command(self, message=None):
    logging.info('Received message from: %s' % message.sender)
    message.reply('We all need a little help sometimes')

  def track_command(self, message=None):
    logging.info('Received message from: %s' % message.sender)

    tracker = Tracker()
    if (tracker.track(message.sender, message.body)):
      message.reply('Tracking: %s' % tracker.extract_search_term(message.body))
    else:
      message.reply('Sorry there was a problem with your last track command <%s>' % message.body)