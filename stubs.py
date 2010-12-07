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
from xmpp import SlashlessCommandMessage

import pshb
import simple_buzz_wrapper

class StubHubSubscriber(pshb.HubSubscriber):
  def subscribe(self, url, hub, callback_url):
    self.callback_url = callback_url

  def unsubscribe(self, url, hub, callback_url):
    self.callback_url = callback_url

class StubMessage(object):
  def __init__(self, sender='foo@example.com', body=''):
    self.sender = sender
    self.body = body
    self.command, self.arg = SlashlessCommandMessage.extract_command_and_arg_from_string(body)
    self.message_to_send = None

  def reply(self, message_to_send, raw_xml=False):
    self.message_to_send = message_to_send

class StubSimpleBuzzWrapper(simple_buzz_wrapper.SimpleBuzzWrapper):
  def __init__(self):
    self.url = 'some fake url'

  def post(self, sender, message_body):
    self.message = message_body
    return self.url

  def search(self, message):
	return [{'title':'Title1', 'links':{'alternate':[{'href':'http://www.example.com/1'}]}}, {'title': 'Title2', 'links':{'alternate':[{'href':'http://www.example.com/2'}]}}]