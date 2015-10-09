import os
import urllib


from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.api import mail

import json
import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

from trending import *

class Stream(ndb.Model):
    ownerEmail = ndb.StringProperty()
    name = ndb.StringProperty()
    inviteMsg = ndb.StringProperty(indexed = False)
    coverUrl = ndb.StringProperty(indexed=False)
    time = ndb.DateTimeProperty(auto_now_add=True)
class Image(ndb.Model):
    time = ndb.DateTimeProperty(auto_now_add=True)
    stream = ndb.KeyProperty(kind=Stream)
    full_size_image = ndb.BlobProperty()
class Subscriber(ndb.Model):
    stream = ndb.KeyProperty(kind=Stream)
    email = ndb.StringProperty()
class View(ndb.Model):
    stream = ndb.KeyProperty(kind=Stream)
    time = ndb.DateTimeProperty(auto_now_add=True)
class Tag(ndb.Model):
    name = ndb.StringProperty()
    stream = ndb.KeyProperty(kind=Stream)


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
            myStreamList = Stream().query(Stream.ownerEmail == user.email())#.fetch()
            numViewsList_my = []
            lastupdatetime_my = []
            numberofpicture_my = []

            for elem in myStreamList:
                viewCount = View.query(View.stream == elem.key).count(limit=None)
                Piccount = Image.query(Image.stream == elem.key).count(limit=None)

                query_image = Image.query(Image.stream == elem.key).order(-Image.time).fetch()
                if len(query_image) == 0:
                    updatetime = elem.time.strftime('%I:%M%p on %b %d, %Y')
                else:
                    updatetime = query_image[0].time.strftime('%I:%M%p on %b %d, %Y')

                numViewsList_my.append(viewCount)
                lastupdatetime_my.append(updatetime)
                numberofpicture_my.append(Piccount)

            subscribeStreamList = []
            numViewsList_sub = []
            lastupdatetime_sub = []
            numberofpicture_sub = []

            lst = Subscriber.query(Subscriber.email == user.email())
            if lst:
                for elem in lst:
                    subscribeStreamList.append(elem.stream)
                    viewCount = View.query(View.stream == elem.stream).count(limit=None)
                    Piccount = Image.query(Image.stream == elem.stream).count(limit=None)
                    query_image = Image.query(Image.stream == elem.stream).order(-Image.time).fetch()
                    if len(query_image) == 0:
                        updatetime = elem.stream.get().time.strftime('%I:%M%p on %b %d, %Y')
                    else:
                        updatetime = query_image[0].time.strftime('%I:%M%p on %b %d, %Y')

                    numViewsList_sub.append(viewCount)
                    lastupdatetime_sub.append(updatetime)
                    numberofpicture_sub.append(Piccount)

            my_grouped_list = zip(myStreamList, numViewsList_my, lastupdatetime_my, numberofpicture_my)
            sub_grouped_list = zip(subscribeStreamList, numViewsList_sub, lastupdatetime_sub, numberofpicture_sub)

            template_values = {
                'my_grouped_list': my_grouped_list,
                'sub_grouped_list': sub_grouped_list,
            }
            template = JINJA_ENVIRONMENT.get_template('Manage.html')
            self.response.write(template.render(template_values))


class DeleteStream(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            myStreamList = Stream.query(Stream.ownerEmail == user.email()).fetch()
            for myStream in myStreamList:
                check = self.request.get(myStream.name)
                if check=='on':
                    myStream.key.delete()
                    View_list = View.query(View.stream == myStream.key)
                    for viewstobeDelete in View_list:
                        viewstobeDelete.key.delete()
            self.redirect('/manage')


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
            streamList = Stream.query(Stream.name==name).fetch()
            if len(streamList) != 0:
                self.redirect('/error?errorType=0')
            else:
                inviteMsg = self.request.get('msg')
                coverUrl = self.request.get('cover_url')
                tagsString = self.request.get('tags')
                subscribersString = self.request.get('subscribers')
                print "subscribersString"
                print subscribersString
                print "len(subscribersString)"
                print len(subscribersString)
                if subscribersString==None:
                    print "subscribersString == None"
                elif subscribersString=="":
                    print "subscribersString is an empty string"
                else:
                    print "non"


                ownerEmail = user.email()

                stream = Stream()
                stream.ownerEmail = ownerEmail
                stream.name = name
                stream.inviteMsg = inviteMsg
                stream.coverUrl = coverUrl
                stream.put()

                if tagsString != "":
                    tagsList = tagsString.split(', ')
                    for item in tagsList:
                        tag = Tag()
                        tag.name = item
                        tag.stream = stream.key
                        tag.put()

                if subscribersString != "":
                    subscribersList = subscribersString.split(', ')
                    for item in subscribersList:
                        subscriber = Subscriber()
                        subscriber.email = item
                        subscriber.stream = stream.key
                        subscriber.put()
                        if len(item) > 1:
                            if inviteMsg != "":
                                mail.send_mail(sender = user.email(),
                                                to = item,
                                                subject = "You are invited to a New Stream!",
                                                body = "You are invited to stream "+name+ ". The following is the message from the Creator:\n" + inviteMsg)
                            else:
                                mail.send_mail(sender = user.email(),
                                                to = item,
                                                subject = "You are invited to a New Stream!",
                                                body = "You are invited to stream "+name+ "." )




                self.redirect('/manage')

class ViewAllPage(webapp2.RequestHandler):
    def get(self):
        stream_list=Stream.query().order(-Stream.time)
        template_values = {
            'Streams': stream_list,
        }
        template = JINJA_ENVIRONMENT.get_template('View_all.html')
        self.response.write(template.render(template_values))

class Search(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('Search.html')
        self.response.write(template.render())

    def post(self):
        streamset=set()
        searchtarget = self.request.get('target')
        # targetTagList = self.request.get('target').split(', ')
        if len(searchtarget) > 0:
            name_result = Stream.query(searchtarget == Stream.name).order(-Stream.time)
            tag_result = Tag.query(searchtarget == Tag.name)

            result_list = name_result.fetch(5)

            for names in name_result:
                streamKey = names.key
                if streamKey not in streamset:      #create a set of streams wihch match the result
                    streamset.add(streamKey)
                else:
                    pass

            i = 0
            for tags in tag_result:
                key_of_stream = tags.stream
                if i == 5:
                    pass
                else:
                    if key_of_stream in streamset:
                        pass
                    else:
                        streamset.add(key_of_stream)
                        result_list.append(key_of_stream.get())
                        i = i+1

            if len(result_list)==0:
                template_values={
                    'Results':result_list,
                    }
                template = JINJA_ENVIRONMENT.get_template('Search.html')
                self.response.write(template.render(template_values))
            else:
                template_values={
                    'Results':result_list,
                    }
                template = JINJA_ENVIRONMENT.get_template('Search.html')
                self.response.write(template.render(template_values))
        else:
            template = JINJA_ENVIRONMENT.get_template('Search.html')
            self.response.write(template.render())




class ViewSinglePage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        streamKey = ndb.Key(urlsafe=self.request.get('streamKey'))

        pic_skip = 0

        imgList = Image.query(Image.stream == streamKey).order(-Image.time).fetch(3, offset = pic_skip)
        ownerCheck = 'notOwner'
        if streamKey.get().ownerEmail == user.email():
            ownerCheck = 'isOwner'

        template_values = {
            'imgList':imgList,
            'streamKey': streamKey,
            'ownerCheck': ownerCheck,
            'skiptimes': pic_skip,
            }
        template = JINJA_ENVIRONMENT.get_template('View_single.html')
        self.response.write(template.render(template_values))

        view = View()
        view.stream = streamKey
        view.put()

    def post(self):
        user = users.get_current_user()
        skiptimes = self.request.get('skiptimes')
        streamKey = ndb.Key(urlsafe=self.request.get('streamKey'))

        pic_skip = int(skiptimes)+3
        pic_to_display = pic_skip
        RemainingImgList = Image.query(Image.stream == streamKey).order(-Image.time).fetch(3, offset = pic_skip)

        pic_to_display = pic_to_display + len(RemainingImgList)
        imgList = Image.query(Image.stream == streamKey).order(-Image.time).fetch(pic_to_display)

        ownerCheck = 'notOwner'
        if streamKey.get().ownerEmail == user.email():
            ownerCheck = 'isOwner'

        template_values = {
            'imgList':imgList,
            'streamKey': streamKey,
            'ownerCheck': ownerCheck,
            'skiptimes': pic_skip,
            }
        template = JINJA_ENVIRONMENT.get_template('View_single.html')
        self.response.write(template.render(template_values))

        view = View()
        view.stream = streamKey
        view.put()

class Subscribe(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        streamKey = ndb.Key(urlsafe=self.request.get('streamKey'))
        subscribersList = Subscriber.query(Subscriber.stream == streamKey).fetch()

        # avoid repeated subscribe
        isRepeat = False
        for subscriber in subscribersList:
            if subscriber.email == user.email():
                isRepeat = True
                break

        if not isRepeat:
            subscriber = Subscriber()
            subscriber.stream = streamKey
            subscriber.email = user.email()
            subscriber.put()

        imgList = Image.query(Image.stream == streamKey).order(-Image.time).fetch()

        template_values = {
            'imgList':imgList,
            'streamKey': streamKey,
        }
        template = JINJA_ENVIRONMENT.get_template('View_single.html')
        self.response.write(template.render(template_values))

class Unsubscribe(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            lst = Subscriber().query(Subscriber.email == user.email()).fetch()
            for subscriber in lst:
                stream_name = self.request.get(subscriber.stream.get().name)
                if stream_name and stream_name=='on':
                    subscriber.key.delete()
            self.redirect('/manage')

class AddImage(webapp2.RequestHandler):
    def post(self):
        if self.request.get('file') != "":
            streamKey = ndb.Key(urlsafe=self.request.get('streamKey'))
            img = Image()
            img.stream = streamKey
            # img_temp = self.request.get('img')
            # img.full_size_image = images.resize(img_temp ,width=300, height=300, crop_to_fit = True)
            img.full_size_image = self.request.get('file')
            img.put()

            self.redirect('/View_single?streamKey='+streamKey.urlsafe())
        else:
            self.redirect('/error?errorType=1')


class ErrorPage(webapp2.RequestHandler):
    def get(self):
        errorType = self.request.get('errorType')
        if errorType=='0':
            errorMsg = "Trying to create a new stream which has the same name as an existing stream"
        elif errorType=='1':
            errorMsg = "You didn't select an image."
        else:
            errorMsg = "Something went wrong"

        template_values = {
            'errorMsg': errorMsg
        }
        template = JINJA_ENVIRONMENT.get_template('Error_Page.html')
        self.response.write(template.render(template_values))

class ImageHandler(webapp2.RequestHandler):
    def get(self):
        ImageKey = ndb.Key(urlsafe=self.request.get('img_id'))
        img = ImageKey.get()
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(img.full_size_image)

class SearchList(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        term = self.request.get('term')
        result = dict()
        if len(term) > 0:
            candidate = ListofIndex.query().order(-ListofIndex.time).fetch()
            for index in candidate:
                if term.lower() in index.index.lower():
                    result[index.index] = index.index
                else:
                    pass
            self.response.write(json.dumps(result))
        else:
            self.response.write(json.dumps(result))

class Trending(webapp2.RequestHandler):
    def get(self):
        Popular_stream_list = PopularStreams.query().order(-PopularStreams.numberofviews).fetch()
        stream_list = list()
        view_list = list()
        for item in Popular_stream_list:
            stream_list.append(item.stream)
            view_list.append(item.numberofviews)

        FinalResult = zip(stream_list, view_list)

        updateRateMessage = "Unavailable"

        template_values = {
            'Streams': FinalResult,
            'updateRateMessage': updateRateMessage,
        }
        template = JINJA_ENVIRONMENT.get_template('Trending.html')
        self.response.write(template.render(template_values))
    def post(self):
        user = users.get_current_user()
        if user:
            Popular_stream_list = PopularStreams.query().order(-PopularStreams.numberofviews).fetch()
            stream_list = list()
            view_list = list()
            for item in Popular_stream_list:
                stream_list.append(item.stream)
                view_list.append(item.numberofviews)
            FinalResult = zip(stream_list, view_list)


            lst = EmailUpdateList.query(EmailUpdateList.mail == user.email()).fetch()
            if len(lst) == 0:
                trendRate = self.request.get('trendRate')
                if trendRate == 'Every 5 minutes':
                    updateRateMessage = "You will receive trending report every 5 minutes"
                    emailUpdateList = EmailUpdateList()
                    emailUpdateList.mail = user.email()
                    emailUpdateList.duration = 5
                    emailUpdateList.put()
                elif trendRate == 'Every 1 hour':
                    updateRateMessage = "You will receive trending report every 1 hour"
                    emailUpdateList = EmailUpdateList()
                    emailUpdateList.mail = user.email()
                    emailUpdateList.duration = 60
                    emailUpdateList.put()
                elif trendRate == 'Every day':
                    updateRateMessage = "You will receive trending report every day"
                    emailUpdateList = EmailUpdateList()
                    emailUpdateList.mail = user.email()
                    emailUpdateList.duration = 1440
                    emailUpdateList.put()
                elif trendRate == 'No report':
                    updateRateMessage = "You have never registered trending report before"
            elif len(lst)==1:
                emailUpdateList = lst[0]
                trendRate = self.request.get('trendRate')
                if trendRate == 'Every 5 minutes':
                    updateRateMessage = "You will receive trending report every 5 minutes"
                    emailUpdateList.duration = 5
                    emailUpdateList.put()
                elif trendRate == 'Every 1 hour':
                    updateRateMessage = "You will receive trending report every 1 hour"
                    emailUpdateList.duration = 60
                    emailUpdateList.put()
                elif trendRate == 'Every day':
                    updateRateMessage = "You will receive trending report every day"
                    emailUpdateList.duration = 1440
                    emailUpdateList.put()
                elif trendRate == 'No report':
                    updateRateMessage = "You canceled receiving trending report"
                    emailUpdateList.key.delete()
            else:
                # Error protection: delete all, then recreate.
                for emailUpdateList in lst:
                    emailUpdateList.key.delete()

                trendRate = self.request.get('trendRate')
                if trendRate == 'Every 5 minutes':
                    updateRateMessage = "You will receive trending report every 5 minutes"
                    emailUpdateList = EmailUpdateList()
                    emailUpdateList.mail = user.email()
                    emailUpdateList.duration = 5
                    emailUpdateList.put()
                elif trendRate == 'Every 1 hour':
                    updateRateMessage = "You will receive trending report every 1 hour"
                    emailUpdateList = EmailUpdateList()
                    emailUpdateList.mail = user.email()
                    emailUpdateList.duration = 60
                    emailUpdateList.put()
                elif trendRate == 'Every day':
                    updateRateMessage = "You will receive trending report every day"
                    emailUpdateList = EmailUpdateList()
                    emailUpdateList.mail = user.email()
                    emailUpdateList.duration = 1440
                    emailUpdateList.put()
                elif trendRate == 'No report':
                    updateRateMessage = "You canceled receiving trending report"


            template_values = {
                'Streams': FinalResult,
                'updateRateMessage': updateRateMessage,
            }
            template = JINJA_ENVIRONMENT.get_template('Trending.html')
            self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', LandingPage),
    ('/manage', ManagePage),
    ('/create', CreatePage),
    ('/View_all', ViewAllPage),
    ('/View_single', ViewSinglePage),
    ('/subscribe', Subscribe),
    ('/unsubscribe', Unsubscribe),
    ('/deleteStream', DeleteStream),
    ('/Add_Image', AddImage),
    ('/img', ImageHandler),
    ('/search', Search),
    ('/crontask', CronTask),
    ('/update5',Update5),
    ('/updatehour',UpdateHour),
    ('/updateday', UpdateDay),
    ('/trending', Trending),
    ('/updatelistauto', UpdateListAuto),
    ('/searchlist', SearchList),
    ('/error', ErrorPage),
], debug=True)
