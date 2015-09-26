import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import images

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
from connexus import *

class PopularStreams(ndb.Model):
    streams = ndb.KeyProperty(kind='Stream', repeated=True)
    numberofviews = ndb.IntegerProperty(repeated=True)


LastResult = PopularStreams.query().fetch()

for items in LastResult:
    items.key.delete()

ViewsWeCare = View.query(datetime.timedelta(hours=int(datetime.datetime.now()-View.time)<=1))

list_of_views=list()
TrendingStreams=list()
Viewnumber=list()

for view in ViewsWeCare:
    list_of_views.append(view.stream)

TrendingStreams_Temp=Counter(list_of_views).most_common(5)

for streams in TrendingStreams_Temp:
    Viewnumber.append(streams[1])
    TrendingStreams.append(streams[0])

Test = PopularStreams(streams = [1,2,3], numberofviews = [1,2,3])
FinalResult = PopularStreams(streams = TrendingStreams, numberofviews = Viewnumber)

Test.put()
FinalResult.put()
