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
from xml.sax import make_parser, handler
from xmpp import MessageBuilder

import unittest
import pshb
import feedparser

class MessageBuilderTest(unittest.TestCase):
    
  def test_builds_valid_message_for_simple_string(self):
    text = 'Tracking: some complex search'
    message_builder = MessageBuilder()
    message_builder.add(text)
    message = message_builder.build_message()
    self.assertEquals(text, message)

  def test_builds_valid_message_for_track_message(self):
    message_builder = MessageBuilder()
    message_builder.add('</track>')
    message = message_builder.build_message()
    expected = '%s' % '</track>'
    self.assertEquals(expected, message)

  def test_builds_valid_message_for_list(self):
    items = ['1', '2', '3', '4']
    message_builder = MessageBuilder()
    for item in items:
      message_builder.add(item)
    message = message_builder.build_message()
    expected = '1\n2\n3\n4'
    self.assertEquals(expected, message)

  def test_builds_valid_message_for_post(self):
    search_term = 'some search'
    url = 'http://example.com/item1'
    feedUrl = 'http://example.com/feed'
    title = 'some title'
    content = 'some content'
    date_published = None
    author = 'some guy'
    entry = feedparser.FeedParserDict({'id':feedUrl})
    post = pshb.PostFactory.createPost(url, feedUrl, title, content, date_published, author, entry)
    message_builder = MessageBuilder()
    message = message_builder.build_message_from_post(post, search_term)
    expected = '[%s] matched post: [%s] with URL: [%s]' % (search_term, title, url)
    self.assertEquals(expected, message)