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


# class Person(ndb.Model):
#     personName = ndb.StringProperty(indexed=False)
#     guilds = ndb.KeyProperty(kind="Guild", repeated=True)
#
# class Guild(ndb.Model):
#     guildName = ndb.StringProperty(indexed=False)
#     @property
#     def members(self):
#         return Person.query().filter(Person.guilds == self.key)
#
#     def add_person(self, person):
#         person.guilds.append(self.key)
#         person.put()

class Landing(webapp2.RequestHandler):
    def get(self):
        # person1 = Person(personName='Sandy')
        # person1.put()
        # guild1 = Guild(guildName = 'guild1')
        # guild1.put()
        # guild1.add_person(person1)
        #
        # result = guild1.members()

        user = users.get_current_user();
        if user:
            log_url = users.create_logout_url(self.request.uri);
            log_url_linktext = 'Logout';

            template_values = {
                'user': user,
                'log_url': log_url,
                'log_url_linktext': log_url_linktext,
                # 'result': result,
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
                # 'result': result,
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
