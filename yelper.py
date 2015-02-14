import json
import urllib2
import oauth2
from httplib2 import iri2uri

SMALL_IMAGE_KEY = 'rating_img_url_small'

def iri_to_uri(iri):
    """Transform a unicode iri into a ascii uri."""
    if not isinstance(iri, unicode):
        raise TypeError('iri %r should be unicode.' % iri)
    return bytes(iri2uri(iri))

class Yelper:
    def __init__(self, business_url):
        # self.consumer_key = 'I30D7AhAgXX_JGGAKNAATQ'
        # self.consumer_secret = 'VAtVZ-l8WRFe9pM2-EH-J29Ss1c'
        # self.token = 'bhGBl5_OUc2kF1tt3f3ddEjAj1SU1OOD'
        # self.token_secret = 'YNT6-i_q661ZurwpleNPiutBtuw'

        # back up info
        self.consumer_key = 'kXRfjx2uNPS0CV-dCL1cqg'
        self.consumer_secret = 'hwy-Plqbq0_6VXQbh2mNxFqqKHc'
        self.token = '4XbEVUnGYeO8lUSJ6gGq1kaRN9HIwmEu'
        self.token_secret = 'AJC45U8kQ3OL9ykAGqJPtKHG8Vk'
        self.business_url = business_url
        self.business_id = self.business_id_from_url()
        self.host = 'api.yelp.com'

    def business_id_from_url(self):
        url_parts = self.business_url.split('/')
        try:
            return url_parts[len(url_parts)-1]
        except IndexError:
            return None

    def request_by_business_id(self):
        if self.business_id:
            print 'id: ' + self.business_id
            #url = u' '.join(('http://', self.host, '/v2/business/', self.business_id)).encode('utf-8').strip()
            url = 'http://' + self.host + '/v2/business/' + iri_to_uri(unicode(self.business_id))
            print 'url: ' + self.business_url
            print 'api-url: '+ url
            consumer = oauth2.Consumer(self.consumer_key, self.consumer_secret)
            oauth_request = oauth2.Request('GET', url, {})
            oauth_request.update({
                'oauth_nonce':oauth2.generate_nonce(),
                'oauth_timestamp':oauth2.generate_timestamp(),
                'oath_token':self.token,
                'oath_consumer_key':self.consumer_key
            })
            token = oauth2.Token(self.token, self.token_secret)
            oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
            signed_url = oauth_request.to_url()
            try:
                conn = urllib2.urlopen(signed_url, timeout=30)
            except urllib2.HTTPError as e:
                print 'Error: HTTPError: ' + str(e)
                return None
            try:
                response = json.loads(conn.read())
            finally:
                conn.close()
            return response

    def make_query(self, param):
        response = ''
        if param == SMALL_IMAGE_KEY:
            response = self.request_by_business_id()
        return response

    def get_small_image_url(self):
        response = self.make_query(SMALL_IMAGE_KEY)
        try:
            return response[SMALL_IMAGE_KEY]
        except KeyError as e:
            print('key error: ' + str(e))
            print 'No image value for ' + self.business_id
            return None
        except TypeError as e:
            print('type error: ' + str(e))
            print 'Error: request returned None object'
            return None