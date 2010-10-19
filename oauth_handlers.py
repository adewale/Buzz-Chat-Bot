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

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import users
from google.appengine.api import xmpp

import buzz_gae_client
import logging
import os
import settings

class UserToken(db.Model):
# The user_id is the key_name so we don't have to make it an explicit property
  request_token_string = db.StringProperty()
  access_token_string = db.StringProperty()
  email_address = db.StringProperty()

  def get_request_token(self):
    "Returns request token as a dictionary of tokens including oauth_token, oauth_token_secret and oauth_callback_confirmed."
    return eval(self.request_token_string)

  def set_access_token(self, access_token):
    access_token_string = repr(access_token)
    self.access_token_string = access_token_string

  def get_access_token(self):
    "Returns access token as a dictionary of tokens including consumer_key, consumer_secret, oauth_token and oauth_token_secret"
    return eval(self.access_token_string)

  @staticmethod
  def create_user_token(request_token):
    user = users.get_current_user()
    user_id = user.user_id()
    request_token_string = repr(request_token)

    # TODO(ade) Support users who sign in to AppEngine with a federated identity aka OpenId
    email = user.email()

    logging.info('Creating user token: key_name: %s request_token_string: %s email_address: %s' % (
    user_id, request_token_string, email))

    return UserToken(key_name=user_id, request_token_string=request_token_string, access_token_string='',
                     email_address=email)

  @staticmethod
  def get_current_user_token():
    user = users.get_current_user()
    user_token = UserToken.get_by_key_name(user.user_id())
    return user_token

  @staticmethod
  def access_token_exists():
    user = users.get_current_user()
    user_token = UserToken.get_by_key_name(user.user_id())
    logging.info('user_token: %s' % user_token)
    return user_token and user_token.access_token_string

  @staticmethod
  def find_by_email_address(email_address):
    user_tokens = UserToken.gql('WHERE email_address = :1', email_address).fetch(1)
    if user_tokens:
      return user_tokens[0] # The result of the query is a list
    else:
      return None

class DanceStartingHandler(webapp.RequestHandler):
  @login_required
  def get(self):
    logging.info('Request body %s' % self.request.body)
    user = users.get_current_user()
    logging.debug('Started OAuth dance for: %s' % user.email())

    template_values = {"jabber_id": ("%s@appspot.com" % settings.APP_NAME)}
    if UserToken.access_token_exists():
      template_values['access_token_exists'] = 'true'
    else:
    # Generate the request token
      client = buzz_gae_client.BuzzGaeClient(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
      request_token = client.get_request_token(settings.CALLBACK_URL)

      # Create the request token and associate it with the current user
      user_token = UserToken.create_user_token(request_token)
      UserToken.put(user_token)

      authorisation_url = client.generate_authorisation_url(request_token)
      logging.info('Authorisation URL is: %s' % authorisation_url)
      template_values['destination'] = authorisation_url

    path = os.path.join(os.path.dirname(__file__), 'start_dance.html')
    self.response.out.write(template.render(path, template_values))


class TokenDeletionHandler(webapp.RequestHandler):
  def post(self):
    user_token = UserToken.get_current_user_token()
    UserToken.delete(user_token)
    self.redirect(settings.FRONT_PAGE_HANDLER_URL)


class DanceFinishingHandler(webapp.RequestHandler):
  def get(self):
    logging.info("Request body %s" % self.request.body)
    user = users.get_current_user()
    logging.debug('Finished OAuth dance for: %s' % user.email())

    oauth_verifier = self.request.get('oauth_verifier')
    client = buzz_gae_client.BuzzGaeClient(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    user_token = UserToken.get_current_user_token()
    request_token = user_token.get_request_token()
    access_token = client.upgrade_to_access_token(request_token, oauth_verifier)
    logging.info('SUCCESS: Received access token.')

    user_token.set_access_token(access_token)
    UserToken.put(user_token)
    logging.debug('Access token was: %s' % user_token.access_token_string)

    # Send an XMPP invitation
    logging.info('Sending invite to %s' % user_token.email_address)
    xmpp.send_invite(user_token.email_address)
    msg = 'Welcome to the BuzzChatBot: %s' % settings.APP_URL
    xmpp.send_message(user_token.email_address, msg)

    self.redirect(settings.PROFILE_HANDLER_URL)