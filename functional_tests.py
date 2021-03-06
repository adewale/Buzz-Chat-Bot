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

import main
import os
import unittest

from gaetestbed import FunctionalTestCase
from stubs import StubMessage, StubSimpleBuzzWrapper
from tracker_tests import StubHubSubscriber
from xmpp import Tracker, XmppHandler, extract_sender_email_address

import oauth_handlers
import settings
  
class FrontPageHandlerFunctionalTest(FunctionalTestCase, unittest.TestCase):
  APPLICATION = main.application
  def test_front_page_can_be_viewed_without_being_logged_in(self):
    response = self.get(settings.FRONT_PAGE_HANDLER_URL)

    self.assertOK(response)
    response.mustcontain("<title>Buzz Chat Bot")
    response.mustcontain(settings.APP_NAME)

  def test_admin_profile_link_is_on_front_page(self):
    response = self.get(settings.FRONT_PAGE_HANDLER_URL)

    self.assertOK(response)
    response.mustcontain('href="%s"' % settings.ADMIN_PROFILE_URL)


class BuzzChatBotFunctionalTestCase(FunctionalTestCase, unittest.TestCase):
  def _setup_subscription(self, sender='foo@example.com',search_term='somestring'):
    search_term = search_term
    body = '%s %s' % (XmppHandler.TRACK_CMD,search_term)

    hub_subscriber = StubHubSubscriber()
    tracker = Tracker(hub_subscriber=hub_subscriber)
    subscription = tracker.track(sender, body)
    return subscription

class PostsHandlerTest(BuzzChatBotFunctionalTestCase):
  APPLICATION = main.application

  def test_can_validate_hub_challenge_for_subscribe(self):
    subscription = self._setup_subscription()
    challenge = 'somechallengetoken'
    topic = 'https://www.googleapis.com/buzz/v1/activities/track?q=somestring'

    response = self.get('/posts?hub.challenge=%s&hub.mode=%s&hub.topic=%s&id=%s' % (challenge, 'subscribe', topic, subscription.id()))

    self.assertOK(response)
    response.mustcontain(challenge)

  def test_can_validate_hub_challenge_for_unsubscribe(self):
    subscription = self._setup_subscription()
    subscription.delete()
    challenge = 'somechallengetoken'
    topic = 'https://www.googleapis.com/buzz/v1/activities/track?q=somestring'

    response = self.get('/posts?hub.challenge=%s&hub.mode=%s&hub.topic=%s&id=%s' % (challenge, 'unsubscribe', topic, subscription.id()))

    self.assertOK(response)
    response.mustcontain(challenge)


class StubXmppHandler(XmppHandler):
  def _make_wrapper(self, email_address):
    self.email_address = email_address
    return StubSimpleBuzzWrapper()

class XmppHandlerTest(BuzzChatBotFunctionalTestCase):
  def __init__(self, methodName='runTest'):
    BuzzChatBotFunctionalTestCase.__init__(self, methodName)

    self.stub_hub_subscriber = StubHubSubscriber()
    self.handler = StubXmppHandler(hub_subscriber=self.stub_hub_subscriber)

  def test_track_command_succeeds_for_varying_combinations_of_whitespace(self):
    arg = 'Some day my prints will come'
    message = StubMessage( body='%s  %s  ' % (XmppHandler.TRACK_CMD,arg))

    # We call the method directly here because we actually care about the object that is returned
    subscription = self.handler.track_command(message=message)

    self.assertEqual(message.message_to_send, XmppHandler.SUBSCRIPTION_SUCCESS_MSG % (message.arg,subscription.id()))
    
  def test_invalid_symbol_command_shows_correct_error(self):
    command = '~'
    message = StubMessage(body=command)

    self.handler.message_received(message)

    self.assertTrue(XmppHandler.UNKNOWN_COMMAND_MSG % command in message.message_to_send, message.message_to_send)

  def test_unhandled_command_shows_correct_error(self):
    command = 'wibble'
    message = StubMessage(body=command)

    self.handler.message_received(message)

    self.assertTrue(XmppHandler.UNKNOWN_COMMAND_MSG % command in message.message_to_send, message.message_to_send)
    
  def test_track_command_fails_for_missing_term(self):
    message = StubMessage(body='%s  ' % XmppHandler.TRACK_CMD)

    self.handler.message_received(message=message)

    self.assertTrue(XmppHandler.NOTHING_TO_TRACK_MSG in message.message_to_send, message.message_to_send)
    
  def test_untrack_command_fails_for_missing_subscription_value(self):
    message = StubMessage(body='%s 777' % XmppHandler.UNTRACK_CMD)

    self.handler.message_received(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send, message.message_to_send)

  def test_untrack_command_fails_for_missing_subscription_argument(self):
    self._setup_subscription()
    message = StubMessage(body='%s' % XmppHandler.UNTRACK_CMD)

    self.handler.message_received(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send, message.message_to_send)

  def test_untrack_command_fails_for_wrong_subscription_id(self):
    subscription = self._setup_subscription()
    id = subscription.id() + 1
    message = StubMessage(body='%s %s' % (XmppHandler.UNTRACK_CMD,id))

    self.handler.message_received(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send, message.message_to_send)

  def test_untrack_command_succeeds_for_valid_subscription_id(self):
    subscription = self._setup_subscription()
    id = subscription.id()
    message = StubMessage(body='%s %s' % (XmppHandler.UNTRACK_CMD, id))

    self.handler.message_received(message=message)

    self.assertTrue('No longer tracking' in message.message_to_send, message.message_to_send)

  def test_untrack_command_fails_for_other_peoples_valid_subscription_id(self):
    subscription = self._setup_subscription()
    id = subscription.id()
    message = StubMessage(sender='notfoo@example.com', body='%s %s' % (XmppHandler.UNTRACK_CMD,id))

    self.handler.message_received(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send, message.message_to_send)

  def test_untrack_command_fails_for_malformed_subscription_id(self):
    message = StubMessage(body='%s jaiku' % XmppHandler.UNTRACK_CMD)

    self.handler.message_received(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send, message.message_to_send)

  def test_untrack_command_fails_for_empty_subscription_id(self):
    message = StubMessage(body='%s' % XmppHandler.UNTRACK_CMD)

    self.handler.message_received(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send, message.message_to_send)

  def test_list_command_lists_existing_search_terms_and_ids_for_each_user(self):
    sender1 = '1@example.com'
    subscription1 = self._setup_subscription(sender=sender1, search_term='searchA')
    sender2 = '2@example.com'
    subscription2 = self._setup_subscription(sender=sender2, search_term='searchB')

    for people in [(sender1, subscription1), (sender2, subscription2)]:
      sender = people[0]
      message = StubMessage(sender=sender, body='%s' % XmppHandler.LIST_CMD)

      self.handler.message_received(message=message)

      subscription = people[1]
      self.assertTrue(str(subscription.id()) in message.message_to_send)
      expected_item = 'Search term: %s with id: %s' % (subscription.search_term, subscription.id())
      self.assertTrue(expected_item in message.message_to_send, message.message_to_send)

  def test_list_command_can_show_exactly_one_subscription(self):
    sender = '1@example.com'
    subscription = self._setup_subscription(sender=sender, search_term='searchA')
    message = StubMessage(sender=sender, body='%s' % XmppHandler.LIST_CMD)

    self.handler.message_received(message=message)

    expected_item = 'Search term: %s with id: %s' % (subscription.search_term, subscription.id())
    self.assertEquals(expected_item, message.message_to_send)

  def test_list_command_can_handle_empty_set_of_search_terms(self):
    sender = '1@example.com'
    message = StubMessage(sender=sender, body='%s' % XmppHandler.LIST_CMD)

    self.handler.message_received(message=message)

    expected_item = XmppHandler.LIST_NOT_TRACKING_ANYTHING_MSG
    self.assertTrue(len(message.message_to_send) > 0)
    self.assertTrue(expected_item in message.message_to_send, message.message_to_send)

  def test_about_command_says_what_bot_is_running(self):
    sender = '1@example.com'
    message = StubMessage(sender=sender, body='%s'  % XmppHandler.ABOUT_CMD)

    self.handler.message_received(message=message)

    expected_item = 'Welcome to %s@appspot.com. A bot for Google Buzz' % settings.APP_NAME
    self.assertTrue(expected_item in message.message_to_send, message.message_to_send)

  def test_post_command_warns_users_with_no_oauth_token(self):
    sender = '1@example.com'
    message = StubMessage(sender=sender, body='%s some message' % XmppHandler.POST_CMD)

    self.handler.message_received(message=message)

    expected_item = 'You (%s) have not given access to your Google Buzz account. Please do so at: %s' % (sender, settings.APP_URL)
    self.assertTrue(expected_item in message.message_to_send, message.message_to_send)

  def test_post_command_warns_users_with_no_access_token(self):
    sender = '1@example.com'

    user_token = oauth_handlers.UserToken(email_address=sender)
    user_token.put()
    message = StubMessage(sender=sender, body='%s some message'  % XmppHandler.POST_CMD)

    self.handler.message_received(message=message)

    expected_item = 'You (%s) did not complete the process for giving access to your Google Buzz account. Please do so at: %s' % (sender, settings.APP_URL)
    self.assertEquals(expected_item, message.message_to_send)
    self.assertEquals(None, oauth_handlers.UserToken.find_by_email_address(sender))

  def test_post_command_posts_message_for_user_with_oauth_token(self):
    sender = '1@example.com'
    user_token = oauth_handlers.UserToken(email_address=sender)
    user_token.access_token_string = 'some thing that looks like an access token from a distance'
    user_token.put()
    message = StubMessage(sender=sender, body='%s some message' % XmppHandler.POST_CMD)

    self.handler.message_received(message=message)

    expected_item = 'Posted: %s' % self.handler.buzz_wrapper.url
    self.assertEquals(expected_item, message.message_to_send)

  def test_post_command_posts_message_for_correct_sender(self):
    # Using Adium format for message sender id
    sender = '1@example.com/Adium457EE950'
    email_address = extract_sender_email_address(sender)
    user_token = oauth_handlers.UserToken(email_address=email_address)
    user_token.access_token_string = 'some thing that looks like an access token from a distance'
    user_token.put()
    message = StubMessage(sender=sender, body='%s some message' % XmppHandler.POST_CMD)

    self.handler.message_received(message=message)

    self.assertEquals(email_address, self.handler.email_address)

  def test_post_command_posts_message_for_sender_ignoring_case(self):
    # Using Adium format for message sender id
    sender = 'UPPER@example.com/Adium457EE950'
    lower_email_address = extract_sender_email_address(sender).lower()
    user_token = oauth_handlers.UserToken(email_address=lower_email_address)
    user_token.access_token_string = 'some thing that looks like an access token from a distance'
    user_token.put()
    message = StubMessage(sender=sender, body='%s some message' % XmppHandler.POST_CMD)

    self.handler.message_received(message=message)

    self.assertEquals(lower_email_address, self.handler.email_address)
    expected_item = 'Posted: %s' % self.handler.buzz_wrapper.url
    self.assertEquals(expected_item, message.message_to_send)
    
  def test_post_command_posts_message_for_sender_with_mixed_case_oauth_token(self):
      # Using Adium format for message sender id
      sender = 'upper@example.com/Adium457EE950'
      email_address = extract_sender_email_address(sender)
      mixed_email_address = 'uPPeR@example.com'
      
      # Note that the test simulates the OAuth dance here.
      # The other tests don't need an environment that's this realistic
      os.environ['USER_EMAIL']  = mixed_email_address
      user_token = oauth_handlers.UserToken.create_user_token('something that looks like a request token')
      user_token.put()
      #user_token = oauth_handlers.UserToken(email_address=mixed_email_address)
      access_token_string = 'some thing that looks like an access token from a distance'
      user_token.set_access_token(access_token_string)
      user_token.put()
      message = StubMessage(sender=sender, body='%s some message' % XmppHandler.POST_CMD)

      self.handler.message_received(message=message)

      expected_item = 'Posted: %s' % self.handler.buzz_wrapper.url
      self.assertEquals(expected_item, message.message_to_send)

  def test_post_command_strips_command_from_posted_message(self):
    sender = '1@example.com'
    user_token = oauth_handlers.UserToken(email_address=sender)
    user_token.access_token_string = 'some thing that looks like an access token from a distance'
    user_token.put()
    message = StubMessage(sender=sender, body='%s     some message' % XmppHandler.POST_CMD)

    self.handler.message_received(message=message)

    expected_item = 'some message'
    self.assertEquals(expected_item, self.handler.buzz_wrapper.message)
    
  def test_slash_post_command_strips_command_from_posted_message(self):
    sender = '1@example.com'
    user_token = oauth_handlers.UserToken(email_address=sender)
    user_token.access_token_string = 'some thing that looks like an access token from a distance'
    user_token.put()
    message = StubMessage(sender=sender, body='/%s some message' % XmppHandler.POST_CMD)

    self.handler.message_received(message=message)

    expected_item = 'some message'
    self.assertEquals(expected_item, self.handler.buzz_wrapper.message)

  def test_slash_post_gets_treated_as_post_command(self):
    sender = '1@example.com'
    user_token = oauth_handlers.UserToken(email_address=sender)
    user_token.access_token_string = 'some thing that looks like an access token from a distance'
    user_token.put()
    message = StubMessage(sender=sender, body='/%s some message' % XmppHandler.POST_CMD)

    self.handler.message_received(message=message)

    expected_item = 'Posted: %s' % self.handler.buzz_wrapper.url
    self.assertEquals(expected_item, message.message_to_send)

  def test_uppercase_post_gets_treated_as_post_command(self):
    sender = '1@example.com'
    user_token = oauth_handlers.UserToken(email_address=sender)
    user_token.access_token_string = 'some thing that looks like an access token from a distance'
    user_token.put()
    message = StubMessage(sender=sender, body='%s some message' % XmppHandler.POST_CMD.upper())

    self.handler.message_received(message=message)

    expected_item = 'Posted: %s' % self.handler.buzz_wrapper.url
    self.assertEquals(expected_item, message.message_to_send)

  def test_slash_uppercase_post_gets_treated_as_post_command(self):
    sender = '1@example.com'
    user_token = oauth_handlers.UserToken(email_address=sender)
    user_token.access_token_string = 'some thing that looks like an access token from a distance'
    user_token.put()
    message = StubMessage(sender=sender, body='/%s some message' % XmppHandler.POST_CMD.upper())

    self.handler.message_received(message=message)

    expected_item = 'Posted: %s' % self.handler.buzz_wrapper.url
    self.assertEquals(expected_item, message.message_to_send)

  def test_help_command_lists_available_commands(self):
    sender = '1@example.com'
    message = StubMessage(sender=sender, body='%s' % XmppHandler.HELP_CMD)

    self.handler.message_received(message=message)

    self.assertTrue(len(message.message_to_send) > 0)
    for command in XmppHandler.COMMAND_HELP_MSG_LIST:
      self.assertTrue(command in message.message_to_send, message.message_to_send)

  def test_alternative_help_command_lists_available_commands(self):
    sender = '1@example.com'
    message = StubMessage(sender=sender, body='%s' % XmppHandler.ALTERNATIVE_HELP_CMD)

    self.handler.message_received(message=message)

    self.assertTrue(XmppHandler.UNKNOWN_COMMAND_MSG % XmppHandler.ALTERNATIVE_HELP_CMD not in message.message_to_send)
    self.assertTrue(len(message.message_to_send) > 0)
    for command in XmppHandler.COMMAND_HELP_MSG_LIST:
      self.assertTrue(command in message.message_to_send, message.message_to_send)

  def test_search_command_succeeds_for_single_token(self):
    arg = 'onewordsearchterm'
    message = StubMessage(body='%s  %s  ' % (XmppHandler.SEARCH_CMD,arg))

    self.handler.message_received(message=message)

    self.assertTrue(len(message.message_to_send) > 0, message)

class XmppHandlerHttpTest(FunctionalTestCase, unittest.TestCase):
  APPLICATION = main.application
  
  def test_help_command_can_be_triggered_via_http(self):
    # Help command was chosen as it's idempotent and has no side-effects
    data = {'from' : settings.APP_NAME + '@appspot.com',
            'to' : settings.APP_NAME + '@appspot.com',
            'body' : 'help'}

    response = self.post('/_ah/xmpp/message/chat/', data=data)

    self.assertOK(response)

  def test_list_command_can_be_triggered_via_http(self):
    # List command was chosen as it's idempotent and has no side-effects
    data = {'from' : settings.APP_NAME + '@appspot.com',
            'to' : settings.APP_NAME + '@appspot.com',
            'body' : 'list'}

    response = self.post('/_ah/xmpp/message/chat/', data=data)

    self.assertOK(response)

  def test_search_command_can_be_triggered_via_http(self):
    data = {'from' : settings.APP_NAME + '@appspot.com',
            'to' : settings.APP_NAME + '@appspot.com',
            'body' : 'search somesearchterm'}

    response = self.post('/_ah/xmpp/message/chat/', data=data)

    self.assertOK(response)

  def test_invalid_http_request_triggers_error(self):
    response = self.post('/_ah/xmpp/message/chat/', data={}, expect_errors=True)

    self.assertEquals('400 Bad Request', response.status)
