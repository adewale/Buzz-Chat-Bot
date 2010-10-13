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
from google.appengine.ext import webapp


import logging
import urllib
import oauth_handlers
import pshb
import settings
import simple_buzz_wrapper
import re

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

  @staticmethod
  def is_blank(string):
    """ utility function for determining whether a string is blank (just whitespace)
    """
    return (string is None) or (len(string) == 0) or string.isspace()

  @staticmethod
  def extract_number(id):
    """Convert an id to an integer and return None if the conversion fails."""
    if id is None:
      return None

    try:
      id = int(id)
    except ValueError, e:
      return None
    return id

  def _valid_subscription(self, search_term):
    return not Tracker.is_blank(search_term)

  def _subscribe(self, message_sender, search_term):
    message_sender = extract_sender_email_address(message_sender)
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

  def track(self, message_sender, search_term):
    if self._valid_subscription(search_term):
      return self._subscribe(message_sender, search_term)
    else:
      return None

  def untrack(self, message_sender, id):
    """ Given an id, untrack takes it and attempts to unsubscribe from the list of tracked items.
    TODO(julian): you should be able to untrack <term> directly.  """
    logging.info("Tracker.untrack: id is: '%s'" % id)
    id_as_int = Tracker.extract_number(id)
    if id_as_int == None:
      # TODO(ade) Do a subscription lookup by name here
      return None

    subscription = Subscription.get_by_id(id_as_int)
    if not subscription:
      return None
    logging.info('Subscripton: %s' % str(subscription))

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

class SlashlessCommandMessage(xmpp.Message):
  """ The default message format with GAE xmpp identifies the command as the first non whitespace word. 
  The argument is whatever occurs after that. 
  Design notes: it uses re for tokenization which is a step up
  from how Message works (that expects a single space character) 
  """
  def __init__(self, vars):
    xmpp.Message.__init__(self, vars)
    
    #TODO(julian) make arg and command protected. because __arg and __command are hidden as private
    #in xmpp.Message, we have to define our own separate instances of these variables
    #even though all we do is change the property accessors for them.
    # scm = slashless command message
    # luckily __arg and __command aren't used elsewhere in Message but
    # we can't guarantee this so it's a bit of a mess
    self.__scm_arg = None
    self.__scm_command = None
    self.__message_to_send = None
    # END TODO
  
  @staticmethod
  def extract_command_and_arg_from_string(string):
    # match any white space and then a word (cmd) 
    #  then any white space then everything after that (arg).
    command = None
    arg = None
     
    results = re.search(r"\s*(\S*\b)\s*(.*)", string) 
    if results != None:
      command = results.group(1)
      arg = results.group(2)
    
    # we didn't find a command and an arg so maybe we'll just find the command
    # some commands may not have args 
    else:
      results = re.search(r"\s*(\S*\b)\s*", string)
      if results != None:
        command = results.group(1)
        
    return (command,arg)
  
  
  def __ensure_command_and_args_extracted(self):
    """ Take the message and identify the command and argument if there is one.
    In the case of a SlashlessCommandMessage, there is always one -- the first word is the command.      
    """    
    # cache the values. 
    if self.__scm_command == None:
      self.__scm_command,self.__scm_arg = SlashlessCommandMessage.extract_command_and_arg_from_string(self.body)
      logging.info("command = '%s', arg = '%s'" %(self.__scm_command,self.__scm_arg))
    
  # These properties are redefined from that defined in xmpp.Message
  @property 
  def command(self):
    self.__ensure_command_and_args_extracted() 
    return self.__scm_command
  
  @property 
  def arg(self):
    self.__ensure_command_and_args_extracted() 
    return self.__scm_arg
  
  @property
  def message_to_send(self):
    """ TODO(julian) rename: this is actually response_message """ 
    return self.__message_to_send
  
  def reply(self, message_to_send, raw_xml=False):
    logging.debug( "SlashlessCommandMessage.reply: message_to_send = %s" % message_to_send)
    xmpp.Message.reply(self, message_to_send, raw_xml=raw_xml)
    self.__message_to_send = message_to_send

 
class XmppHandler(webapp.RequestHandler):
  ABOUT_CMD   = 'about'
  HELP_CMD    = 'help'
  LIST_CMD    = 'list'
  POST_CMD    = 'post'
  TRACK_CMD   = 'track'
  UNTRACK_CMD = 'untrack'
  
  PERMITTED_COMMANDS = [ABOUT_CMD,HELP_CMD,LIST_CMD,POST_CMD,TRACK_CMD,UNTRACK_CMD]

  COMMAND_HELP_MSG_LIST = [
    '%s Prints out this message' % HELP_CMD,
    '%s [search term] Starts tracking the given search term and returns the id for your subscription' % TRACK_CMD,
    '%s [id] Removes your subscription for that id' % UNTRACK_CMD,
    '%s Lists all search terms and ids currently being tracked by you' % LIST_CMD,
    '%s Tells you which instance of the Buzz Chat Bot you are using' % ABOUT_CMD,
    '%s [some message] Posts that message to Buzz' % POST_CMD
  ]
  
  TRACK_FAILED_MSG                = 'Sorry there was a problem with that track command '
  NOTHING_TO_TRACK_MSG            = "To track a phrase on buzz, you need to enter the phrase :) Please type: track <your phrase to track>" 
  UNKNOWN_COMMAND_MSG             = "Sorry, '%s' was not understood. Here are a list of the things you can do:"
  SUBSCRIPTION_SUCCESS_MSG        = 'Tracking: %s with id: %s'
  LIST_NOT_TRACKING_ANYTHING_MSG  = 'You are not tracking anything. To track when a word or phrase appears in Buzz, enter: track <thing of interest>'

  def __init__(self, buzz_wrapper=simple_buzz_wrapper.SimpleBuzzWrapper(), hub_subscriber=pshb.HubSubscriber()):
    self.buzz_wrapper = buzz_wrapper
    self.tracker = Tracker(hub_subscriber=hub_subscriber)
    
  def unhandled_command(self, message):
    """ User entered a command that is not recognised. Tell them this and show help""" 
    self.help_command(message, XmppHandler.UNKNOWN_COMMAND_MSG % message.command )
    
  def message_received(self, message):
    """ Take the message we've received and dispatch it to the appropriate command handler
    using introspection. E.g. if the command is 'track' it will map to track_command. 
    Args:
      message: Message: The message that was sent by the user.
    """
    if message.command and message.command in XmppHandler.PERMITTED_COMMANDS:
      handler_name = '%s_command' % (message.command,)
      handler = getattr(self, handler_name, None)
      if handler:
        handler(message)
        return
    self.unhandled_command(message)
      
  def post(self):
    """ Redefines post to create a message from our new SlashlessCommandMessage. 
    TODO(julian) xmpp_handlers: redefine the BaseHandler to have a function createMessage which can be 
    overridden this will avoid the code duplicated below
    """
    logging.info("Received chat msg, raw post =  '%s'" % self.request.POST)
    try:
      # CHANGE this is the only bit that has changed from xmpp_handlers.Message 
      self.xmpp_message = SlashlessCommandMessage(self.request.POST)
      # END CHANGE
    except xmpp.InvalidMessageError, e:
      logging.error("Invalid XMPP request: Missing required field %s", e[0])
      self.error(400)
      return
    self.message_received(self.xmpp_message)

  def handle_exception(self, exception, debug_mode):
    logging.error( "handle_exception: calling webapp.RequestHandler superclass")
    webapp.RequestHandler.handle_exception(self, exception, debug_mode)
    if self.xmpp_message:
      self.xmpp_message.reply("Oops. Something went wrong. Sorry about that")
      logging.error('User visible oops for message: %s' % str(self.xmpp_message.body))

  def help_command(self, message=None, prompt='We all need a little help sometimes' ):
    """ Print out the help command.
    Optionally accepts a message builder
    so help can be printed out if the user looks like they're having trouble """
    logging.info('Received message from: %s' % message.sender)

    lines = [prompt]
    lines.extend(self.COMMAND_HELP_MSG_LIST)
    message_builder = MessageBuilder()

    for line in lines:
      message_builder.add(line)
    reply(message_builder, message)

  def track_command(self, message=None):
    """ Start tracking a phrase against the Buzz API.
    message must be a valid
    xmpp.Message or subclass and cannot be null. """
    logging.debug('Received message from: %s' % message.sender)
    subscription = None
    
    message_builder = MessageBuilder()
    if message.arg == '':      
      message_builder.add( XmppHandler.NOTHING_TO_TRACK_MSG )
    else:
      logging.debug( "track_command: calling tracker.track with term '%s'" % message.arg )
      subscription = self.tracker.track(message.sender, message.arg)
      if subscription:
        message_builder.add( XmppHandler.SUBSCRIPTION_SUCCESS_MSG % (subscription.search_term, subscription.id()))
      else:
        message_builder.add('%s <%s>' % (XmppHandler.TRACK_FAILED_MSG, message.body))
        
    reply(message_builder, message)
    logging.debug( "message.message_to_send = '%s'" % message.message_to_send )
    return subscription

  def untrack_command(self, message=None):
    logging.info('Received message from: %s' % message.sender)

    subscription = self.tracker.untrack(message.sender, message.arg)
    message_builder = MessageBuilder()
    if subscription:
      message_builder.add('No longer tracking: %s with id: %s' % (subscription.search_term, subscription.id()))
    else:
      message_builder.add('Untrack failed. That subscription does not exist for you. Remember the syntax is: %s [id]' % XmppHandler.UNTRACK_CMD)
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
      message_builder.add(XmppHandler.LIST_NOT_TRACKING_ANYTHING_MSG)
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
      message_body = message.body[len(XmppHandler.POST_CMD):]
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