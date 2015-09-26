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

# class Owner(ndb.Model):
#     email = ndb.StringProperty()
class Stream(ndb.Model):
    ownerEmail = ndb.StringProperty()
    name = ndb.StringProperty()
    inviteMsg = ndb.StringProperty(indexed = False)
    coverUrl = ndb.StringProperty(indexed=False)
    time = ndb.DateTimeProperty(auto_now_add=True)
class Image(ndb.Model):
    # name = ndb.StringProperty(indexed=False)
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
            myStreamList = Stream().query(Stream.ownerEmail == user.nickname())#.fetch()
            numViewsList_my = []
            for elem in myStreamList:
                viewCount = View.query(View.stream == elem.key).count(limit=None)
                numViewsList_my.append(viewCount)

            subscribeStreamList = []
            numViewsList_sub = []
            lst = Subscriber().query(Subscriber.email == user.nickname())#.fetch()
            if lst:
                for elem in lst:
                    subscribeStreamList.append(elem.stream)
                    viewCount = View.query(View.stream == elem.stream).count(limit=None)
                    numViewsList_sub.append(viewCount)

            my_grouped_list = zip(myStreamList, numViewsList_my)
            sub_grouped_list = zip(subscribeStreamList, numViewsList_sub)

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
            myStreamList = Stream.query(Stream.ownerEmail == user.nickname()).fetch()
            for myStream in myStreamList:
                check = self.request.get(myStream.name)
                if check=='on':
                    myStream.key.delete()
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

                ownerEmail = user.nickname()

                stream = Stream()
                stream.ownerEmail = ownerEmail
                stream.name = name
                stream.inviteMsg = inviteMsg
                stream.coverUrl = coverUrl
                stream.put()

                tagsList = tagsString.split(', ')
                for item in tagsList:
                    tag = Tag()
                    tag.name = item
                    tag.stream = stream.key
                    tag.put()

                subscribersList = subscribersString.split(', ')
                for item in subscribersList:
                    subscriber = Subscriber()
                    subscriber.email = item
                    subscriber.stream = stream.key
                    subscriber.put()

                self.redirect('/manage')

class ViewAllPage(webapp2.RequestHandler):
    def get(self):
        stream_list=Stream.query().order(-Stream.time)
        template_values = {'Streams': stream_list}
        template = JINJA_ENVIRONMENT.get_template('View_all.html')
        self.response.write(template.render(template_values))

class Search(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('Search.html')
        self.response.write(template.render())

    def post(self):
        streamset=set()
        searchtarget = self.request.get('target')
        name_result = Stream.query(searchtarget == Stream.name)
        tag_result =  Tag.query(searchtarget == Tag.name)

        result_list = name_result.fetch()

        for names in name_result:
            streamKey = names.key
            if streamKey not in streamset:
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

        if len(result_list)==0:
            template_values={'Results':result_list, 'Test': [0,0,0,0]}
            template = JINJA_ENVIRONMENT.get_template('Search.html')
            self.response.write(template.render(template_values))
        else:
            template_values={'Results':result_list, 'Test': [1,1,1,1]}
            template = JINJA_ENVIRONMENT.get_template('Search.html')
            self.response.write(template.render(template_values))




class ViewSinglePage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        streamKey = ndb.Key(urlsafe=self.request.get('streamKey'))
        # print "streamKey:"
        # print streamKey
        # print
        imgList = Image.query(Image.stream == streamKey).order(-Image.time).fetch()

        ownerCheck = 'notOwner'
        if streamKey.get().ownerEmail == user.nickname():
            ownerCheck = 'isOwner'



        template_values = {
            'imgList':imgList,
            'streamKey': streamKey,
            'ownerCheck': ownerCheck,
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
            if subscriber.email == user.nickname():
                isRepeat = True
                break

        if not isRepeat:
            subscriber = Subscriber()
            subscriber.stream = streamKey
            subscriber.email = user.nickname()
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
            lst = Subscriber().query(Subscriber.email == user.nickname()).fetch()
            for subscriber in lst:
                stream_name = self.request.get(subscriber.stream.get().name)
                if stream_name and stream_name=='on':
                    subscriber.key.delete()
            self.redirect('/manage')

class AddImage(webapp2.RequestHandler):
    def post(self):
        streamKey = ndb.Key(urlsafe=self.request.get('streamKey'))
        img = Image()
        img.stream = streamKey
        img.full_size_image= self.request.get('img')
        img.put()

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
        if (errorType=='0'):
            errorMsg = "Trying to create a new stream which has the same name as an existing stream"
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
    ('/error', ErrorPage)
], debug=True)
