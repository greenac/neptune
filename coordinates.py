import os,sys,urllib, json, threading
import django
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'around'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'around.settings')
django.setup()

from data_models.models import Scene, Event

class GetCoordinates:
        def __init__(self):
            self.counter = 0
            self.range = 10
            self.delta_t = 2
            self.scenes = Scene.objects.all()
            # banter's key
            self.api_key = 'AIzaSyDKZ_L40Thpm3u_uLMbOm1v3U_Pc1X9bJs'
            # andre's key
            #self.api_key = 'AIzaSyCF5B1AQhCZ8l9r-H1-wEbUvMP3yWDKGk4'
            self.base_url = 'https://maps.googleapis.com/maps/api/geocode/json?'
            print('number of scenes', len(self.scenes))

        def save_chords(self):
            try:
                scenes = self.scenes[self.counter:self.counter + self.range]
            except IndexError:
                scenes = self.scenes[self.counter:len(self.scenes)]
                pass
            for scene in scenes:
                print('processing scene number', scene.id)
                if scene.type != '' and not scene.has_coordinate():
                    print(scene.name + ' does not have coordinates')
                    address = Address(address=scene.address,
                                      city=scene.city,
                                      state=scene.state,
                                      zip=scene.zip,
                                      country=scene.country
                    )
                    # check if the scene has an address
                    if address.has_address():
                        print('scene address' + str(address))
                        coords = self.get_chords(self.make_url(address))
                        scene.latitude = coords['latitude']
                        scene.longitude = coords['longitude']
                        scene.save()
                else:
                    print(scene.name + ' has coordinates lat:' + scene.latitude + ' long: ' + scene.longitude)
                events = scene.event_set.all()
                print(scene.name, 'has', len(events), 'events')
                event_counter = 1
                for event in events:
                    print('processing event', event_counter)
                    if not event.has_coordinate():
                        # event does not have coordinates
                        # check if scene has coordinates. If yes, then copy them to event
                        if scene.has_coordinate():
                            print("copying scene's coordinates to event")
                            event.latitude = scene.latitude
                            event.longitude = scene.longitude
                            # make query to google to retrieve coordinates
                        else:
                            print("making query for events's coordinates")
                            address = Address(address=event.address,
                                              city=event.city,
                                              state=event.state,
                                              zip=event.zip,
                                              country=event.country,
                                              is_scene=False
                            )
                            print('event address: ' + str(address))
                            coords = self.get_chords(self.make_url(address))
                            event.longitude = coords['longitude']
                            event.latitude = coords['latitude']
                        event.save()
                    else:
                        print('event already has coordinate lat:', event.latitude, event.longitude)
                    event_counter += 1
                print('\n')
                self.counter += 1
            if self.counter < len(self.scenes):
                self.run()
            return None

        def scene_has_chords(self, scene):
            if scene.latitude == '' and scene.longitude == '':
                return True
            return False

        def get_chords(self, url):
            request = urllib.request.Request(url)
            response = urllib.request.urlopen(request)
            data = json.loads(response.read().decode('utf8'))
            try:
                latitude = data['results'][0]['geometry']['location']['lat']
                longitude = data['results'][0]['geometry']['location']['lng']
            except IndexError:
                latitude = ''
                longitude = ''
            return {'latitude':latitude, 'longitude':longitude}

        def make_url(self, address):
            url = self.base_url + self.make_query_parameters(address)
            print('url:', url)
            return self.base_url + self.make_query_parameters(address)

        def make_query_parameters(self, address):
            if address.is_scene:
                if address.has_address():
                    address_string = 'address=' + address.address.replace(' ', '+') + ',+'
                    address_string = address_string.replace('&', 'and')
                    address_string += address.city.replace(' ', '+') + ',+'
                    address_string += address.state.replace(' ', '+') + '&key=' + self.api_key
            else:
                address_string = 'address=' + address.address.replace(' ', '+') + ',+'
                address_string = address_string.replace('&', 'and')
                address_string += address.city.replace(' ', '+') + ',+'
                address_string += address.state.replace(' ', '+') + '&key=' + self.api_key
            return address_string

        def run(self):
                timer = threading.Timer(self.delta_t, lambda:self.save_chords())
                timer.start()
                return None

class Address:
    def __init__(self, address, city, state, zip, country, is_scene=True):
        self.address = address
        self.city = city
        self.state = state
        self.zip = zip
        self.country = country
        self.is_scene = is_scene

    def has_address(self):
        return self.address != '' and self.city != '' and self.state != ''

    def __str__(self):
        return self.address + ' ' + self.city + ', ' + self.state + ' ' + self.zip