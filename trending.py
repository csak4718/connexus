import os
import urllib

import datetime
import time
import logging
import collections

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.api import mail

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Stream(ndb.Model):
    ownerEmail = ndb.StringProperty()
    name = ndb.StringProperty()
    inviteMsg = ndb.StringProperty(indexed = False)
    coverUrl = ndb.StringProperty(indexed=False)
    time = ndb.DateTimeProperty(auto_now_add=True)
class PopularStreams(ndb.Model):
    streams = ndb.KeyProperty(kind='Stream')
    numberofviews = ndb.IntegerProperty()
class View(ndb.Model):
    stream = ndb.KeyProperty(kind=Stream)
    time = ndb.DateTimeProperty(auto_now_add=True)
class EmailUpdateList(ndb.Model):
    mail = ndb.StringProperty()
    duration = ndb.IntegerProperty()


class CronTask(webapp2.RequestHandler):
    def get(self):
        LastResult = PopularStreams.query().fetch()

        for items in LastResult:
            items.key.delete()

        hour_ago = datetime.datetime.today() - datetime.timedelta(hours=1)

        ViewsWeCare = View.query(View.time >= hour_ago).fetch()

        list_of_views=list()
        TrendingStreams=list()
        Viewnumber=list()

        for view in ViewsWeCare:
            if hour_ago <= view.time:
                list_of_views.append(view.stream)
            else:
                pass

        TrendingStreams_Temp = collections.Counter(list_of_views).most_common(5)


        for streams in TrendingStreams_Temp:
            FinalResult = PopularStreams()
            FinalResult.streams = streams[0]
            FinalResult.numberofviews = streams[1]
            FinalResult.put()

class Update5(webapp2.RequestHandler):
    def get(self):
        mail_list = EmailUpdateList.query( EmailUpdateList.duration == 5 )
        for user in mail_list:
            if len(user.mail) > 1:
                mail.send_mail(sender = "Connexus :: Info info@<connexus-1079>.appspotmail.com",
                                to = user.mail,
                                subject = "Update Trending",
                                body = """ The New Trending is now Live! """)

class UpdateHour(webapp2.RequestHandler):
    def get(self):
        mail_list = EmailUpdateList.query( EmailUpdateList.duration == 60 )
        for user in mail_list:
            if len(user.mail) > 1:
                mail.send_mail(sender = "Connexus :: Info info@<connexus-1079.appspotmail.com>",
                                to = user.mail,
                                subject = "Update Trending",
                                body = """ The New Trending is now Live! """)

class UpdateDay(webapp2.RequestHandler):
    def get(self):
        mail_list = EmailUpdateList.query( EmailUpdateList.duration == 1440 )
        for user in mail_list:
            if len(user.mail) > 1:
                mail.send_mail(sender = "Connexus :: Info <info@connexus-1079.appspotmail.com>",
                                to = user.mail,
                                subject = "Update Trending",
                                body = """ The New Trending is now Live! """)

"""
        for streams in TrendingStreams_Temp:
            Viewnumber.append(streams[1])
            TrendingStreams.append(streams[0])
        FinalResult = PopularStreams(streams = TrendingStreams, numberofviews = Viewnumber)

        FinalResult.put()
"""
