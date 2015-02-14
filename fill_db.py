# import os,sys
#import django
#django.setup()
#
# sys.path.append(os.path.join(os.path.dirname(__file__), 'around'))
#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'around.settings')

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'around'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'around.settings'
from django.conf import settings
import data_models.models as dm

from db_filler import ParseMerchant
from yelper import Yelper

parser = ParseMerchant()
parser.run_parse_merchant()


yelper = Yelper('')
counter = 0
scenes = dm.Scene.objects.all()
for scene in scenes:
    print '\ncount: ' + str(counter)
    counter += 1
    yelper.business_url = scene.yelp_url
    yelper.business_id = yelper.business_id_from_url()
    image_url = yelper.get_small_image_url()
    if image_url != None:
        print 'image url: ' + image_url
        scene.yelp_image_url = image_url
        scene.save()
