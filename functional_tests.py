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
import unittest

from gaetestbed import FunctionalTestCase
from tracker_tests import StubHubSubscriber
from xmpp import Tracker, XmppHandler
import logging

class BuzzChatBotFunctionalTestCase(FunctionalTestCase, unittest.TestCase):
  def _setup_subscription(self, sender='foo@example.com',search_term='somestring'):
    search_term = search_term
    body = '/track %s' % search_term

    hub_subscriber = StubHubSubscriber()
    tracker = Tracker(hub_subscriber=hub_subscriber)
    subscription = tracker.track(sender, body)
    return subscription

class PostsHandlerTest(BuzzChatBotFunctionalTestCase):
  APPLICATION = main.application

  def test_can_validate_hub_challenges(self):
    subscription = self._setup_subscription()
    challenge = 'somechallengetoken'
    topic = 'https://www.googleapis.com/buzz/v1/activities/track?q=somestring'
    response = self.get('/posts?hub.challenge=%s&hub.mode=%s&hub.topic=%s&id=%s' % (challenge, 'subscribe', topic, subscription.id()))
    self.assertOK(response)
    response.mustcontain(challenge)

class StubMessage(object):
  def __init__(self, sender='foo@example.com', body=''):
    self.sender = sender
    self.body = body

  def reply(self, message_to_send, raw_xml=False):
    self.message_to_send = message_to_send


class XmppHandlerTest(BuzzChatBotFunctionalTestCase):
  def test_untrack_command_fails_for_missing_subscription_value(self):
    message = StubMessage(body='/untrack 777')
    handler = XmppHandler()
    handler.untrack_command(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send)

  def test_untrack_command_fails_for_missing_subscription_argument(self):
    subscription = self._setup_subscription()
    message = StubMessage()
    handler = XmppHandler()
    handler.untrack_command(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send)

  def test_untrack_command_fails_for_wrong_subscription_id(self):
    subscription = self._setup_subscription()
    id = subscription.id() + 1
    message = StubMessage(body='/untrack %s' % id)
    handler = XmppHandler()
    handler.untrack_command(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send)

  def test_untrack_command_succeeds_for_valid_subscription_id(self):
    subscription = self._setup_subscription()
    id = subscription.id()
    message = StubMessage(body='/untrack %s' % id)
    handler = XmppHandler()
    handler.untrack_command(message=message)

    self.assertTrue('No longer tracking' in message.message_to_send)

  def test_untrack_command_fails_for_other_peoples_valid_subscription_id(self):
    subscription = self._setup_subscription()
    id = subscription.id()
    message = StubMessage(sender='notfoo@example.com', body='/untrack %s' % id)
    handler = XmppHandler()
    handler.untrack_command(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send)

  def test_untrack_command_fails_for_malformed_subscription_id(self):
    message = StubMessage(body='/untrack jaiku')
    handler = XmppHandler()
    handler.untrack_command(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send)

  def test_untrack_command_fails_for_empty_subscription_id(self):
    message = StubMessage(body='/untrack')
    handler = XmppHandler()
    handler.untrack_command(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send)

  def test_list_command_lists_existing_search_terms_and_ids_for_each_user(self):
    sender1 = '1@example.com'
    subscription1 = self._setup_subscription(sender=sender1, search_term='searchA')
    sender2 = '2@example.com'
    subscription2 = self._setup_subscription(sender=sender2, search_term='searchB')

    handler = XmppHandler()
    for people in [(sender1, subscription1), (sender2, subscription2)]:
      sender = people[0]
      message = StubMessage(sender=sender, body='/list')
      handler.list_command(message=message)
      subscription = people[1]
      self.assertTrue(str(subscription.id()) in message.message_to_send)

      expected_item = 'Search term: %s with id: %s' % (subscription.search_term, subscription.id())
      self.assertTrue(expected_item in message.message_to_send, expected_item)