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
    email = ndb.StringProperty()
class Stream(ndb.Model):
    owner = ndb.StructuredProperty(Owner)
    name = ndb.StringProperty()
    inviteMsg = ndb.StringProperty(indexed = False)
    coverUrl = ndb.StringProperty(indexed=False)
    time = ndb.DateTimeProperty(auto_now_add=True)
class Image(ndb.Model):
    name = ndb.StringProperty(indexed=False)
    time = ndb.DateTimeProperty(auto_now_add=True)
    stream = ndb.StructuredProperty(Stream)
class Subscriber(ndb.Model):
    stream = ndb.StructuredProperty(Stream)
    email = ndb.StringProperty()
class View(ndb.Model):
    stream = ndb.StructuredProperty(Stream)
    time = ndb.DateTimeProperty(auto_now_add=True)
class Tag(ndb.Model):
    name = ndb.StringProperty()
    stream = ndb.StructuredProperty(Stream)


class LandingPage(webapp2.RequestHandler):
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

class ManagePage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            myStreamList = Stream.query(Stream.owner.email == user.nickname()).fetch()
            print myStreamList

            subscribeStreamList = []
            lst = Subscriber.query(Subscriber.email == user.nickname()).fetch()
            if lst:
                for elem in lst:
                    subscribeStreamList.append(elem.stream)
                print subscribeStreamList

            template_values = {
                'myStreamList': myStreamList,
                'subscribeStreamList': subscribeStreamList,
            }
            template = JINJA_ENVIRONMENT.get_template('Manage.html')
            self.response.write(template.render(template_values))
    def post(self):
        user = users.get_current_user()
        if user:
            myStreamList = Stream.query(Stream.owner.email == user.nickname()).fetch()
            for myStream in myStreamList:
                check = self.request.get(myStream.name)
                if check=='on':
                    myStream.key.delete()


            # template_values = {
            #     'myStreamList': myStreamList,
            #     'subscribeStreamList': subscribeStreamList,
            # }
            template = JINJA_ENVIRONMENT.get_template('Manage.html')
            self.response.write(template.render({}))


class CreatePage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            template = JINJA_ENVIRONMENT.get_template('Create.html')
            self.response.write(template.render({}))
    def post(self):
        user = users.get_current_user()
        if user:
            name = self.request.get('name')
            inviteMsg = self.request.get('msg')
            coverUrl = self.request.get('cover_url')
            tagsString = self.request.get('tags')
            subscribersString = self.request.get('subscribers')

            owner = Owner()
            owner.email = user.nickname()
            owner.put()

            stream = Stream()
            stream.owner = owner
            stream.name = name
            stream.inviteMsg = inviteMsg
            stream.coverUrl = coverUrl
            stream.put()

            tagsList = tagsString.split(', ')
            for item in tagsList:
                tag = Tag()
                tag.name = item
                tag.stream = stream
                tag.put()

            subscribersList = subscribersString.split(', ')
            for item in subscribersList:
                subscriber = Subscriber()
                subscriber.email = item
                subscriber.stream = stream
                subscriber.put()

            self.redirect('/manage')

class View_all(webapp2.RequestHandler):
    def get(self):
        stream_list=Stream.query().order(-Stream.time)
        template_values = {'Streams': stream_list}
        template = JINJA_ENVIRONMENT.get_template('View_all.html')
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', LandingPage),
    ('/manage', ManagePage),
    ('/create', CreatePage),
    ('/View_all', View_all),
], debug=True)
