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
from xmpp import SlashlessCommandMessage, XmppHandler


class SlashlessCommandMessageTest(unittest.TestCase):
  def test_extracts_symbol_as_command_given_symbol(self):
    self.assertEquals('?', SlashlessCommandMessage.extract_command_and_arg_from_string('?')[0])

  def test_extracts_all_commands(self):
    for command in XmppHandler.PERMITTED_COMMANDS:
      self.assertEquals(command, SlashlessCommandMessage.extract_command_and_arg_from_string(command)[0])