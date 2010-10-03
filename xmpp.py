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

from google.appengine.api import xmpp
from google.appengine.ext import db
from google.appengine.ext.webapp import xmpp_handlers

import logging
import urllib
import oauth_handlers
import pshb
import settings
import simple_buzz_wrapper

class Subscription(db.Model):
  url = db.StringProperty(required=True)
  search_term = db.StringProperty(required=True)
  subscriber = db.StringProperty()

  def id(self):
    return self.key().id()

  def __eq__(self, other):
    if not other:
      return False
    return self.id() == other.id()

  @staticmethod
  def exists(id):
    """Return True or False to indicate if a subscription with the given id exists"""
    if not id:
      return False
    return Subscription.get_by_id(int(id)) is not None


class Tracker(object):
  def __init__(self, hub_subscriber=pshb.HubSubscriber()):
    self.hub_subscriber =  hub_subscriber

  def _valid_subscription(self, message_body):
    return self._extract_search_term(message_body) != ''

  def _extract_search_term(self, message_body):
    search_term = message_body[len('/track'):]
    return search_term.strip()

  def _subscribe(self, message_sender, message_body):
    message_sender = extract_sender_email_address(message_sender)
    search_term = self._extract_search_term(message_body)
    url = self._build_subscription_url(search_term)
    logging.info('Subscribing to: %s for user: %s' % (url, message_sender))

    subscription = Subscription(url=url, search_term=search_term, subscriber=message_sender)
    db.put(subscription)

    callback_url = self._build_callback_url(subscription)

    logging.info('Callback URL was: %s' % callback_url)
    self.hub_subscriber.subscribe(url, 'http://pubsubhubbub.appspot.com/', callback_url)

    return subscription

  def _build_callback_url(self, subscription):
    return "http://%s.appspot.com/posts?id=%s" % (settings.APP_NAME, subscription.id())

  def _build_subscription_url(self, search_term):
    search_term = urllib.quote(search_term)
    return 'https://www.googleapis.com/buzz/v1/activities/track?q=%s' % search_term

  def track(self, message_sender, message_body):
    if self._valid_subscription(message_body):
      return self._subscribe(message_sender, message_body)
    else:
      return None

  def _is_number(self, id):
    if not id:
      return False
    id = id.strip()
    for char in id:
      if not char.isdigit():
        return False
    return True

  def untrack(self, message_sender, message_body):
    logging.info('Message is: %s' % message_body)
    id = message_body[len('/untrack'):]
    if not self._is_number(id):
      return None

    id = id.strip()
    subscription = Subscription.get_by_id(int(id))
    logging.info('Subscripton: %s' % str(subscription))
    if not subscription:
      return None

    if subscription.subscriber != extract_sender_email_address(message_sender):
      return None
    subscription.delete()

    callback_url = self._build_callback_url(subscription)
    logging.info('Callback URL was: %s' % callback_url)
    self.hub_subscriber.unsubscribe(subscription.url, 'http://pubsubhubbub.appspot.com/', callback_url)
    return subscription


class MessageBuilder(object):
  def __init__(self):
    self.lines = []

  def build_message(self):
    text = ''
    for index,line in enumerate(self.lines):
      text += line
      if (index+1) < len(self.lines):
        text += '\n'
    return text

  def add(self, line):
    self.lines.append(line)

  def build_message_from_post(self, post, search_term):
    return '''[%s] matched post: [%s] with URL: [%s]''' % (search_term, post.title, post.url)



class XmppHandler(xmpp_handlers.CommandHandler):
  HELP_CMD    = '/help'
  TRACK_CMD   = '/track'
  UNTRACK_CMD = '/untrack'
  LIST_CMD    = '/list'
  ABOUT_CMD   = '/about'
  POST_CMD    = '/post'

  commands = [
        '%s Prints out this message' % HELP_CMD,
        '%s [search term] Starts tracking the given search term and returns the id for your subscription' % TRACK_CMD,
        '%s [id] Removes your subscription for that id' % UNTRACK_CMD,
        '%s Lists all search terms and ids currently being tracked by you' % LIST_CMD,
        '%s Tells you which instance of the Buzz Chat Bot you are using' % ABOUT_CMD,
        '%s [some message] Posts that message to Buzz' % POST_CMD
  ]

  
  def __init__(self, buzz_wrapper=simple_buzz_wrapper.SimpleBuzzWrapper()):
    self.buzz_wrapper = buzz_wrapper

  def handle_exception(self, exception, debug_mode):
    super(xmpp_handlers.CommandHandler, self).handle_exception(exception, debug_mode)
    if self.xmpp_message:
      self.xmpp_message.reply('Oops. Something went wrong.')
      logging.error('User visible oops for message: %s' % str(self.xmpp_message.body))

  def help_command(self, message=None):
    logging.info('Received message from: %s' % message.sender)

    lines = ['We all need a little help sometimes']
    lines.extend(self.commands)

    message_builder = MessageBuilder()
    for line in lines:
      message_builder.add(line)
    reply(message_builder, message)

  def track_command(self, message=None):
    logging.info('Received message from: %s' % message.sender)

    tracker = Tracker()
    subscription = tracker.track(message.sender, message.body)
    message_builder = MessageBuilder()
    if subscription:
      message_builder.add('Tracking: %s with id: %s' % (subscription.search_term, subscription.id()))
    else:
      message_builder.add('Sorry there was a problem with your last track command <%s>' % message.body)
    reply(message_builder, message)

  def untrack_command(self, message=None):
    logging.info('Received message from: %s' % message.sender)

    tracker = Tracker()
    subscription = tracker.untrack(message.sender, message.body)
    message_builder = MessageBuilder()
    if subscription:
      message_builder.add('No longer tracking: %s with id: %s' % (subscription.search_term, subscription.id()))
    else:
      message_builder.add('Untrack failed. That subscription does not exist for you. Remember the syntax is: /untrack [id]')
    reply(message_builder, message)

  def list_command(self, message=None):
    logging.info('Received message from: %s' % message.sender)
    message_builder = MessageBuilder()
    sender = extract_sender_email_address(message.sender)
    logging.info('Sender: %s' % sender)
    subscriptions_query = Subscription.gql('WHERE subscriber = :1', sender)
    if subscriptions_query.count() > 0:
      for subscription in subscriptions_query:
        message_builder.add('Search term: %s with id: %s' % (subscription.search_term, subscription.id()))
    else:
      message_builder.add('No subscriptions')
    reply(message_builder, message)

  def about_command(self, message):
    logging.info('Received message from: %s' % message.sender)
    message_builder = MessageBuilder()
    about_message = 'Welcome to %s@appspot.com. A bot for Google Buzz. Find out more at: http://%s.appspot.com' % (settings.APP_NAME, settings.APP_NAME)
    message_builder.add(about_message)
    reply(message_builder, message)

  def post_command(self, message):
    logging.info('Received message from: %s' % message.sender)
    message_builder = MessageBuilder()
    sender = extract_sender_email_address(message.sender)
    user_token = oauth_handlers.UserToken.find_by_email_address(sender)
    if not user_token:
      message_builder.add('You (%s) have not given access to your Google Buzz account. Please do so at: http://%s.appspot.com' % (sender, settings.APP_NAME))
    elif not user_token.access_token_string:
      # User didn't finish the OAuth dance so we make them start again
      user_token.delete()
      message_builder.add('You (%s) did not complete the process for giving access to your Google Buzz account. Please do so at: http://%s.appspot.com' % (sender, settings.APP_NAME))
    else:
      message_body = message.body[len('/post'):]
      url = self.buzz_wrapper.post(sender, message_body)
      message_builder.add('Posted: %s' % url)
    reply(message_builder, message)


def extract_sender_email_address(message_sender):
    return message_sender.split('/')[0]

def reply(message_builder, message):
  message_to_send = message_builder.build_message()
  logging.info('Message that will be sent: %s' % message_to_send)
  message.reply(message_to_send, raw_xml=False)

def send_posts(posts, subscriber, search_term):
  message_builder = MessageBuilder()
  for post in posts:
    xmpp.send_message(subscriber, message_builder.build_message_from_post(post, search_term), raw_xml=False)