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

class BuzzChatBotFunctionalTestCase(FunctionalTestCase, unittest.TestCase):
  def _setup_subscription(self):
    sender = 'foo@example.com'
    search_term='somestring'
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
  def __init__(self):
    self.sender = 'foo@example.com'
    self.body = ''

  def reply(self, message_to_send, raw_xml=False):
    self.message_to_send = message_to_send


class XmppHandlerTest(BuzzChatBotFunctionalTestCase):
  def test_untrack_command_fails_for_missing_subscription_value(self):
    message = StubMessage()
    message.body = '/untrack 777'
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
    message = StubMessage()
    message.body = '/untrack %s' % id
    handler = XmppHandler()
    handler.untrack_command(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send)

  def test_untrack_command_succeeds_for_valid_subscription_id(self):
    subscription = self._setup_subscription()
    id = subscription.id()
    message = StubMessage()
    message.body = '/untrack %s' % id
    handler = XmppHandler()
    handler.untrack_command(message=message)

    self.assertTrue('No longer tracking' in message.message_to_send)

  def test_untrack_command_fails_for_other_peoples_valid_subscription_id(self):
    subscription = self._setup_subscription()
    id = subscription.id()
    message = StubMessage()
    message.sender = 'not' + message.sender
    message.body = '/untrack %s' % id
    handler = XmppHandler()
    handler.untrack_command(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send)

  def test_untrack_command_fails_for_malformed_subscription_id(self):
    message = StubMessage()
    message.body = '/untrack jaiku'
    handler = XmppHandler()
    handler.untrack_command(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send)

  def test_untrack_command_fails_for_empty_subscription_id(self):
    message = StubMessage()
    message.body = '/untrack'
    handler = XmppHandler()
    handler.untrack_command(message=message)

    self.assertTrue('Untrack failed' in message.message_to_send)