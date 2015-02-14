from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import json
import math
import datetime
from resources.logger import Logger

def model_log_file():
    return 'around_debug.log'

def user_as_dict(self):
        user_dict = {'id':self.id,
                     'password':self.password,
                     'last_login':date_to_dict(self.last_login),
                     'is_superuser':self.is_superuser,
                     'username':self.username,
                     'first_name':self.first_name,
                     'last_name':self.last_name,
                     'email':self.email,
                     'is_staff':self.is_staff,
                     'is_active':self.is_active,
                     'date_joined':date_to_dict(self.date_joined)
        }
        return user_dict

def banter_user(self):
    bu = BanterUser.objects.get(user=self)
    return bu

User.add_to_class('user_as_dict', user_as_dict)
User.add_to_class('banter_user', banter_user)


class BanterUser(models.Model):
    user = models.ForeignKey(User, unique=True)
    date_updated = models.DateTimeField()
    type = models.CharField(max_length=100)
    profile_id = models.CharField(max_length=200)
    notification_token = models.CharField(max_length=200)
    profile_url = models.URLField(max_length=200)
    pic = models.CharField(max_length=200)

    def __str__(self):
        props = [self.user.first_name, self.user.last_name, self.user.email, self.profile_id]
        return property_linker(props)

    def add_friends(self, friends_list):
        # to-do: this algorithm runs in m*n time
        # can make this more efficient when time permits
        logger = Logger(model_log_file())
        for friend_dict in friends_list:
            # if friend_dict does not contain a banter_id, try and map friend to existing user. Otherwise, take no action
            if friend_dict['banter_id'] == 0:
                # friend has not been assigned a banter id. Try and retrieve friend.
                if friend_dict['profile_id']:
                    profile_id = friend_dict['profile_id']
                    friend_in_db = False
                    try:
                        friend_user = BanterUser.objects.get(profile_id=profile_id)
                        friend_in_db = True
                    except Exception as e:
                        # friend_user does not exist
                        logger.log_error('friend not in database with profile id #: ' + str(profile_id) + ' ' + str(e))
                        pass
                    if friend_in_db:
                        # check if friend is already one of user's friends
                        try:
                            user_friend = self.friend_set.filter(friend_user_id=friend_user.id)[0]
                        except Exception as e:
                            logger.log_message('friend is not in ' + self.user.first_name + ' friends set ' + str(e))
                            user_friend = Friend(banter_user=self,
                                                 friend_user_id=friend_user.id,
                                                 email=friend_user.user.email)
                            user_friend.save()
                            pass
        return None

    def banter_user_as_dict(self):
        banter_user_as_dict = {'first_name':self.user.first_name,
                               'last_name':self.user.last_name,
                               'profile_id':self.profile_id,
                               'email':self.user.email,
                               'banter_id':self.pk,
                               'profile_url':self.profile_url,
                               'date_updated':self.convert_date_to_string(),
                               'type':self.type,
                               'friends':self.make_friends_list()
        }
        return banter_user_as_dict

    def banter_user_as_json(self):
        bu_dict = {'id':self.id,
                   'user_id':self.user_id,
                   'date_updated':date_to_dict(self.date_updated),
                   'type':self.type,
                   'profile_id':self.profile_id,
                   'notification_token':self.notification_token,
                   'profile_url':self.profile_url,
                   'pic':self.pic,
        }
        return bu_dict

    def make_friends_list(self):
        friends_list = []
        friends = Friend.objects.filter(banter_user=self)
        for friend in friends:
            if friend.banter_user.type == 'facebook':
                try:
                    friends_list.append(friend.friend_as_dict())
                except Exception as e:
                    logger = Logger(model_log_file())
                    logger.log_error('could not save friend as dictionary: ' + str(e))
        return friends_list

    def picture_path(self):
        return settings.MEDIA_ROOT + 'profile_pics/' + self.user.email +  '.jpeg'

    def convert_date_to_string(self):
        return self.date_updated.strftime('%Y/%m/%d %H:%M:%S')

class Friend(models.Model):
    banter_user = models.ForeignKey(BanterUser)
    friend_user_id = models.IntegerField()
    email = models.EmailField(max_length=200)

    def friend_as_dict(self):
        friend_user = User.objects.get(id=self.friend_user_id)
        friend_dict = {'banter_id':self.friend_user_id,
                       'email':self.email,
                       'profile_id':friend_user.banter_user().profile_id,
                       'type':friend_user.banter_user().type,
                       'first_name':friend_user.first_name,
                       'last_name':friend_user.last_name
        }
        return friend_dict

    def from_dict(self, friend_dict):
        logger = Logger(model_log_file())
        email = friend_dict['email']
        banter_id = friend_dict['banter_id']
        user_found = True
        if email != '':
            self.email = email
            if not self.banter_user:
                try:
                    self.banter_user = User.objects.get(username=email)
                except Exception as e:
                    logger.log_error('error saving user: ' + self.email + ' ' + str(e))
                    user_found = False
        if user_found and not self.friend_user_id and banter_id != '':
            self.friend_user_id = banter_id
        return None

    def __str__(self):
        return self.email

class Scene(models.Model):
    type = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=200)
    logo_path = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    description = models.TextField()
    website_url = models.URLField(max_length=255)
    facebook_url = models.URLField(max_length=255)
    yelp_url = models.URLField(max_length=255)
    twitter_url = models.URLField(max_length=255)
    open_table_url = models.URLField(max_length=255)
    instagram_url = models.URLField(max_length=255)
    yelp_image_url = models.URLField(max_length=255)
    yelp_price_url = models.URLField(max_length=255)
    message = models.TextField()
    time_offset = models.IntegerField()
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=100)
    zip = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.CharField(max_length=200)
    longitude = models.CharField(max_length=200)
    monday = models.CharField(max_length=200)
    tuesday = models.CharField(max_length=200)
    wednesday = models.CharField(max_length=200)
    thursday = models.CharField(max_length=200)
    friday = models.CharField(max_length=200)
    saturday = models.CharField(max_length=200)
    sunday = models.CharField(max_length=200)

    def __str__(self):
        props = [self.type, self.name, self.contact, self.phone_number, self.email, self.website_url]
        return property_linker(props)

    def scene_as_dict(self):
        scene_dict = {'scene_id':self.id,
                      'type':self.type,
                      'name':self.name,
                      'contact':self.contact,
                      'logo':self.logo_path, #need to change this to return the image...once we have it
                      'phone_number':self.phone_number,
                      'email':self.email,
                      'description':self.description,
                      'website_url':self.website_url,
                      'facebook_url':self.facebook_url,
                      'yelp_url':self.yelp_url,
                      'twitter_url':self.twitter_url,
                      'open_table_url':self.open_table_url,
                      'instagram_url':self.instagram_url,
                      'yelp_image_url':self.yelp_image_url,
                      'yelp_price_url':self.yelp_price_url,
                      'message':self.message,
                      'address':self.address,
                      'city':self.city,
                      'state':self.state,
                      'zip':self.zip,
                      'country':self.country,
                      'latitude':self.latitude,
                      'longitude':self.longitude,
                      'monday':self.monday,
                      'tuesday':self.tuesday,
                      'wednesday':self.wednesday,
                      'thursday':self.thursday,
                      'friday':self.friday,
                      'saturday':self.saturday,
                      'sunday':self.sunday
        }
        return scene_dict

    def scene_as_trimmed_dict(self):
        scene_dict = {'scene_id':self.id,
                      'type':self.type,
                      'name':self.name,
                      'phone_number':self.phone_number,
                      'description':self.description,
                      'yelp_url':self.yelp_url,
                      'yelp_image_url':self.yelp_image_url,
                      'address':self.address,
                      'city':self.city,
                      'state':self.state,
                      'zip':self.zip,
                      'country':self.country,
                      'latitude':self.latitude,
                      'longitude':self.longitude,
                      'monday':self.monday,
                      'tuesday':self.tuesday,
                      'wednesday':self.wednesday,
                      'thursday':self.thursday,
                      'friday':self.friday,
                      'saturday':self.saturday,
                      'sunday':self.sunday
        }
        return scene_dict

    def get_events_as_dicts(self):
        events = []
        for event in self.event_set.all():
            events.append(event.event_as_dict())
        return events

    def get_comments(self):
        comments = list(self.comment_set.all())
        comments.sort(key=lambda Comment:Comment.date, reverse=True)
        comment_dicts = []
        for comment in comments:
            comment_dicts.append(comment.comment_as_dict())
        return comment_dicts

    def has_address(self):
        if self.address == '':
            return False
        return True

    def has_coordinate(self):
        if self.latitude == '' or self.longitude == '':
            return False
        return True

    def coordinate(self):
        return {'latitude':float(self.latitude), 'longitude':float(self.longitude)}

class Event(models.Model):
    scene = models.ForeignKey(Scene)
    start = models.DateTimeField(null=True)
    end = models.DateTimeField(null=True)
    recurring_start = models.TimeField(null=True)
    recurring_end = models.TimeField(null=True)
    ends_next_day = models.BooleanField(default=False)
    description1 = models.TextField()
    description2 = models.TextField()
    type = models.CharField(max_length=200)
    type_ext = models.CharField(max_length=2)
    message = models.TextField()
    exact_address = models.CharField(max_length=50)
    recurring_weekly = models.CharField(max_length=50)
    location_description = models.CharField(max_length=300)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=100)
    zip = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.CharField(max_length=200)
    longitude = models.CharField(max_length=200)
    monday = models.CharField(max_length=200)
    tuesday = models.CharField(max_length=200)
    wednesday = models.CharField(max_length=200)
    thursday = models.CharField(max_length=200)
    friday = models.CharField(max_length=200)
    saturday = models.CharField(max_length=200)
    sunday = models.CharField(max_length=200)

    def __str__(self):
        if self.start:
            start = self.start
        else:
            start = self.recurring_start
        if self.end:
            end = self.end
        else:
            end = self.recurring_end
        return 'type: %s start: %s end: %s' % (self.type,
                                               self.datetime_to_time_string(start),
                                               self.datetime_to_time_string(end))

    def event_as_dict(self, full_scene_info=True):
        if self.start:
            start = self.datetime_to_time_string(self.start)
            end = self.datetime_to_time_string(self.end)
        else:
            start = self.datetime_to_time_string(self.recurring_start)
            end = self.datetime_to_time_string(self.recurring_end)
        event_dict = {'scene_id':self.scene.id,
                      'event_id':self.id,
                      'start':start,
                      'end':end,
                      'description1':self.description1,
                      'description2':self.description2,
                      'type':self.type,
                      'type_ext':self.type_ext,
                      'message':self.message,
                      'address':self.address,
                      'city':self.city,
                      'state':self.state,
                      'zip':self.zip,
                      'country':self.country,
                      'latitude':self.latitude,
                      'longitude':self.longitude,
                      'monday':self.monday,
                      'tuesday':self.tuesday,
                      'wednesday':self.wednesday,
                      'thursday':self.thursday,
                      'friday':self.friday,
                      'saturday':self.saturday,
                      'sunday':self.sunday,
        }
        if full_scene_info:
            scene_dict = self.scene.scene_as_dict()
        else:
            scene_dict = self.scene.scene_as_trimmed_dict()
        event_dict['scene'] = scene_dict
        return event_dict

    def datetime_to_time_string(self, dt):
        hour = dt.hour
        minutes = dt.minute
        meridiem = 'AM'
        if hour == 12:
            meridiem = 'PM'
        if hour >= 13:
            hour -= 12
            meridiem = 'PM'
        if hour == 0 and meridiem == 'AM':
            hour = 12
        min_string = str(minutes)
        if len(min_string) == 1:
            min_string = '0' + min_string
        return str(hour) + ':' + min_string + ' ' + meridiem

    def has_address(self):
        if self.address == '':
            return False
        return True

    def has_coordinate(self):
        if self.latitude == '' or self.longitude == '':
            return False
        return True

    def coordinate(self):
        return {'latitude':float(self.latitude), 'longitude':float(self.longitude)}

    def occupancy_status(self):
        event_dict_light = {'event_id':self.id,
                           'type_ext':self.type_ext,
         }
        return event_dict_light

class Comment(models.Model):
    scene = models.ForeignKey(Scene)
    commenter = models.ForeignKey(BanterUser)
    comment = models.TextField()
    date = models.DateTimeField()

    def comment_as_dict(self):
        comment_dict = {'scene_id':self.scene.id,
                        'username':self.commenter.user.username,
                        'first_name':self.commenter.user.first_name,
                        'last_name':self.commenter.user.last_name,
                        'comment':self.comment,
                        'elapsed_time':self.time_since_comment(),
                        'comment_id':self.id,
                        'date_created':date_as_string(self.date)
                        }
        return comment_dict

    def time_since_comment(self):
        elapsed = datetime.datetime.now() - self.date
        if elapsed.days > 365:
            years = elapsed.days/365
            return str(years) + 'yrs ago'
        if elapsed.days > 30:
            months = elapsed.days/30
            return str(months) + 'months ago'
        if elapsed.days > 0:
            return str(elapsed.days) + 'day ago'
        minutes = elapsed.seconds/60
        hours = minutes/60
        if hours > 0:
            minutes = minutes%60
            return str(hours) + 'h ' + str(minutes) + 'min ago'
        if minutes > 0:
            return str(minutes) + 'min ago'
        return 'now'

def date_as_string(date):
        date_string = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        time_string = str(date.hour) + ':' + str(date.minute) + ':' + str(date.second)
        return date_string + ' ' + time_string

def property_linker(properties):
    return_val = ''
    for prop in properties:
        return_val += str(prop) + ' '
    return return_val

def date_to_dict(date):
    date_dict = {'year':date.year,
                 'month':date.month,
                 'day':date.day,
                 'hour':date.hour,
                 'minute':date.minute,
                 'second':date.second
    }
    return date_dict


class Log(models.Model):
    user = models.TextField()
    function = models.TextField()
    message = models.TextField()
    timestamp = models.DateTimeField()

class Decoder(models.Model):
    range = models.IntegerField()
    name = models.TextField()
    field = models.TextField()
    value = models.TextField()
