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
import buzz_gae_client
import settings
import oauth_handlers
import logging

class SimpleBuzzWrapper(object):
  "Simple client that exposes the bare minimum set of common Buzz operations"

  def __init__(self, user_token=None):
    if user_token:
      self.current_user_token = user_token
    self.builder = buzz_gae_client.BuzzGaeClient(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)

  def search(self, query, user_token=None, max_results=10):
    if query is None or query.strip() is '':
      return None
    api_client = self.builder.build_api_client()

    json = api_client.activities().search(q=query, max_results=max_results).execute()
    if json.has_key('items'):
      return json['items']
    return []

  def post(self, sender, message_body):
    if message_body is None or message_body.strip() is '':
      return None

    user_token = oauth_handlers.UserToken.find_by_email_address(sender)
    api_client = self.builder.build_api_client(user_token.get_access_token())

    #TODO(ade) What happens with users who have hidden their email address?
    # Switch to @me so it won't matter
    user_id = sender.split('@')[0]

    activities = api_client.activities()
    logging.info('Retrieved activities for: %s' % user_id)
    activity = activities.insert(userId=user_id, body={
      'data' : {
        'title': message_body,
        'object': {
          'content': message_body,
          'type': 'note'}
       }
    }
                                 ).execute()
    url = activity['links']['alternate'][0]['href']
    logging.info('Just created: %s' % url)
    return url

  def get_profile(self):
    api_client = self.builder.build_api_client(self.current_user_token.get_access_token())
    user_profile_data = api_client.people().get(userId='@me').execute()
    return user_profile_data

