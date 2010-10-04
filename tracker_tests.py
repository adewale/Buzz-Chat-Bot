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
from xmpp import Subscription, Tracker, XmppHandler
import pshb
import settings

class StubHubSubscriber(pshb.HubSubscriber):
  def subscribe(self, url, hub, callback_url):
    self.callback_url = callback_url

  def unsubscribe(self, url, hub, callback_url):
    self.callback_url = callback_url

class TrackerTest(unittest.TestCase):
  def test_is_blank_works_on_blank_strings(self):
    self.assertTrue(Tracker.is_blank(" "))
    self.assertTrue(Tracker.is_blank("    ")) # has a tab in it
    self.assertTrue(Tracker.is_blank(""))
    
  def test_is_blank_works_on_nonblank_strings(self):
    self.assertFalse(Tracker.is_blank("  a"))
    self.assertFalse(Tracker.is_blank("adf    "))
    self.assertFalse(Tracker.is_blank("  adfas    "))
    self.assertFalse(Tracker.is_blank("daf-sa"))
    
  def test_tracker_rejects_empty_search_term(self):
    sender = 'foo@example.com'
    body = XmppHandler.TRACK_CMD
    tracker = Tracker()
    self.assertEquals(None, tracker.track(sender, body))

  def test_tracker_rejects_padded_empty_string(self):
    sender = 'foo@example.com'
    body = '%s     ' % XmppHandler.TRACK_CMD
    tracker = Tracker()
    self.assertEquals(None, tracker.track(sender, body))

  def test_tracker_accepts_valid_string(self):
    sender = 'foo@example.com'
    search_term='somestring'
    body = '%s %s' % (XmppHandler.TRACK_CMD, search_term)
    hub_subscriber = StubHubSubscriber()
    tracker = Tracker(hub_subscriber=hub_subscriber)
    expected_callback_url = 'http://%s.appspot.com/posts/%s/%s' % (settings.APP_NAME, sender, search_term)
    expected_subscription = Subscription(url='https://www.googleapis.com/buzz/v1/activities/track?q=%s' % search_term, search_term=search_term, callback_url=expected_callback_url)
    actual_subscription = tracker.track(sender, body)
    self.assertEquals(expected_subscription.url, actual_subscription.url)
    self.assertEquals(expected_subscription.search_term, actual_subscription.search_term)

  def test_tracker_extracts_correct_search_term(self):
    search_term = 'somestring'
    body = '%s %s' % (XmppHandler.TRACK_CMD, search_term)
    tracker = Tracker()
    self.assertEquals(search_term, tracker._extract_search_term(body))

  def test_tracker_builds_correct_pshb_url(self):
    search_term = 'somestring'
    tracker = Tracker()
    self.assertEquals('https://www.googleapis.com/buzz/v1/activities/track?q=%s' % search_term, tracker._build_subscription_url(search_term))

  def test_tracker_url_encodes_search_term(self):
    search_term = 'some string'
    tracker = Tracker()
    self.assertEquals('https://www.googleapis.com/buzz/v1/activities/track?q=' + 'some%20string', tracker._build_subscription_url(search_term))

  def _delete_all_subscriptions(self):
    for subscription in Subscription.all().fetch(100):
      subscription.delete()

  def test_tracker_saves_subscription(self):
    self._delete_all_subscriptions()

    self.assertEquals(0, len(Subscription.all().fetch(100)))
    sender = 'foo@example.com'
    search_term='somestring'
    body = '%s %s' % (XmppHandler.TRACK_CMD,search_term)

    tracker = Tracker()
    subscription = tracker.track(sender, body)
    self.assertEquals(1, len(Subscription.all().fetch(100)))
    self.assertEquals(subscription, Subscription.all().fetch(1)[0])

  def test_tracker_subscribes_with_callback_url_that_identifies_subscriber_and_query(self):
    sender = 'foo@example.com'
    search_term='somestring'
    body = '%s %s' % (XmppHandler.TRACK_CMD,search_term)

    hub_subscriber = StubHubSubscriber()
    tracker = Tracker(hub_subscriber=hub_subscriber)
    subscription = tracker.track(sender, body)

    expected_callback_url = 'http://%s.appspot.com/posts?id=%s' % (settings.APP_NAME, subscription.id())
    self.assertEquals(expected_callback_url, hub_subscriber.callback_url)

  def test_tracker_subscribes_with_urlencoded_callback_url(self):
    sender = 'foo@example.com'
    search_term='some string'
    body = '%s %s' % (XmppHandler.TRACK_CMD,search_term)

    hub_subscriber = StubHubSubscriber()
    tracker = Tracker(hub_subscriber=hub_subscriber)
    subscription = tracker.track(sender, body)

    expected_callback_url = 'http://%s.appspot.com/posts?id=%s' % (settings.APP_NAME, subscription.id())
    self.assertEquals(expected_callback_url, hub_subscriber.callback_url)

  def test_tracker_subscribes_with_callback_url_that_identifies_subscriber_and_query_without_xmpp_client_identifier(self):
    sender = 'foo@example.com/Adium380DADCD'
    search_term='somestring'
    body = '%s %s' % (XmppHandler.TRACK_CMD,search_term)

    hub_subscriber = StubHubSubscriber()
    tracker = Tracker(hub_subscriber=hub_subscriber)
    subscription = tracker.track(sender, body)

    expected_callback_url = 'http://%s.appspot.com/posts?id=%s' % (settings.APP_NAME, subscription.id())
    self.assertEquals(expected_callback_url, hub_subscriber.callback_url)

  def test_tracker_rejects_invalid_id_for_untracking(self):
    self._delete_all_subscriptions()
    sender = 'foo@example.com/Adium380DADCD'
    body = '%s 1' % XmppHandler.UNTRACK_CMD

    hub_subscriber = StubHubSubscriber()
    tracker = Tracker(hub_subscriber=hub_subscriber)
    subscription = tracker.untrack(sender, body)
    self.assertEquals(None, subscription)

  def test_tracker_untracks_valid_id(self):
    self._delete_all_subscriptions()

    sender = 'foo@example.com/Adium380DADCD'
    search_term='somestring'
    body = '%s %s' % (XmppHandler.TRACK_CMD,search_term)

    hub_subscriber = StubHubSubscriber()
    tracker = Tracker(hub_subscriber=hub_subscriber)
    track_subscription = tracker.track(sender, body)

    body = '%s %s' % (XmppHandler.UNTRACK_CMD,track_subscription.id())
    untrack_subscription = tracker.untrack(sender, body)
    self.assertEquals(track_subscription, untrack_subscription)
    self.assertFalse(Subscription.exists(track_subscription.id()))
    self.assertEquals('http://%s.appspot.com/posts?id=%s' % (settings.APP_NAME, track_subscription.id()), hub_subscriber.callback_url)
