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
import xml.etree.ElementTree

from xmpp import MessageBuilder

class MessageBuilderTest(unittest.TestCase):
  def assertValid(self, string):
    from xml.sax import make_parser, handler

    parser = make_parser()
    parser.setFeature(handler.feature_namespaces,True)
    parser.setContentHandler(handler.ContentHandler())

    import StringIO
    f = StringIO.StringIO(string)

    # This will raise an exception if the string is invalid
    parser.parse(f)
    
  def test_builds_valid_message_for_simple_string(self):
    text = 'Tracking: some complex search'
    message_builder = MessageBuilder()
    message_builder.add(text)
    message = message_builder.build_message()
    expected = '''<html xmlns='http://jabber.org/protocol/xhtml-im'>
    <body xmlns="http://www.w3.org/1999/xhtml">
    %s
    </body>
    </html>''' % text
    self.assertEquals(expected, message)
    self.assertValid(message)

  def test_builds_valid_message_for_track_message(self):
    # Note that this can easily become </track> if we use <> for messages
    text = '</track>'
    message_builder = MessageBuilder()
    message_builder.add(text)
    message = message_builder.build_message()
    expected = '''<html xmlns='http://jabber.org/protocol/xhtml-im'>
    <body xmlns="http://www.w3.org/1999/xhtml">
    %s
    </body>
    </html>''' % text
    #self.assertEquals(expected, message)
    self.assertValid(message)

  def test_builds_valid_message_for_list(self):
    items = ['1', '2', '3']
    message_builder = MessageBuilder()
    for item in items:
      message_builder.add(item)
    message = message_builder.build_message()
    expected = '''<html xmlns='http://jabber.org/protocol/xhtml-im'>
    <body xmlns="http://www.w3.org/1999/xhtml">
    1<br></br>2<br></br>3
    </body>
    </html>'''
    self.assertEquals(expected, message)
    self.assertValid(message)