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

import unittest
from xmpp import Tracker

class TrackerTest(unittest.TestCase):
  def test_tracker_rejects_empty_search_term(self):
    sender = 'foo@example.com'
    body = '/track'
    tracker = Tracker()
    self.assertFalse(tracker.track(sender, body))

  def test_tracker_rejects_padded_empty_string(self):
    sender = 'foo@example.com'
    body = '/track     '
    tracker = Tracker()
    self.assertFalse(tracker.track(sender, body))

  def test_tracker_accepts_valid_string(self):
    sender = 'foo@example.com'
    body = '/track somestring'
    tracker = Tracker()
    self.assertTrue(tracker.track(sender, body))

  def test_tracker_builds_correct_pshb_url(self):
    search_term = 'somestring'
    body = '/track %s' % search_term
    tracker = Tracker()
    self.assertEquals('https://www.googleapis.com/buzz/v1/activities/track?q=%s' % search_term, tracker._build_url(body))

  def test_tracker_url_encodes_search_term(self):
    search_term = 'some string'
    body = '/track %s' % search_term
    tracker = Tracker()
    self.assertEquals('https://www.googleapis.com/buzz/v1/activities/track?q=' + 'some%20string', tracker._build_url(body))