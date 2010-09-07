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
from xmpp import Tracker

class PostsHandlerTest(FunctionalTestCase, unittest.TestCase):
  APPLICATION = main.application

  def test_can_validate_hub_challenges(self):
    sender = 'foo@example.com'
    search_term='somestring'
    body = '/track %s' % search_term

    challenge = 'somechallengetoken'
    hub_subscriber = StubHubSubscriber()
    tracker = Tracker(hub_subscriber=hub_subscriber)
    subscription = tracker.track(sender, body)

    topic = 'https://www.googleapis.com/buzz/v1/activities/track?q=somestring'
    response = self.get('/posts?hub.challenge=%s&hub.mode=%s&hub.topic=%s&id=%s' % (challenge, 'subscribe', topic, subscription.id()))
    self.assertOK(response)
    response.mustcontain(challenge)