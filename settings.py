# These are the settings that tend to differ between installations. Tweak these for your installation.
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
APP_NAME = 'buzzchatbot'

#Note that the APP_URL must _not_ end in a slash as it will be concatenated with other values
APP_URL = 'http://%s.appspot.com' % APP_NAME
ADMIN_PROFILE_URL = 'http://profiles.google.com/adewale'

#PSHB settings
# This is the token that will act as a shared secret to verify that this application is the one that registered the
# given subscription. The hub will send us a challenge containing this token.
SECRET_TOKEN = "SOME_SECRET_TOKEN"

# Should we ignore the hubs defined in the feeds we're consuming
ALWAYS_USE_DEFAULT_HUB = False

# What PSHB hub should we use for feeds that don't support PSHB. pollinghub.appspot.com is a hub I've set up that does polling.
DEFAULT_HUB = "http://pollinghub.appspot.com/"

# Should anyone be able to add/delete subscriptions or should access be restricted to admins
OPEN_ACCESS = False

# How often should a task, such as registering a subscription, be retried before we give up
MAX_TASK_RETRIES = 10

# Maximum number of items to be fetched for any part of the system that wants everything of a given data model type
MAX_FETCH = 500

# Should Streamer check that posts it receives from a putative hub are for feeds it's actually subscribed to
SHOULD_VERIFY_INCOMING_POSTS = False


# Buzz Chat Bot settings
# OAuth consumer key and secret - you should change these to 'anonymous' unless you really are buzzchatbot.appspot.com
# Alternatively you could go here: https://www.google.com/accounts/ManageDomains and register your instance so that
# you'll get your own consumer key and consumer secret
#CONSUMER_KEY = 'buzzchatbot.appspot.com'
#CONSUMER_SECRET = 'tcw1rCMgLVY556Y0Q4rW/RnK'
CONSUMER_KEY = 'anonymous'
CONSUMER_SECRET = 'anonymous'

# OAuth callback URL
CALLBACK_URL = '%s/finish_dance' % APP_URL
PROFILE_HANDLER_URL = '/profile'
FRONT_PAGE_HANDLER_URL = '/'
# Installation specific config ends.
