import os, sys, urllib, json, threading
import data_models.models as dm
import spreadsheet_files.database_creator as dc
import datetime
import django
import os, sys

django.setup()
sys.path.append(os.path.join(os.path.dirname(__file__), 'around'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'around.settings'
from django.conf import settings


class ParseMerchant:
    def __init__(self):
        self.time_zone_shift = -8
        self.constants = dc.Constants()
        self.file_reader = dc.FileReader()
        for file in self.file_reader.all_files():
            self.file_reader.read_fields(file)
        self.data_merchant = dc.DataMerchant()
        # self.base_merchant = dm.Merchant()
        self.scene = dm.Scene()
        self.event = dm.Event()
        self.parse_event_hours = {}
        self.parse_scene_hours = {}

    def run_parse_merchant(self):
        for merchant in self.file_reader.merchants:
            self.data_merchant = merchant
            self.save_scene()
            self.make_events()
        return None

    def save_scene(self):
        try:
            self.scene = dm.Scene()
            self.scene.type = self.data_merchant.all_fields[self.constants.type].lower()
            self.scene.name = self.data_merchant.all_fields[self.constants.name]
            scene = self.get_scene()
            if scene:
                self.scene = scene
                print self.scene.name + ' already in database. overwriting scene information.'
            else:
                print self.scene.name + ' not in database. creating new entry.'
            self.scene.contact = self.data_merchant.all_fields[self.constants.contact]
            self.scene.logo_path = self.data_merchant.all_fields[self.constants.logo]
            self.scene.phone_number = self.data_merchant.all_fields[self.constants.phone_number]
            self.scene.email = self.data_merchant.all_fields[self.constants.email]
            self.scene.description = self.data_merchant.all_fields[self.constants.description]
            self.scene.website_url = self.data_merchant.all_fields[self.constants.website]
            self.scene.facebook_url = self.data_merchant.all_fields[self.constants.facebook]
            self.scene.yelp_url = self.data_merchant.all_fields[self.constants.yelp]
            self.scene.twitter_url = self.data_merchant.all_fields[self.constants.twitter]
            self.scene.open_table_url = self.data_merchant.all_fields[self.constants.open_table]
            self.scene.instagram_url = ''
            self.scene.message = self.data_merchant.all_fields[self.constants.message]
            self.scene.time_offset = self.time_zone_shift
            # save scene hours
            self.make_scene_hours()
            self.scene.monday = self.clean_commas(self.parse_scene_hours[self.constants.days[0]])
            self.scene.tuesday = self.clean_commas(self.parse_scene_hours[self.constants.days[1]])
            self.scene.wednesday = self.clean_commas(self.parse_scene_hours[self.constants.days[2]])
            self.scene.thursday = self.clean_commas(self.parse_scene_hours[self.constants.days[3]])
            self.scene.friday = self.clean_commas(self.parse_scene_hours[self.constants.days[4]])
            self.scene.saturday = self.clean_commas(self.parse_scene_hours[self.constants.days[5]])
            self.scene.sunday = self.clean_commas(self.parse_scene_hours[self.constants.days[6]])
            self.parse_scene_hours = {}
            # save scene address
            self.scene.address = self.get_scene_address(0)
            self.scene.city = self.get_scene_address(1)
            self.scene.state = self.get_scene_address(2)
            self.scene.zip = self.get_scene_address(3)
            self.scene.latitude = self.get_scene_address(4)
            self.scene.longitude = self.get_scene_address(5)
            self.scene.country = 'united states'
            self.scene.save()
            print 'saving scene: ' + self.scene.name
        except Exception as e:
            print 'error in scene ' + str(e)
        return None

    def does_scene_exist(self):
        try:
            dm.Scene.objects.get(name=self.scene.name, type=self.scene.type)
            scene_exists = True
        except Exception:
            scene_exists = False
            pass
        return scene_exists

    def get_scene(self):
        scene = None
        try:
            scene = dm.Scene.objects.get(name=self.scene.name, type=self.scene.type)
        except Exception as e:
            print 'no scene with name ' + self.scene.name + ' ' + str(e)
        return scene

    def make_scene_hours(self):
        for day in self.constants.scene_days:
            hours = self.data_merchant.all_fields[day]
            self.insert_hour(day, hours, 'scene')
        return None

    def insert_hour(self, day, hours, hour_type):
        the_day = self.get_day(day)
        if the_day:
            if hour_type == 'scene':
                if the_day in self.parse_scene_hours:
                    current_time = self.parse_scene_hours[the_day]
                    if current_time != '':
                        current_time += ',' + hours
                    self.parse_scene_hours[the_day] = current_time
                else:
                    self.parse_scene_hours[the_day] = hours
            elif hour_type == 'event':
                if the_day in self.parse_event_hours:
                    current_time = self.parse_event_hours[the_day]
                    if current_time != '':
                        current_time += ',' + hours
                    self.parse_event_hours[the_day] = current_time
                else:
                    self.parse_event_hours[the_day] = hours
        return None

    def clean_commas(self, time_string):
        if len(time_string) > 0:
            if time_string[0] == ',':
                time_string = time_string[1:len(time_string)]
            if len(time_string) > 0:
                if time_string[len(time_string) - 1] == ',':
                    time_string = time_string[0:len(time_string) - 1]
        return time_string

    def save_scene_hours(self):
        scene_hours = dm.SceneHours()
        scene_hours.scene = self.scene
        scene_hours.save()
        self.parse_scene_hours = {}
        return None

    def save_scene_address(self):
        scene_address = dm.SceneAddress()
        scene_address.scene = self.scene

        scene_address.save()
        return None

    def get_scene_address(self, index):
        field = self.constants.address[index]
        try:
            return self.data_merchant.all_fields[field]
        except KeyError:
            return ''

    def make_events(self):
        # gives an array of food truck or happy hour events
        try:
            events = self.data_merchant.events
        except KeyError:
            print 'Error: no value for' + type
            return None
        if events:
            for event in events:
                self.save_event(event)
        return None

    def save_event(self, event):
        self.event = dm.Event()
        self.event.scene = self.scene
        self.event.description1 = ''
        self.event.description2 = ''
        self.event.type = self.parse_event_type(event.all_fields[self.constants.type])
        self.event.type_ext = '0'
        self.event.message = event.all_fields[self.constants.message]
        self.set_start_date(event)
        self.set_end_date(event)
        print 'saving event of type ' + self.event.type + ' from scene ' + self.event.scene.name
        self.set_event_address(event)
        self.set_event_hours(event)
        self.event.save()
        return None

    def set_start_date(self, event):
        time_string = event.all_fields[self.constants.start]
        hours, minutes, meridiem = self.parse_time(time_string)
        hours = self.hours_with_meridiem(hours, meridiem)
        year, month, day = self.parse_date(event)
        if year == 0 and month == 0 and day == 0:
            # event is recurring. save time as time object under event leaving
            # date time field null
            start_time = datetime.time(hours, minutes)
            self.event.recurring_start = start_time
        else:
            # event is a one time event. set event's recurring start date
            start_date = datetime.datetime(year, month, day, hours, minutes)
            self.event.start = start_date
        return None

    def set_end_date(self, event):
        time_string = event.all_fields[self.constants.end]
        hours, minutes, meridiem = self.parse_time(time_string)
        hours = self.hours_with_meridiem(hours, meridiem)
        year, month, day = self.parse_date(event)
        if year == 0 and month == 0 and day == 0:
            # event is recurring. save time
            end_time = datetime.time(hours, minutes)
            self.event.recurring_end = end_time
            self.event.ends_next_day = self.does_recurring_event_end_next_day()
        else:
            # event is a one time event. set event's recurring end date
            end_date = datetime.datetime(year, month, day, hours, minutes)
            time_diff = end_date - self.event.start
            if time_diff.days < 0:
                end_date = end_date + datetime.timedelta(days=abs(time_diff.days))
            self.event.end = end_date
        return None

    def does_recurring_event_end_next_day(self):
        end_hour = self.event.recurring_end.hour
        start_hour = self.event.recurring_start.hour
        if end_hour - start_hour >= 0:
            # event ends on same day it started
            return False
        return True

    def hours_with_meridiem(self, hours, meridiem):
        if meridiem == 'pm' and hours != 12:
            hours += 12
            if hours >= 24:
                hours -= 24
        elif meridiem == 'am' and hours == 12:
            hours = 0
        return hours

    def parse_date(self, event):
        year, month, day = 0, 0, 0
        try:
            day = int(event.all_fields[self.constants.day])
            month = int(event.all_fields[self.constants.month])
            year = int(event.all_fields[self.constants.year])
        except ValueError:
            year, month, day = 0, 0, 0
            pass
        return year, month, day

    def parse_time(self, time_string):
        time_string = time_string.lower()
        parts = time_string.split(':')
        hours = parts[0]
        parts = parts[1].split(' ')
        minutes = parts[0]
        meridiem = parts[1]
        return int(hours), int(minutes), meridiem

    def set_event_address(self, event):
        # event address not set up use scene address
        if event.all_fields[self.constants.address[0]] == '' and self.constants.address[4] not in event.all_fields.keys():
            self.event.address = self.scene.sceneaddress.address
            self.event.city = self.scene.sceneaddress.city
            self.event.state = self.scene.sceneaddress.state
            self.event.zip = self.scene.sceneaddress.zip
        else:
            self.event.address = event.all_fields[self.constants.address[0]]
            self.event.city = event.all_fields[self.constants.address[1]]
            self.event.state = event.all_fields[self.constants.address[2]]
            self.event.zip = event.all_fields[self.constants.address[3]]
        self.country = 'united states'
        return None

    def set_event_hours(self, event):
        self.event.monday = event.all_fields[self.constants.days[0]]
        self.event.tuesday = event.all_fields[self.constants.days[1]]
        self.event.wednesday = event.all_fields[self.constants.days[2]]
        self.event.thursday = event.all_fields[self.constants.days[3]]
        self.event.friday = event.all_fields[self.constants.days[4]]
        self.event.saturday = event.all_fields[self.constants.days[5]]
        self.event.sunday = event.all_fields[self.constants.days[6]]
        return None

    def get_day(self, day):
        day = day.lower()
        if self.constants.days[0] in day:
            return self.constants.days[0]
        elif self.constants.days[1] in day:
            return self.constants.days[1]
        elif self.constants.days[2] in day:
            return self.constants.days[2]
        elif self.constants.days[3] in day:
            return self.constants.days[3]
        elif self.constants.days[4] in day:
            return self.constants.days[4]
        elif self.constants.days[5] in day:
            return self.constants.days[5]
        elif self.constants.days[6] in day:
            return self.constants.days[6]
        else:
            return None

    def parse_event_type(self, event_type):
        event_type = event_type.lower()
        if event_type == 'food truck':
            return 'food_truck'
        elif event_type == 'happy hour':
            return 'happy_hour'
        else:
            return event_type

    def insert_value(self, value):
        if value == None:
            return ''
        else:
            return value.lower()
