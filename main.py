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

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
from google.appengine.ext.webapp.util import run_wsgi_app

import logging
import oauth_handlers
import os
import settings
import xmpp
import pshb
import simple_buzz_wrapper

class ProfileViewingHandler(webapp.RequestHandler):
  @login_required
  def get(self):
    user_token = oauth_handlers.UserToken.get_current_user_token()
    buzz_wrapper = simple_buzz_wrapper.SimpleBuzzWrapper(user_token)
    user_profile_data = buzz_wrapper.get_profile()

    template_values = {'user_profile_data': user_profile_data, 'access_token': user_token.access_token_string}
    path = os.path.join(os.path.dirname(__file__), 'profile.html')
    self.response.out.write(template.render(path, template_values))


class FrontPageHandler(webapp.RequestHandler):
  def get(self):
    template_values = {'commands' : xmpp.XmppHandler.commands,
                       'help_command' : xmpp.XmppHandler.HELP_CMD,
                       'jabber_id' : '%s@appspot.com' % settings.APP_NAME,
                       'admin_url' : settings.ADMIN_PROFILE_URL}
    path = os.path.join(os.path.dirname(__file__), 'front_page.html')
    self.response.out.write(template.render(path, template_values))

class PostsHandler(webapp.RequestHandler):
  def _get_subscription(self):
    logging.info("Headers were: %s" % str(self.request.headers))
    logging.info('Request: %s' % str(self.request))
    id = self.request.get('id')
    subscription = xmpp.Subscription.get_by_id(int(id))
    return subscription

  def get(self):
    """Show all the resources in this collection"""
    logging.info("Headers were: %s" % str(self.request.headers))
    logging.info('Request: %s' % str(self.request))
    logging.debug("New content: %s" % self.request.body)
    id = self.request.get('id')

    # If this is a hub challenge
    if self.request.get('hub.challenge'):
    # If this subscription exists
      mode = self.request.get('hub.mode')
      topic = self.request.get('hub.topic')
      if mode == "subscribe" and xmpp.Subscription.get_by_id(int(id)):
        self.response.out.write(self.request.get('hub.challenge'))
        logging.info("Successfully accepted %s challenge for feed: %s" % (mode, topic))
      elif mode == "unsubscribe" and not xmpp.Subscription.get_by_id(int(id)):
        self.response.out.write(self.request.get('hub.challenge'))
        logging.info("Successfully accepted %s challenge for feed: %s" % (mode, topic))
      else:
        self.response.set_status(404)
        self.response.out.write("Challenge failed")
        logging.info("Challenge failed for feed: %s" % topic)
      # Once a challenge has been issued there's no point in returning anything other than challenge passed or failed
      return

  def post(self):
    """Create a new resource in this collection"""
    logging.info("Headers were: %s" % str(self.request.headers))
    logging.info('Request: %s' % str(self.request))
    logging.debug("New content: %s" % self.request.body)
    id = self.request.get('id')

    subscription = xmpp.Subscription.get_by_id(int(id))
    if not subscription:
      self.response.set_status(404)
      self.response.out.write("No such subscription")
      logging.warning('No subscription for %s' % id)
      return

    subscriber = subscription.subscriber
    search_term = subscription.search_term
    parser = pshb.ContentParser(self.request.body, settings.DEFAULT_HUB, settings.ALWAYS_USE_DEFAULT_HUB)
    url = parser.extractFeedUrl()

    if not parser.dataValid():
      parser.logErrors()
      self.response.out.write("Bad entries: %s" % parser.data)
      return
    else:
      posts = parser.extractPosts()
      logging.info("Successfully received %s posts for subscription: %s" % (len(posts), url))
      xmpp.send_posts(posts, subscriber, search_term)
      self.response.set_status(200)

application = webapp.WSGIApplication([
                                         (settings.FRONT_PAGE_HANDLER_URL, FrontPageHandler),
                                         (settings.PROFILE_HANDLER_URL, ProfileViewingHandler),
                                         ('/start_dance', oauth_handlers.DanceStartingHandler),
                                         ('/finish_dance', oauth_handlers.DanceFinishingHandler),
                                         ('/delete_tokens', oauth_handlers.TokenDeletionHandler),
                                         ('/posts', PostsHandler),
                                         ('/_ah/xmpp/message/chat/', xmpp.XmppHandler), ],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
