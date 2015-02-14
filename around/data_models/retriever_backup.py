from data_models.models import Scene, Event, EventHours
import datetime
import math
import django
django.setup()

import logging
#LOG_PATH = ''
LOG_PATH = '/var/log/'
logging.basicConfig(filename=LOG_PATH + 'around_debug.log', level=logging.INFO)

class Retriever:
    def __init__(self):
        self.date = datetime.datetime.utcnow() + datetime.timedelta(hours=-7) #hours needs to be passed in. currently pdt offset from utc
        self.day_start = self.date - datetime.timedelta(hours=)
        self.day_end = datetime.datetime(year=self.date.year, month=self.date.month, day=self.date.day, hour=self.date.hour, minute=self.date.minute, second=self.date.second)
        dt_time_frame = self.midnight - self.date
        self.time_frame = float(dt_time_frame.seconds)/3600
        self.user_location = {}
        self.logging = False
        self.log_str = ''

    def get_events_in_time_frame(self):
        events = []
        for event in Event.objects.all():
            event_plus = EventPlus(event)
            status = self.event_in_time_frame(event_plus)
            include_event = False
            if status == 'is_upcoming':
                event_plus.plus['is_upcoming'] = True
                include_event = True
            elif status == 'is_ongoing':
                event_plus.plus['is_ongoing'] = True
                include_event = True
            if include_event:
                d = self.distance_between_user_and_event(event_plus.event.eventaddress.coordinate())
                event_plus.plus['distance_to_user'] = d
                events.append(event_plus.event_plus_as_dict())
        return sorted(events, key=lambda k:k['distance_to_user'])

    def event_in_time_frame(self, event_plus):
        if self.event_occurs_today(event_plus):
            # must add check for events that within time frame but on the next day
            # example: it is 11:30pm need to add functionality to check for events at 12:00am
            # and after on the next day
            self.log_str = 'now: ' + str(self.date) + '\n'
            event_start = Retriever().parse_event_time(event_plus.event.start)
            event_end = Retriever().parse_event_time(event_plus.event.end)
            if event_end != None and event_start != None:
                dt_start = datetime.timedelta(days=event_start[0], hours=event_start[1]-self.date.hour, minutes=event_start[2]-self.date.minute)
                start_date = self.date + dt_start
                self.log_str += 'start date: ' + str(start_date) + '\n'

                time_frame_date = start_date + datetime.timedelta(hours=-self.time_frame)
                dt_time_frame = self.date - time_frame_date

                self.log_str += 'dt time frame: ' + str(dt_time_frame) + '\n'
                dt_end = datetime.timedelta(days=event_end[0], hours=event_end[1]-self.date.hour, minutes=event_end[2]-self.date.minute)
                end_date = self.date + dt_end
                #check if event is after time frame date and before event end date
                if dt_time_frame.days == 0 and dt_end.days == 0:
                    #check if current time is between time_frame_date and event start date.
                    #if yes, than event is upcoming
                    if dt_start.days == 0:
                        self.log_str += 'event is upcoming\n\n'
                        self.log()
                        return 'is_upcoming'
                    #only option left if for event to be ongoing
                    else:
                        self.log_str += 'event is ongoing. delta days:\n\n'
                        self.log()
                        return 'is_ongoing'
        self.log_str += '\n\n'
        self.log()
        return 'not_in_time_frame'

    def parse_event_time(self, time):
        time = time.lower()
        time = time.replace(' ', '')
        time_comps = time.split(':')
        days = 0
        try:
            hours, minutes = time_comps[0], time_comps[1]
        except IndexError:
            return None
        hours = int(hours)
        if 'am' in minutes:
            minutes = minutes.replace('am', '')
        else:
            minutes = minutes.replace('pm', '')
            hours += 12
            if hours == 24:
                hours = 0
                days = 1
        minutes = int(minutes)
        return [days, hours, minutes]

    def event_occurs_today(self, event_plus):
        #need to add logic to handle case where next day falls in time frame
        day_number = self.date.weekday()
        if day_number == 0:
            return event_plus.event.eventhours.monday == '1'
        elif day_number == 1:
            return event_plus.event.eventhours.tuesday == '1'
        elif day_number == 2:
            return event_plus.event.eventhours.wednesday == '1'
        elif day_number == 3:
            return event_plus.event.eventhours.thursday == '1'
        elif day_number == 4:
            return event_plus.event.eventhours.friday == '1'
        elif day_number == 5:
            return event_plus.event.eventhours.saturday == '1'
        else:
            return event_plus.event.eventhours.sunday == '1'

    def distance_between_user_and_event(self, pt):
        # pt = list[latitude,longitude]
        #distance between two point in meters
        earth_radius = 6371009  #in meters
        latitude1 = math.radians(self.user_location['latitude'])
        latitude2 = math.radians(pt['latitude'])
        d_latitude = latitude1 - latitude2
        d_longitude = math.radians(self.user_location['longitude'] - pt['longitude'])
        k = math.sin(d_latitude/2)**2 + math.cos(latitude1)*math.cos(latitude2)*math.sin(d_longitude/2)**2
        d = earth_radius*2*math.asin(math.sqrt(k))
        return d

    def log(self):
        if self.logging:
            logging.log(self.log_str)
        self.log_str = ''
        return None

class EventPlus:
    def __init__(self, event):
        self.event = event
        self.plus = {'is_ongoing':False,
                     'is_upcoming':False,
                     'distance_to_user':-1,
                     'scene':event.scene.scene_as_dict()}

    def event_plus_as_dict(self):
        d = self.event.event_as_dict()
        for key, value in self.plus.items():
            d[key] = value
        return d
