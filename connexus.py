import os
import urllib
import urllib2


from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.api import mail
from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError
from math import radians, cos, sin, asin, sqrt

import jinja2
import webapp2
import json
import datetime

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

from trending import *

class Stream(ndb.Model):
    ownerEmail = ndb.StringProperty()
    name = ndb.StringProperty()
    inviteMsg = ndb.StringProperty(indexed=False)
    coverUrl = ndb.StringProperty(indexed=False)
    time = ndb.DateTimeProperty(auto_now_add=True)
    lastTimeUpload = ndb.DateTimeProperty()

class Image(ndb.Model):
    time = ndb.DateTimeProperty(auto_now_add=True)
    stream = ndb.KeyProperty(kind=Stream)
    full_size_image = ndb.BlobProperty()
    Thumbnail = ndb.BlobProperty()
    geoPt = ndb.GeoPtProperty()

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
                'myStreamList': myStreamList,
                'subscribeStreamList': subscribeStreamList,
            }
            template = JINJA_ENVIRONMENT.get_template('Manage.html')
            self.response.write(template.render(template_values))

class Unsubscribe(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            lst = Subscriber().query(Subscriber.email == user.email()).fetch()
            for subscriber in lst:
                check = self.request.get(subscriber.stream.get().name)
                if check and check=='on':
                    subscriber.key.delete()
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('success')

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
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('success')

class CheckSameStreamName(webapp2.RequestHandler):
    def post(self):
        name = self.request.get('stream_name')
        streamList = Stream.query(Stream.name==name).fetch()
        if len(streamList) != 0:
            isSame = 'yes'
        else:
            isSame = 'no'

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(isSame)

class CheckSubscribeOwnStream(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        subscribersString = self.request.get('subscribers')

        subscribe_your_own_stream = 'no'
        for item in subscribersString.split(', '):
            if item == user.email():
                subscribe_your_own_stream = 'yes'

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(subscribe_your_own_stream)


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
                if streamKey not in streamset:      #create a set of streams which match the result
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


class ErrorPage(webapp2.RequestHandler):
    def get(self):
        errorType = self.request.get('errorType')
        if errorType=='0':
            errorMsg = "Trying to create a new stream which has the same name as an existing stream"
        elif errorType=='1':
            errorMsg = "You didn't select an image."
        elif errorType=='2':
            errorMsg = "Sorry, only string is allowed as urlsafe input"
        elif errorType=='3':
            errorMsg = "Sorry, the urlsafe string seems to be invalid"
        elif errorType=='4':
            errorMsg = "Stream's name cannot be empty"
        elif errorType=='5':
            errorMsg = "You cannot subscribe your own stream"
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

class ImageHandler_Thumb(webapp2.RequestHandler):
    def get(self):
        ImageKey = ndb.Key(urlsafe=self.request.get('img_id'))
        img = ImageKey.get()
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(img.Thumbnail)

class SearchList(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        term = self.request.get('term')
        result = dict()
        if len(term) > 0:
            candidate = ListofIndex.query().order(-ListofIndex.time).fetch()
            for index in candidate:
                if term.lower() in index.index.lower():
                    if len(result) >= 20:
                        pass
                    else:
                        result[index.index] = index.index
                else:
                    pass
            self.response.write(json.dumps(result))
        else:
            self.response.write(json.dumps(result))

class SearchListofName(webapp2.RequestHandler):
    def get(self):
        namelist = Stream.query().fetch()
        Result=[]
        for stream in namelist:
            Result.append(stream.name)

        self.response.headers['Content-Type'] = 'application/json'
        term = self.request.get('term')
        result = dict()
        if len(term) > 0:
            candidate = Result
            for index in candidate:
                if term.lower() in index.lower():
                    if len(result) >= 20:
                        pass
                    else:
                        result[index] = index
                else:
                    pass
            self.response.write(json.dumps(result))
        else:
            self.response.write(json.dumps(result))


class MarkerImageHandler(webapp2.RequestHandler):
    def get(self):
        ImageKey = ndb.Key(urlsafe=self.request.get('img_id'))
        img = ImageKey.get()
        markerImage = images.resize(img.full_size_image ,width=100, height=100, crop_to_fit = True)
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(markerImage)

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

class Geo_Data(webapp2.RequestHandler):
    def get(self):
        streamKey = ndb.Key(urlsafe=self.request.get('streamKey'))
        query_begin_date = self.request.get('start')
        query_end_date = self.request.get('end')
        query_begin_date_obj = datetime.datetime.strptime(query_begin_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        query_end_date_obj = datetime.datetime.strptime(query_end_date, "%Y-%m-%dT%H:%M:%S.%fZ")

        imgList = Image.query(Image.stream == streamKey).order(-Image.time).fetch()
        for img in imgList:
            if not query_begin_date_obj <= img.time <= query_end_date_obj:
                imgList.remove(img)


        self.response.headers['Content-Type'] = 'application/json'
        markers = []
        for img in imgList:
            if img.geoPt is not None:
                content = '<img src="/markerImg?img_id=' + img.key.urlsafe() + '" alt="image">'
                markers.append({'latitude': img.geoPt.lat, 'longitude': img.geoPt.lon, 'content': content})

        data = {
            'markers': markers,
        }
        self.response.out.write(json.dumps(data))


class Geo(webapp2.RequestHandler):
    def get(self):
        streamKey = ndb.Key(urlsafe=self.request.get('streamKey'))

        template_values = {
            'streamKey': streamKey,
        }
        template = JINJA_ENVIRONMENT.get_template('geo.html')
        self.response.write(template.render(template_values))

class CreateFromExtension(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        ImageUrl = self.request.get('term')

        template_values = {
            'ImgUrl': ImageUrl,
        }
        if user:
            template = JINJA_ENVIRONMENT.get_template('CreateFromExtension.html')
            self.response.write(template.render(template_values))

    def post(self):
        user = users.get_current_user()
        ImageUrl = self.request.get('TheURL')
        webimg = urllib2.urlopen(ImageUrl).read()
        lat = self.request.get('lat')
        lng = self.request.get('lng')
        imgLocation = lat+", "+lng
        print "imgLocation"
        print imgLocation

        if user:
            name = self.request.get('name')

            streamList = Stream.query(Stream.name==name).fetch()
            for stream in streamList:
                if imgLocation != ", ":
                    img = Image()
                    img.stream = stream.key
                    img_temp = webimg
                    img.Thumbnail = images.resize(img_temp ,width=300, height=300, crop_to_fit = True)
                    img.full_size_image = img_temp
                    img.geoPt = ndb.GeoPt(imgLocation)
                    img.put()

                    stream.lastTimeUpload = img.time
                    stream.put()

                    self.redirect('/View_single?streamKey='+stream.key.urlsafe())
                else:
                    # user chose not to share his geo location
                    img = Image()
                    img.stream = stream.key
                    img_temp = webimg
                    img.Thumbnail = images.resize(img_temp ,width=300, height=300, crop_to_fit = True)
                    img.full_size_image = img_temp
                    img.put()

                    stream.lastTimeUpload = img.time
                    stream.put()

                    self.redirect('/View_single?streamKey='+stream.key.urlsafe())

class CheckIsOwner(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        name = self.request.get('stream_name')
        streamList = Stream.query(Stream.name==name).fetch()
        if len(streamList)==1:
            if streamList[0].ownerEmail==user.email():
                isOwner = 'yes'
            else:
                isOwner = 'no'
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(isOwner)

class CheckStreamExist(webapp2.RequestHandler):
    def post(self):
        name = self.request.get('stream_name')
        streamList = Stream.query(Stream.name==name).fetch()
        if len(streamList) == 0:
            isExist = 'no'
        else:
            isExist = 'yes'

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(isExist)

# reference
class View_all_photos_mobile(webapp2.RequestHandler):
    def get(self):
        imageQuery = Image.query()
        imageList = []
        imageURLList = []
        # imageCaptionList = []
        for pic in imageQuery:
            imageList.append(pic)

        imageList = sorted(imageList, key=lambda k: k.time,reverse = True)

        for pic in imageList:
            picURL = images.get_serving_url(pic.blob_key)
            imageURLList.append(picURL)
            # imageCaptionList.append(pic.caption)

        dictPassed = {
            'displayImages':imageURLList,
            # 'imageCaptionList':imageCaptionList
        }
        jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
        self.response.write(jsonObj)

class ViewSinglePage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        # print "STREAM KEY"
        # print self.request.get('streamKey')

        try:
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
        except TypeError:
            self.redirect('/error?errorType=2')
        except ProtocolBufferDecodeError:
            self.redirect('/error?errorType=3')



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

class MySubscribedImages_mobile(webapp2.RequestHandler):
    def get(self):
        userEmail = self.request.get("userEmail")
        lst = Subscriber.query(Subscriber.email == userEmail).fetch()
        imgList =[]
        for elem in lst:
            imgList += Image.query(Image.stream == elem.stream).fetch()

        imgList = sorted(imgList, key=lambda k: k.time, reverse = True)
        imageUrlList = []
        for img in imgList:
            url = "http://connexus-fall15.appspot.com/img?img_id="+img.key.urlsafe()
            imageUrlList.append(url)

        dictPassed = {
            'displayImages': imageUrlList,
        }
        jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
        self.response.write(jsonObj)

class View_single_mobile(webapp2.RequestHandler):
    def get(self):
        streamKey = ndb.Key(urlsafe=self.request.get('streamKey'))
        ownerEmail = streamKey.get().ownerEmail
        imgList = Image.query(Image.stream == streamKey).order(-Image.time).fetch()
        imageUrlList = []
        for img in imgList:
            url = "http://connexus-fall15.appspot.com/img?img_id="+img.key.urlsafe()
            imageUrlList.append(url)

        dictPassed = {
            'displayImages': imageUrlList,
            'ownerEmail': ownerEmail,
        }
        jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
        self.response.write(jsonObj)

class View_all_streams_mobile(webapp2.RequestHandler):
    def get(self):
        sorted_stream_list = Stream.query().order(-Stream.lastTimeUpload)
        coverImageUrlList = []
        streamKeyList = []
        streamNameList = []
        for stream in sorted_stream_list:
            streamKeyList.append(stream.key.urlsafe())
            streamNameList.append(stream.name)
            # print "StreamName"
            # print stream.name
            # print "COVER URL"
            # print stream.coverUrl
            if stream.coverUrl != "":
                coverImageUrlList.append(stream.coverUrl)
            else:
                coverImageUrlList.append("http://www.paganwardistro.com/imagens/distro/NoCoverAvailable.png")

        dictPassed = {
            'displayStreams': coverImageUrlList,
            'streamKeyList': streamKeyList,
            'streamNameList': streamNameList,
        }
        jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
        self.response.write(jsonObj)


class Search_mobile(webapp2.RequestHandler):
    def get(self):
        streamset=set()
        searchtarget = self.request.get('searchTerm')

        if len(searchtarget) > 0:
            name_result_all = Stream.query().order(-Stream.time).fetch()
            tag_result_all = Tag.query.fetch()
            name_result = []
            tag_result = []

            for stream in name_result_all:
                if searchtarget.lower() in stream.name.lower():
                    name_result.append(stream)
                else:
                    pass

            for tag in tag_result_all:
                if searchtarget.lower() in tag.name.lower():
                    tag_result.append(tag)
                else:
                    pass

            result_list = name_result.fetch()

            for names in name_result:
                streamKey = names.key
                if streamKey not in streamset:      #create a set of streams which match the result
                    streamset.add(streamKey)
                else:
                    pass


            for tags in tag_result:
                key_of_stream = tags.stream
                if key_of_stream in streamset:
                    pass
                else:
                    streamset.add(key_of_stream)
                    result_list.append(key_of_stream.get())


            coverImageUrlList = []
            streamKeyList = []
            streamNameList = []
            for stream in result_list:
                streamKeyList.append(stream.key.urlsafe())
                streamNameList.append(stream.name)

                if stream.coverUrl != "":
                    coverImageUrlList.append(stream.coverUrl)
                else:
                    coverImageUrlList.append("http://www.paganwardistro.com/imagens/distro/NoCoverAvailable.png")

            dictPassed = {
                'displayStreams': coverImageUrlList,
                'streamKeyList': streamKeyList,
                'streamNameList': streamNameList,
            }
            jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
            self.response.write(jsonObj)

class Search_Nearby_mobile(webapp2.RequestHandler):
    def get(self):
        user_lat = float(self.request.get('latitude'))
        user_lon = float(self.request.get('longitude'))
        img_list = Image.query().fetch()

        for img in img_list:
            print "GEO_PT"
            print img.geoPt
            if img.geoPt is None:
                img_list.remove(img)

        nearImageList = sorted(img_list, key=lambda k: self.haversine(user_lon, user_lat, k.geoPt.lon, k.geoPt.lat),reverse = True)
        imageUrlList = []
        sorted_stream_list = []
        for img in nearImageList:
            url = "http://connexus-fall15.appspot.com/img?img_id="+img.key.urlsafe()
            imageUrlList.append(url)
            sorted_stream_list.append(img.stream.get())

        streamKeyList = []
        streamNameList = []
        for stream in sorted_stream_list:
            streamKeyList.append(stream.key.urlsafe())
            streamNameList.append(stream.name)

        dictPassed = {
            'displayImages': imageUrlList,
            'streamKeyList': streamKeyList,
            'streamNameList': streamNameList,
        }

        jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
        self.response.write(jsonObj)


    def haversine(self, lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 3956 # Radius of earth in kilometers. Use 3956 for miles. Use 6371 for km.
        return c * r


class Add_Image_mobile(webapp2.RequestHandler):
    def post(self):
        # TODO: make photoCaption meaningful
        streamKey = ndb.Key(urlsafe=self.request.get('streamKey'))
        img = Image()
        img.stream = streamKey
        img_temp = self.request.get('file')
        img.Thumbnail = images.resize(img_temp ,width=300, height=300, crop_to_fit = True)
        img.full_size_image = img_temp
        imgLocation = self.request.get('imgLocation')
        img.geoPt = ndb.GeoPt(imgLocation)
        img.put()

        stream = streamKey.get()
        stream.lastTimeUpload = img.time
        stream.put()


class AddImage(webapp2.RequestHandler):
    def post(self):
        imgLocation = self.request.get('imgLocation')
        if imgLocation != "":
            streamKey = ndb.Key(urlsafe=self.request.get('streamKey'))
            img = Image()
            img.stream = streamKey
            img_temp = self.request.get('img')
            img.Thumbnail = images.resize(img_temp ,width=300, height=300, crop_to_fit = True)
            img.full_size_image = img_temp
            img.geoPt = ndb.GeoPt(imgLocation)
            img.put()
            print "IMG.TIME = "
            print img.time
            stream = streamKey.get()
            stream.lastTimeUpload = img.time
            stream.put()

            self.redirect('/View_single?streamKey='+streamKey.urlsafe())
        else:
            # user chose not to share his geo location
            streamKey = ndb.Key(urlsafe=self.request.get('streamKey'))
            img = Image()
            img.stream = streamKey
            img_temp = self.request.get('img')
            img.Thumbnail = images.resize(img_temp ,width=300, height=300, crop_to_fit = True)
            img.full_size_image = img_temp
            img.put()
            print "IMG.TIME = "
            print img.time
            stream = streamKey.get()
            stream.lastTimeUpload = img.time
            stream.put()

            self.redirect('/View_single?streamKey='+streamKey.urlsafe())


# imgList = Image.query(Image.stream == stream.key).order(-Image.time).fetch()


app = webapp2.WSGIApplication([
    ('/', LandingPage),
    ('/manage', ManagePage),
    ('/create', CreatePage),
    ('/View_all', ViewAllPage),
    ('/CreateFromExtension', CreateFromExtension),
    ('/View_single', ViewSinglePage),
    ('/subscribe', Subscribe),
    ('/unsubscribe', Unsubscribe),
    ('/deleteStream', DeleteStream),
    ('/Add_Image', AddImage),
    ('/img', ImageHandler),
    ('/img_thumb', ImageHandler_Thumb),
    ('/markerImg', MarkerImageHandler),
    ('/search', Search),
    ('/crontask', CronTask),
    ('/update5',Update5),
    ('/updatehour',UpdateHour),
    ('/updateday', UpdateDay),
    ('/trending', Trending),
    ('/updatelistauto', UpdateListAuto),
    ('/searchlist', SearchList),
    ('/searchlistofname', SearchListofName),
    ('/error', ErrorPage),
    ('/geo_data', Geo_Data),
    ('/geo', Geo),
    ('/checkSameStreamName', CheckSameStreamName),
    ('/checkSubscribeOwnStream', CheckSubscribeOwnStream),
    ('/checkStreamExist', CheckStreamExist),
    ('/checkIsOwner', CheckIsOwner),
    ('/View_single_mobile', View_single_mobile),
    ('/View_all_streams_mobile', View_all_streams_mobile),
    ('/Add_Image_mobile', Add_Image_mobile),
    ('/Search_mobile', Search_mobile),
    ('/Search_Nearby_mobile', Search_Nearby_mobile),
    ('/MySubscribedImages_mobile', MySubscribedImages_mobile),
], debug=True)
