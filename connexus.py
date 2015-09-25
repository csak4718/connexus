import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Owner(ndb.Model):
    email = ndb.StringProperty(indexed=False)
class Stream(ndb.Model):
    owner = ndb.StructuredProperty(Owner)
    name = ndb.StringProperty(indexed=False)
class Image(ndb.Model):
    name = ndb.StringProperty(indexed=False)
    time = ndb.DateTimeProperty(auto_now_add=True)
    stream = ndb.StructuredProperty(Stream)
class Subscriber(ndb.Model):
    stream = ndb.StructuredProperty(Stream)
    email = ndb.StringProperty(indexed=False)
class View(ndb.Model):
    stream = ndb.StructuredProperty(Stream)
    time = ndb.DateTimeProperty(auto_now_add=True)
class Tag(ndb.Model):
    name = ndb.StringProperty(indexed=False)
    stream = ndb.StructuredProperty(Stream)


class Landing(webapp2.RequestHandler):
    def get(self):

        user = users.get_current_user();
        if user:
            log_url = users.create_logout_url(self.request.uri);
            log_url_linktext = 'Logout';

            template_values = {
                'user': user,
                'log_url': log_url,
                'log_url_linktext': log_url_linktext,

            }

            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))
        else:
            log_url = users.create_login_url(self.request.uri)
            log_url_linktext = 'Login'

            template_values = {
                'user': user,
                'log_url': log_url,
                'log_url_linktext': log_url_linktext,

            }

            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))

class Manage(webapp2.RequestHandler):
    def post(self):
        # TODO
        pass


app = webapp2.WSGIApplication([
    ('/', Landing),
    ('/manage', Manage),
], debug=True)
