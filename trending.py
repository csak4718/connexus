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

from connexus import *

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
    stream = ndb.KeyProperty(kind='Stream')
    numberofviews = ndb.IntegerProperty()
class View(ndb.Model):
    stream = ndb.KeyProperty(kind=Stream)
    time = ndb.DateTimeProperty(auto_now_add=True)
class ListofIndex(ndb.Model):
    index = ndb.StringProperty()
    time = ndb.DateTimeProperty(auto_now_add=True)
class Tag(ndb.Model):
    name = ndb.StringProperty()
    stream = ndb.KeyProperty(kind=Stream)

# Send trending report to 'mail' every 'duration'
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

        list_of_streams=list()
        trendingStreams=list()
        viewNumber=list()

        for view in ViewsWeCare:
            if hour_ago <= view.time:
                list_of_streams.append(view.stream)
            else:
                pass

        TrendingStreams_Temp = collections.Counter(list_of_streams).most_common(5)


        for tupleElem in TrendingStreams_Temp:
            FinalResult = PopularStreams()
            FinalResult.stream = tupleElem[0]
            FinalResult.numberofviews = tupleElem[1]
            FinalResult.put()

class UpdateListAuto(webapp2.RequestHandler):
    def get(self):
        LastResult = ListofIndex.query().fetch()

        for index in LastResult:
            index.key.delete()

        namelist = Stream.query().fetch()
        taglist = Tag.query().fetch()

        for stream in namelist:
            Result = ListofIndex()
            Result.index = stream.name
            Result.put()

        tagset=set()
        for tag in taglist:
            if tag.name not in tagset:
                tagset.add(tag.name)
                Result = ListofIndex()
                Result.index = tag.name
                Result.put()
            else:
                pass

class Update5(webapp2.RequestHandler):
    def get(self):
        mail_list = EmailUpdateList.query( EmailUpdateList.duration == 5 ).fetch()
        for user in mail_list:
            if len(user.mail) > 1:
                mail.send_mail(sender = "Connexus info@connexus-1079.appspotmail.com",
                                to = user.mail,
                                subject = "Update Trending",
                                body = " The New Trending is now Live! ")

class UpdateHour(webapp2.RequestHandler):
    def get(self):
        mail_list = EmailUpdateList.query( EmailUpdateList.duration == 60 ).fetch()
        for user in mail_list:
            if len(user.mail) > 1:
                mail.send_mail(sender = "Connexus info@connexus-1079.appspotmail.com",
                                to = user.mail,
                                subject = "Update Trending",
                                body = """ The New Trending is now Live! """)

class UpdateDay(webapp2.RequestHandler):
    def get(self):
        mail_list = EmailUpdateList.query( EmailUpdateList.duration == 1440 ).fetch()
        for user in mail_list:
            if len(user.mail) > 1:
                mail.send_mail(sender = "Connexus info@connexus-1079.appspotmail.com",
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
