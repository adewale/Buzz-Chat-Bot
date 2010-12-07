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

import simple_buzz_wrapper
import unittest

class SimpleBuzzWrapperTest(unittest.TestCase):
# None of the tests make a remote call. We assume the underlying libraries
# and servers are working.

  def test_wrapper_rejects_empty_post(self):
    wrapper = simple_buzz_wrapper.SimpleBuzzWrapper()
    self.assertEquals(None, wrapper.post('sender@example.org', ''))

  def test_wrapper_rejects_post_containing_only_whitespace(self):
    wrapper = simple_buzz_wrapper.SimpleBuzzWrapper()
    self.assertEquals(None, wrapper.post('sender@example.org', '            '))

  def test_wrapper_rejects_none_post(self):
    wrapper = simple_buzz_wrapper.SimpleBuzzWrapper()
    self.assertEquals(None, wrapper.post('sender@example.org', None))

  def test_wrapper_rejects_empty_search(self):
	wrapper = simple_buzz_wrapper.SimpleBuzzWrapper()
	self.assertEquals(None, wrapper.search(''))

  def test_wrapper_rejects_search_containing_only_whitespace(self):
	wrapper = simple_buzz_wrapper.SimpleBuzzWrapper()
	self.assertEquals(None, wrapper.search(' '))

  def test_wrapper_rejects_search_with_none(self):
	wrapper = simple_buzz_wrapper.SimpleBuzzWrapper()
	self.assertEquals(None, wrapper.search(None))