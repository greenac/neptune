from data_models.models import Scene, Event, BanterUser, Friend
import datetime, math, django, os, sys, json, urllib2, random
from resources.logger import Logger

django.setup()
from django.contrib.auth.models import User
from django.conf import settings

MAX_HOURS_IN_DAY = 23
MAX_MINUTES_IN_HOUR = 59
MAX_SECONDS_IN_MINUTE = 59
LOG_LEVEL = 20
SHIFT_FROM_UTC = -8
IS_ONGOING = 'is_ongoing'
IS_UPCOMING = 'is_upcoming'
NOT_IN_TIME_FRAME = 'not_in_time_frame'
LOG_FILE = 'around_debug.log'

class Retriever:
    def __init__(self):
        # hours needs to be passed in. currently pdt offset from utc
        self.day_time_shift = 5
        self.now = datetime.datetime.utcnow() + datetime.timedelta(hours=SHIFT_FROM_UTC)
        self.day_start = self.make_start_of_day()
        self.day_end = self.make_end_of_day()
        self.user_location = {}
        self.logging = False
        self.log_str = ''
        self.current_event_ids = set([])
        self.expired_event_ids = set([])
        self.logger = Logger(LOG_FILE)
        self.event_info = EventInfo()
        self.meta_data_on = False
        self.for_occupancy = False

    def make_start_of_day(self):
        hour = self.now.hour
        if hour < self.day_time_shift:
            hour += 24
        return self.now + datetime.timedelta(hours=-hour + self.day_time_shift,
                                             minutes=-self.now.minute,
                                             seconds=-self.now.second)
    def make_end_of_day(self):
        hour = self.now.hour
        if hour < self.day_time_shift:
            hour += 24
        td = datetime.timedelta(hours=MAX_HOURS_IN_DAY - hour + self.day_time_shift,
                                minutes=MAX_MINUTES_IN_HOUR - self.now.minute,
                                seconds=MAX_SECONDS_IN_MINUTE - self.now.second)
        return self.now + td

    def get_events_in_time_frame(self):
        events = []
        try:
            fetched_events = self.events_to_process()
            for event in fetched_events:
                event_plus = EventPlus(event)
                status = self.is_event_in_time_frame(event_plus)
                include_event = False
                if status == IS_UPCOMING:
                    event_plus.plus[IS_UPCOMING] = True
                    include_event = True
                elif status == IS_ONGOING:
                    event_plus.plus[IS_ONGOING] = True
                    include_event = True
                if include_event:
                    d = distance_between_user_and_event(self.user_location, event_plus.event.coordinate())
                    event_plus.plus['distance_to_user'] = d
                    if self.meta_data_on:
                        event_plus.event.type = self.convert_event_type(event_plus.event.type)
                    events.append(event_plus.event_plus_as_dict())
                elif event.id in self.current_event_ids:
                    self.expired_event_ids.add(event.id)
        except Exception as e:
            self.logger.log_error(str(e) + ' get events in time frame')
        # if len(self.current_event_ids) > 0:
        #     events = self.filter_events(events)
        return sorted(events, key=lambda k:k['distance_to_user'])

    def events_to_process(self):
        if self.for_occupancy:
            return list(Event.objects.filter(type='occupancy'))
        return list(Event.objects.all())

    def convert_event_type(self, event_type):
        logger = Logger(LOG_FILE)
        try:
            if event_type == 'food_truck':
                event_type = 'foodTruck'
            elif event_type == 'happy_hour':
                event_type = 'happyHour'
            return event_type
        except Exception as e:
            logger.log_error(message='Error processing events: ' + str(e))
        return event_type

    def is_event_in_time_frame(self, event_plus):
        result = NOT_IN_TIME_FRAME
        try:
            if event_plus.event.recurring_start:
                event_plus.plus['is_recurring'] = True
                # event is recurring. set up datetime objects for event plus
                if self.include_recurring_event(event_plus):
                    # recurring event is on current day of week
                    # set up event plus date time objects
                    self.set_recurring_dates(event_plus,
                                             start_offset=event_plus.date_info['start_shift'],
                                             end_offset=event_plus.date_info['end_shift']
                    )
            else:
                # copy pointers from event's dates to event_plus dates for one time events
                event_plus.date_info['start_date'] = event_plus.event.start
                event_plus.date_info['end_date'] = event_plus.event.end
            # check if event occurs within a Banter! definition of a day
            event_start = event_plus.date_info['start_date']
            event_end = event_plus.date_info['end_date']
            if event_start and event_end:
                td_over = self.day_end - event_start
                if td_over.days >= 0:
                    # event is before our start of day
                    td_start = event_start - self.day_start
                    if td_start.days >= 0:
                        # event starts after our start of day
                        # at this point we know that the event's times are within our day
                        # we must now determine whether the event is already passed, ongoing, or upcoming
                        td_end = event_end - self.now
                        if td_end.days >= 0:
                            # event end is after our current time -- event is not over
                            td_start = self.now - event_start
                            if td_start.days >= 0:
                                # current time is after event start, so event must be ongoing
                                result = IS_ONGOING
                            else:
                                #current time is before the event start, so event must be upcoming
                                result = IS_UPCOMING
        except Exception as e:
            self.logger.log_error(str(e))
        return result

    def include_recurring_event(self, event_plus):
        # TODO have the 0s and 1s for recurring events shifted to according to our time shift in spread sheet also
        # TODO creating datetime objects for each object is taking too much time and memory. Simpler & cleaner to just
        # TODO have the data entered in the correct format
        if event_plus.event.ends_next_day:
            if self.now.hour <= self.day_time_shift:
                # check event against previous day. i.e. if wed at 12:55am
                # check tuesday to see if event occurs
                occurs_today = self.recurring_event_occurs_on_day(event_plus, check_previous=True)
                if occurs_today:
                    event_plus.date_info['start_shift'] = -1
            else:
                occurs_today = self.recurring_event_occurs_on_day(event_plus)
                if occurs_today:
                    event_plus.date_info['end_shift'] = 1
        else:
            occurs_today = self.recurring_event_occurs_on_day(event_plus)
        return occurs_today

    def recurring_event_occurs_on_day(self, event_plus, check_next=False, check_previous=False):
        day_number = self.day_start.weekday()
        if check_next:
            day_number += 1
            if day_number > 6:
                day_number = 0
        elif check_previous:
            day_number -= 1
            if day_number < 0:
                day_number = 6

        if day_number == 0:
            occurs_today = event_plus.event.monday == '1'
        elif day_number == 1:
            occurs_today = event_plus.event.tuesday == '1'
        elif day_number == 2:
            occurs_today = event_plus.event.wednesday == '1'
        elif day_number == 3:
            occurs_today = event_plus.event.thursday == '1'
        elif day_number == 4:
            occurs_today = event_plus.event.friday == '1'
        elif day_number == 5:
            occurs_today = event_plus.event.saturday == '1'
        else:
            occurs_today = event_plus.event.sunday == '1'
        return occurs_today

    def set_recurring_dates(self, event_plus, start_offset=0, end_offset=0):
        start_time = event_plus.event.recurring_start
        event_start = datetime.datetime(self.now.year,
                                        self.now.month,
                                        self.now.day,
                                        start_time.hour,
                                        start_time.minute)
        if start_offset != 0:
            event_start = event_start + datetime.timedelta(days=start_offset)
        event_plus.date_info['start_date'] = event_start

        end_time = event_plus.event.recurring_end
        event_end = datetime.datetime(self.now.year,
                                      self.now.month,
                                      self.now.day,
                                      end_time.hour,
                                      end_time.minute)
        if end_offset != 0:
            event_end = event_end + datetime.timedelta(days=end_offset)
        event_plus.date_info['end_date'] = event_end
        return None

    def filter_events(self, events):
        # events is an array of event plus objects. Check if the event is in the current events set
        # If it isn't in the set, add it to the events to be returned
        if len(self.current_event_ids) > 0:
            filtered_events = []
            for event_dict in events:
                if event_dict['event_id'] not in self.current_event_ids:
                    filtered_events.append(event_dict)
            return filtered_events
        return events

    def date_as_string(self, date):
        date_string = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        time_string = str(date.hour) + ':' + str(date.minute)
        return date_string + ' ' + time_string

    def log(self):
        if self.logging:
            self.logger.log_message(message=self.log_str)
        self.log_str = ''
        return None

class EventPlus:
    def __init__(self, event):
        self.event = event
        self.date_info = {'start_date':None,
                          'end_date':None,
                          'start_shift':0,
                          'end_shift':0
        }
        self.plus = {'is_ongoing':False,
                     'is_upcoming':False,
                     'is_recurring':False,
                     'distance_to_user':-1,
                     'day':0,
                     'month':0,
                     'year':0,
        }

    def event_plus_as_dict(self):
        try:
            d = self.event.event_as_dict(full_scene_info=False)
            for key, value in self.plus.items():
                d[key] = value
            if self.date_info['start_date'] and self.date_info['end_date']:
                d['start_date'] = date_to_string(self.date_info['start_date'])
                d['end_date'] = date_to_string(self.date_info['end_date'])
            return d
        except Exception as e:
            logger = Logger(LOG_FILE)
            logger.log_error('event plus as dict ' + str(e))
        return -1

class CityGetter:
    def __init__(self, latitude, longitude):
        self.api_key = 'AIzaSyDKZ_L40Thpm3u_uLMbOm1v3U_Pc1X9bJs'
        self.base_url = 'https://maps.googleapis.com/maps/api/geocode/json?latlng='
        self.latitude = latitude
        self.longitude = longitude
        self.banter_regions = {'san francisco'}
        self.max_radius = 40000.0 # radial distance in m from center of sf
        self.sf_city_center = {"latitude":37.79695630000001, "longitude":-122.4002903}

    def query_url(self):
        return self.base_url + str(self.latitude) + ',' + str(self.longitude) + '&key=' + self.api_key

    def make_query(self):
        logger = Logger(LOG_FILE)
        try:
            response = urllib2.urlopen(self.query_url())
            data = json.loads(response.read())
            city = data['results'][0]['address_components'][3]['long_name']
            logger.log_message(message='google api response city: ' + city)
            if city.lower() in self.banter_regions:
                logger.log_message(message='Banter! supports ' + city)
                return True
            logger.log_message(message='Banter! does not support ' + city)
        except Exception as e:
            logger.log_error(message='Error querying geocode api in city getter: ' + str(e))
        return False

    def in_radius(self):
        user_location = {'latitude':self.latitude, 'longitude':self.longitude}
        distance = distance_between_user_and_event(user_location, self.sf_city_center)
        if distance <= self.max_radius:
            return True
        return False

class Node:
    def __init__(self, value):
        self.payload = value
        self.prev = None
        self.next = None

class LinkedList:
    def __init__(self):
        nodes = []
        head = None
        tail = None

    def insert(self, value):
        node = Node(value)
        node.prev = self.tail
        self.tail = node
        self.nodes.append(object)

class ProfilePicController:
    def __init__(self, username):
        self.username = username

    def save_pic(self, pic_data):
        success = False
        try:
            with open(self.picture_path(), 'wb') as image_file:
                image_file.write(pic_data)
            image_file.close()
            success = True
        except Exception as e:
            logger = Logger(LOG_FILE)
            logger.log_error(message=str(e))
        if success:
            try:
                user = User.objects.get(username=self.username)
                banter_user = BanterUser.objects.get(user_id=user.id)
                banter_user.pic = self.pic_name()
                banter_user.save()
            except Exception as e:
                logger = Logger(LOG_FILE)
                logger.log_error(message='error saving profile pic for user: ' + self.username + '\nError: ' + str(e))
        return success

    def get_pic(self):
        pic_data = None
        try:
            with open(self.picture_path(), 'rb') as image_file:
                pic_data = image_file.read()
            image_file.close()
        except Exception as e:
            logger = Logger(LOG_FILE)
            logger.log_error(message='error getting profile pic ' + str(e))
        return pic_data

    def picture_path(self):
        return settings.MEDIA_ROOT + 'profile_pics/' + self.pic_name()

    def pic_name(self):
        return self.username + '.jpeg'

class EventInfo:
    def __init__(self):
        self.extensions = ['DotActive',
                           'DotNotActive',
                           'MapPinActive',
                           'MapPinNotActive',
                           'PinActive',
                           'PinNotActive',
                           'FilterActive',
                           'FilterNotActive'
        ]
        self.magnifiers = ['@2x', '@3x']

    def filter_order(self):
        section1_list = ['foodTruck', 'happyHour', 'performer']
        section2_list = ['occupancy1', 'occupancy2', 'occupancy3', 'occupancy4', 'occupancy5']
        sort_list = [section1_list, section2_list]
        return sort_list

    def available_images(self):
        names = []
        base_path = os.path.dirname(os.path.abspath(__file__))
        with open (base_path + '/files/event_icon_names.txt', 'r') as icon_file:
            for line in icon_file:
                line = line.replace('\n', '')
                names.append(line)
        icon_file.close()
        return set(names)

class EventIconHandler:
    def __init__(self, event_types=[]):
        self.event_types = event_types
        self.event_info = EventInfo()

    def dir_path(self):
        return settings.MEDIA_ROOT + 'event_icons/'

    def icon_exists(self, icon_name):
        path = self.dir_path() + icon_name
        if os.path.exists(path):
            return True
        return False

    def icon_urls(self):
        logger = Logger(LOG_FILE)
        urls = {}
        url_base = 'http://s3.amazonaws.com/banter-us-east-event-icons-2015-01-16/'
        event_types = []
        icon_names = self.event_info.available_images()
        for event_list in self.event_info.filter_order():
            event_types += event_list
        for event_type in event_types:
            urls_list = []
            for ext in self.event_info.extensions:
                pic_name = event_type + ext
                for magnifier in self.event_info.magnifiers:
                    pic_name_magnified = pic_name + magnifier + '.png'
                    if pic_name_magnified in icon_names:
                        url = url_base + pic_name_magnified
                        urls_list.append(url)
            if len(urls_list) > 0:
                urls[event_type] = urls_list
        return urls

    def get_icon(self, pic_name):
        # TODO -- this should only be a temporary method. This class should send s3 url
        pic_data = None
        if pic_name:
            pic_path = self.dir_path() + pic_name
            try:
                with open(pic_path, 'rb') as image_file:
                    pic_data = image_file.read()
                image_file.close()
            except Exception as e:
                logger = Logger(LOG_FILE)
                logger.log_error(message='error getting event pic ' + pic_name + ' with error: ' + str(e))
        return pic_data

def distance_between_user_and_event(user_location, pt):
        # pt = list[latitude,longitude]
        #distance between two point in meters
        try:
            earth_radius = 6371009.0  #in meters
            latitude1 = math.radians(user_location['latitude'])
            latitude2 = math.radians(pt['latitude'])
            d_latitude = latitude1 - latitude2
            d_longitude = math.radians(user_location['longitude'] - pt['longitude'])
            k = math.sin(.5*d_latitude)**2 + math.cos(latitude1)*math.cos(latitude2)*math.sin(.5*d_longitude)**2
            d = 2.0*earth_radius*math.asin(math.sqrt(k))
            return d
        except Exception as e:
            logger = Logger(LOG_FILE)
            logger.log_error(str(e))
        return None

def date_to_string(date):
    month = str(date.month)
    day = str(date.day)
    hour = str(date.hour)
    minute = str(date.minute)
    second = str(date.second)
    if date.month < 10:
        month = '0' + month
    if date.day < 10:
        day = '0' + day
    if date.hour < 10:
        hour = '0' + hour
    if date.minute < 10:
        minute = '0' + minute
    if date.second < 10:
        second = '0' + second
    return '%d-%s-%s %s:%s:%s' % (date.year, month, day, hour, minute, second)

# use update occupancy for testing. It is located in retriever.py.
# To use select current day, and it will cause all occupancies to appear
# for testing on dev only -- NOT FOR PRODUCTION!!
def update_occupancy():
    date = datetime.datetime.utcnow() - datetime.timedelta(hours=8)
    weekday = date.weekday()
    events = Event.objects.filter(type='occupancy')
    random.seed()
    day = ''
    for event in events:
        event.type_ext = str(random.randint(1,5))
        if weekday == 0:
            if day == '':
                day = 'Monday'
            event.monday = '1'
        elif weekday == 1:
            if day == '':
                day = 'Tuesday'
            event.tuesday = '1'
        elif weekday == 2:
            if day == '':
                day = 'Wednesday'
            event.wednesday = '1'
        elif weekday == 3:
            if day == '':
                day = 'Thursday'
            event.thursday = '1'
        elif weekday == 4:
            if day == '':
                day = 'Friday'
            event.friday = '1'
        elif weekday == 5:
            if day == '':
                day = 'Saturday'
            event.saturday = '1'
        else:
            if day == '':
                day = 'Sunday'
            event.sunday = '1'
        event.save()
    return day

def first_message():
    base_path = os.path.dirname(os.path.abspath(__file__))
    with open (base_path + '/files/opening_message.json', 'r') as message_file:
        message_dict = json.load(message_file)
    message_file.close()
    return message_dict