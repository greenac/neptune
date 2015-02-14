from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import datetime
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
import json
from django.conf import settings
from data_models.models import Scene
from data_models.points_distance import distance_between_points
from data_models.retriever import Retriever, CityGetter, ProfilePicController, EventIconHandler, EventInfo, update_occupancy, \
    first_message
from data_models.models import BanterUser
from data_models.models import Comment
from resources.logger import Logger
from data_models.models import Event
from data_models.models import Log
from data_models.models import Decoder
import copy
import base64

RESPONSE_KEY = 'response'
RESPONSE_USERNAME_AND_PASSWORD_CORRECT = 610
RESPONSE_USERNAME_CORRECT_PASSWORD_WRONG = 611
RESPONSE_NEW_USER_CREATED = 612
RESPONSE_USER_DOES_NOT_EXIST = 613
RESPONSE_COMMENT_SAVE_SUCCESSFUL = 614
RESPONSE_COMMENT_SAVE_FAILURE = 615
RESPONSE_SUPPORTED_CITY = 700
RESPONSE_NON_SUPPORTED_CITY = 701
RESPONSE_PIC_SAVE_SUCCESSFUL = 800
RESPONSE_PIC_SAVE_FAILED = 801
RESPONSE_NO_USER_FOR_PIC_DATA = 802
RESPONSE_PIC_QUERY_SUCCESSFUL = 803
RESPONSE_EVENTS_FETCH_SUCCESSFUL = 900
RESPONSE_FAILED_TO_FETCH_EVENTS = 901
RESPONSE_FAILED_TO_UPDATE_OCCUPANCY = 902
RESPONSE_GENERIC_SUCCESS = 1000
RESPONSE_GENERIC_FAILURE = 1001

LOG_FILE = 'around_debug.log'


@csrf_exempt
def get_scenes_in_view(request):
    try:
        data = json.loads(request.body)
        user_point = data
    except ValueError:
        user_point = {"latitude": 37.79695630000001, "longitude": -122.4002903}
        pass
        # an array [latitude, longitude]
    scenes = []
    for scene in Scene.objects.all():
        if scene.name != '':
            scene_dict = scene.scene_as_dict()
            if scene.sceneaddress.latitude != '':
                scene_point = {'latitude': float(scene.sceneaddress.latitude),
                               'longitude': float(scene.sceneaddress.longitude)}
                distance_from_user = distance_between_points(user_point, scene_point)
                scene_dict['distance_from_user'] = distance_from_user
            events = scene_dict['events']
            for event in events:
                if event['address']['latitude'] != '':
                    event_point = {'latitude': float(event['address']['latitude']),
                                   'longitude': float(event['address']['longitude'])}
                    distance_from_user = distance_between_points(user_point, event_point)
                    event['distance_from_user'] = distance_from_user
            scenes.append(scene_dict)
    response = json.dumps(scenes)
    return HttpResponse(response, content_type="application/json")


@csrf_exempt
def get_current_and_upcoming_events(request):
    start = datetime.datetime.utcnow()
    logger = Logger(LOG_FILE)
    try:
        user_location = json.loads(request.body)
    except ValueError:
        # hard code location for testing in browser
        user_location = {"latitude": 37.79695630000001, "longitude": -122.4002903}
        pass
    try:
        retriever = Retriever()
        retriever.user_location = user_location  # will be passed in request
        events = retriever.get_events_in_time_frame()
    except Exception as e:
        logger.log_error(message='Error retrieving events: ' + str(e))
    try:
        response = json.dumps(events)
    except Exception as e:
        logger.log_error(message='error saving events as json' + str(e))
        pass
    end = datetime.datetime.utcnow()
    delta = end - start
    logger.log_message('time to retrieve events: ' + str(delta.microseconds / (1000.0 * 1000.0)) + ' seconds')
    return HttpResponse(response, content_type="application/json")


@csrf_exempt
def fetch_events(request):
    start = datetime.datetime.utcnow()
    logger = Logger(LOG_FILE)
    response = {RESPONSE_KEY: RESPONSE_FAILED_TO_FETCH_EVENTS}
    retriever = Retriever()
    events = []
    expired_event_ids = []
    try:
        data = json.loads(request.body)
        latitude = data['latitude']
        longitude = data['longitude']
        current_event_ids = data['event_ids']
        user_location = {'latitude': latitude, 'longitude': longitude}
        for_occupancy = data['for_occupancy']
        retriever.for_occupancy = for_occupancy
    except ValueError:
        # hard code location for testing in browser
        user_location = {"latitude": 37.79695630000001, "longitude": -122.4002903}
        current_event_ids = []
        for_occupancy = False
        pass
    try:
        retriever.meta_data_on = True
        retriever.user_location = user_location  # will be passed in request
        retriever.current_event_ids = set(current_event_ids)
        events = retriever.get_events_in_time_frame()
        expired_event_ids = retriever.expired_event_ids
        expired_event_ids = []
    except Exception as e:
        logger.log_error(message='Error retrieving events: ' + str(e))
        response = json.dumps({RESPONSE_KEY: RESPONSE_FAILED_TO_FETCH_EVENTS})
    try:
        response = json.dumps({RESPONSE_KEY: RESPONSE_EVENTS_FETCH_SUCCESSFUL,
                               'day_time_shift': retriever.day_time_shift,
                               'events': events,
                               'expired_events': expired_event_ids,
                               'filter_order': retriever.event_info.filter_order()
        })
    except Exception as e:
        logger.log_error(message='error saving events as json' + str(e))
        pass
    end = datetime.datetime.utcnow()
    delta = end - start
    logger.log_message(
        message='time to retrieve events from fetch_events: ' + str(delta.microseconds / (1000.0 * 1000.0)) + ' seconds')
    return HttpResponse(response, content_type="application/json")


@csrf_exempt
def save_user(request):
    logger = Logger(LOG_FILE)
    create_new_user = True
    user = None
    right_password = False
    try:
        data = json.loads(request.body)
        users = User.objects.filter(email=data['email'])
        if len(users) > 0:
            # user with this email address/username exists. Try and authenticate with password
            user = authenticate(username=data['email'], password=data['password'])
            if user:
                right_password = True
                create_new_user = False
    except Exception as e:
        logger.log_error(message='error loading json data in save_user: ' + str(e))
        pass
    create_banter_user = False
    try:
        if user and right_password:
            user.last_login = datetime.datetime.utcnow()
            user.save()
            banter_user = BanterUser.objects.get(user=user)
            banter_user.date_updated = datetime.datetime.utcnow()
            response = {'response': RESPONSE_USERNAME_AND_PASSWORD_CORRECT,
                        'banter_user': banter_user.banter_user_as_dict()}
        elif user and not right_password:
            response = {'response': RESPONSE_USERNAME_CORRECT_PASSWORD_WRONG}
        else:
            create_banter_user = True
    except Exception as e:
        logger.log_error(message='error saving existing user: ' + str(e))
        create_banter_user = True
        pass
    # user does not exist. make new user. this will only occur if user is
    # social user. If email user call new_email_user before making call to
    # save_user
    if create_new_user:
        user = User.objects.create_user(first_name=data['first_name'],
                                        last_name=data['last_name'],
                                        email=data['email'],
                                        username=data['email'],
                                        password=data['password']
        )
        user.save()
    pic_name = user.email + '.jpeg'
    try:
        pic_string = data['pic']
        pic_path = settings.MEDIA_ROOT + 'profile_pics/' + pic_name
        try:
            with open(pic_path, 'w') as pic_file:
                pic_file.write(base64.decodestring(pic_string))
            pic_file.close()
        except Exception as e:
            logger.log_error(str(e))
            pass
    except Exception as e:
        logger.log_error(message='no base 64 pic for ' + user.email)
    try:
        if create_banter_user:
            banter_user = BanterUser(user=user,
                                     date_updated=datetime.datetime.utcnow(),
                                     type=data['type'],
                                     profile_id=data['profile_id'],
                                     pic=pic_name,
                                     profile_url=data['profile_url'],
            )
            banter_user.save()
        else:
            banter_user = BanterUser.objects.get(user=user)
            banter_user.date_updated = user.last_login
            banter_user.save()
    except Exception as e:
        logger.log_error(message='error creating banter user: ' + str(e))
        pass
    try:
        friends_list = data['friends']
        banter_user.add_friends(friends_list)
        banter_user.save()
    except Exception as e:
        logger.log_error(message='error saving friends list: ' + str(e))
        pass
    try:
        user_as_dict = banter_user.banter_user_as_dict()
        response = {'response': RESPONSE_NEW_USER_CREATED,
                    'banter_user': user_as_dict}

    except Exception as e:
        logger.log_error(message='error saving user as dictionary: ' + str(e))
        pass
    return HttpResponse(json.dumps(response))


@csrf_exempt
def get_user(request):
    try:
        data = json.loads(request.body)
        username = data['email']
        password = data['password']
    except Exception as e:
        logger = Logger(LOG_FILE)
        logger.log_error('error loading json in get_user: ' + str(e))
        pass
    user = authenticate(username=username, password=password)
    if user:
        # user exists
        banter_user = BanterUser.objects.get(user=user)
        response = {'response': RESPONSE_USERNAME_AND_PASSWORD_CORRECT,
                    'banter_user': banter_user.banter_user_as_dict()
        }
    else:
        try:
            # check if user exists but has entered wrong password
            user = User.objects.get(email=username)
            response = {'response': RESPONSE_USERNAME_CORRECT_PASSWORD_WRONG}
        except:
            # user does not exist
            response = {'response': RESPONSE_USER_DOES_NOT_EXIST}
            pass
    return HttpResponse(json.dumps(response))


@csrf_exempt
def comments_for_scenes(request):
    logger = Logger(LOG_FILE)
    try:
        data = json.loads(request.body)
        scene_ids = data['scene_ids']
    except Exception as e:
        logger.log_error(message='error loading comments: ' + str(e))
        pass
    try:
        comments = {}
        for scene_id in scene_ids:
            scene = Scene.objects.get(id=scene_id)
            comments[scene_id] = scene.get_comments()
        response = {'comments': comments}
    except Exception as e:
        logger.log_error(message='Error retrieving comments: ' + str(e))
    return HttpResponse(json.dumps(response))


@csrf_exempt
def save_comment(request):
    load_successful = True
    try:
        data = json.loads(request.body)
        scene_id = data['scene_id']
        scene = Scene.objects.get(id=scene_id)
        commenter_user = User.objects.get(username=data['email'])
        commenter = BanterUser.objects.get(user_id=commenter_user.id)
        comment = data['comment']
    except Exception as e:
        logger = Logger(LOG_FILE)
        logger.log_error('Error loading data in save_comment: ' + str(e))
        load_successful = False
    if load_successful:
        new_comment = Comment(scene=scene,
                              commenter=commenter,
                              comment=comment,
                              date=datetime.datetime.utcnow()
        )
        new_comment.save()
        response_number = RESPONSE_COMMENT_SAVE_SUCCESSFUL
    else:
        response_number = RESPONSE_COMMENT_SAVE_FAILURE
    response = {'response': response_number}
    return HttpResponse(json.dumps(response))


@csrf_exempt
def supported_city(request):
    logger = Logger(LOG_FILE)
    # try:
    # data = json.loads(request.body)
    # logger.log_message(message='current city json: ' + str(data))
    #     city_getter = CityGetter(data['latitude'], data['longitude'])
    #     supported_city = city_getter.make_query()
    # except Exception as e:
    #     logger.log_error(message='Error in current city: ' + str(e))
    #     supported_city = False
    # if supported_city:
    #     response_number = RESPONSE_SUPPORTED_CITY
    # else:
    #     response_number = RESPONSE_NON_SUPPORTED_CITY
    # response = {'response':response_number}
    try:
        data = json.loads(request.body)
        city_getter = CityGetter(data['latitude'], data['longitude'])
        supported_city = city_getter.in_radius()
    except Exception as e:
        logger.log_error(message='Error in current city: ' + str(e))
        supported_city = False
    if supported_city:
        response_number = RESPONSE_SUPPORTED_CITY
    else:
        response_number = RESPONSE_NON_SUPPORTED_CITY
    response = {'response': response_number}
    return HttpResponse(json.dumps(response))


@csrf_exempt
def all_users(request):
    users = User.objects.all()
    complete_users = []
    for user in users:
        user_dict = user.user_as_dict()
        try:
            banter_user = user.banteruser_set.all()[0]
            bu_dict = banter_user.banter_user_as_json()
            bu_dict['email'] = user.email
            complete_users.append({'user': user_dict, 'banter_user': bu_dict})
        except Exception as e:
            logger = Logger(LOG_FILE)
            logger.log_error(message=user.email + ' does not have a banter user. ' + str(e))
    response = json.dumps(complete_users)
    return HttpResponse(response)


@csrf_exempt
def post_profile_pic(request):
    logger = Logger(LOG_FILE)
    try:
        username = request.META['HTTP_USERNAME']
    except Exception as e:
        logger.log_error(message='failed to decode header from request' + str(e))
        return HttpResponse(json.dumps({'response': RESPONSE_NO_USER_FOR_PIC_DATA}))
    users = User.objects.filter(username=username)
    if len(users) > 0:
        # write data to file
        try:
            data = request.body
            pic_controller = ProfilePicController(username=username)
            success = pic_controller.save_pic(data)
        except Exception as e:
            logger.log_error(message='Error saving pic in post body: ' + str(e))
            success = False
        if success:
            response = {'response': RESPONSE_PIC_SAVE_SUCCESSFUL}
        else:
            response = {'response': RESPONSE_PIC_SAVE_SUCCESSFUL}
    else:
        logger.log_message(message='no user that matches username: ' + username)
        response = {'response': RESPONSE_NO_USER_FOR_PIC_DATA}
    return HttpResponse(json.dumps(response))


@csrf_exempt
def get_profile_pic(request):
    logger = Logger(LOG_FILE)
    try:
        data = json.loads(request.body)
        username = data['username']
    except Exception as e:
        logger.log_error('failed to decode json from get profile pic request' + str(e))
        response = HttpResponse()
        response['response'] = RESPONSE_NO_USER_FOR_PIC_DATA
        return response
    users = User.objects.filter(username=username)
    if len(users) > 0:
        # read from pic file
        pic_controller = ProfilePicController(username=username)
        pic_data = pic_controller.get_pic()
        if pic_data:
            response = HttpResponse(pic_data)
            response['username'] = username
            response['response'] = RESPONSE_PIC_SAVE_SUCCESSFUL
        else:
            response = HttpResponse(json.dumps(data))
            response['response'] = RESPONSE_NO_USER_FOR_PIC_DATA
    else:
        response = HttpResponse(json.dumps(data))
        response['response'] = RESPONSE_NO_USER_FOR_PIC_DATA
    return response


@csrf_exempt
def set_occupancy(request):
    try:
        logger = Logger(LOG_FILE)
        data = json.loads(request.body)
        event_id = data['event_id']
        status = data['status']
        username = data['username']
        event = Event.objects.get(id=event_id)
        event.type_ext = status
        logger.log_message('received event ' + str(event_id) + ' and status ' + status + ' by user ' + username)
        event.save()
        # Tracking Occupancy
        new_log = Log(user=username,
                      function='occupancy',
                      message='event_id=' + str(event_id) + ' status=' + status,
                      timestamp=datetime.datetime.utcnow()
        )
        new_log.save()
        # End Tracking Occupancy
        response = {'response': RESPONSE_EVENTS_FETCH_SUCCESSFUL}
        #logger.log_message(response)
    except Exception as e:
        logger.log_error(message='Error updating occupancy status: ' + str(e))
        response = {'response': RESPONSE_FAILED_TO_UPDATE_OCCUPANCY}
    return HttpResponse(json.dumps(response))


@csrf_exempt
def get_occupancy(request):
    logger = Logger(LOG_FILE)
    try:
        data = json.loads(request.body)
        event_ids = data['event_ids']
        occupancies = {}
        # logger.log_message('Received '+str(event_ids))
        for event_id in event_ids:
            event = Event.objects.get(id=event_id)
            occupancies[event_id] = event.occupancy_status()
        response = {'occupancies': occupancies}
    except Exception as e:
        logger.log_error('Error retrieving events: ' + str(e))
        response = {'occupancies': RESPONSE_FAILED_TO_UPDATE_OCCUPANCY}
    return HttpResponse(json.dumps(response))


@csrf_exempt
def event_icon_urls(request):
    logger = Logger(LOG_FILE)
    response_code = RESPONSE_GENERIC_SUCCESS
    response = {}
    try:
        handler = EventIconHandler()
        response['event_icon_urls'] = handler.icon_urls()
    except Exception as e:
        logger.log_error('ERROR retrieving event icons: ' + str(e))
        response_code = RESPONSE_GENERIC_FAILURE
    response['response'] = response_code
    return HttpResponse(json.dumps(response))


@csrf_exempt
def filter_order(request):
    response = {}
    try:
        event_info = EventInfo()
        response['filter_order'] = event_info.filter_order()
        response['response'] = RESPONSE_GENERIC_SUCCESS
    except Exception as e:
        logger = Logger(LOG_FILE)
        logger.log_error(message='Error in retrieving filter order')
        response['response'] = RESPONSE_GENERIC_FAILURE
        pass
    return HttpResponse(json.dumps(response))


@csrf_exempt
def occupancy_today(request):
    return HttpResponse('Updated Occupancy for ' + update_occupancy())


@csrf_exempt
def get_decoder_name_unique(request):
    logger = Logger(LOG_FILE)
    try:
        data = json.loads(request.body)
        name_ids = data['names']
        # logger.log_message('Received' + str(data))
    except Exception as e:
        # logger.log_message('Error block 1' + str(e))
        response = {'decoder': 903}
    try:
        decoder = {}
        for name_id in name_ids:
            mydata = Decoder.objects.get(name=name_id)
            decoder[name_id] = mydata.value
        response = {'decoder': decoder}
        # logger.log_message('Sending' + str(response))
    except Exception as e:
        logger.log_error('Error retrieving name: ' + str(e))
        response = {'decoder': RESPONSE_FAILED_TO_UPDATE_OCCUPANCY}
    return HttpResponse(json.dumps(response))


@csrf_exempt
def get_decoder_name_multiple(request):
    logger = Logger(LOG_FILE)
    try:
        data = json.loads(request.body)
        name_ids = data['names']
        # logger.log_message('Received' + str(data))
    except Exception as e:
        logger.log_error('Error block 1' + str(e))
        response = {'decoder': 903}
    try:
        decoder_out = {}
        decoder_in = {}
        # logger.log_message('Name_ids[0]' + str(name_ids))
        for name_id in name_ids:
            result_set = Decoder.objects.filter(name=name_id)
            for name in result_set:
                decoder_in[name.field] = name.value
            decoder_out[name_id] = decoder_in
        response = {'decoder': decoder_out}
        # logger.log_message('Sending' + str(response))
    except Exception as e:
        logger.log_error('Error retrieving name: ' + str(e))
        response = {'decoder': RESPONSE_FAILED_TO_UPDATE_OCCUPANCY}
    return HttpResponse(json.dumps(response))


@csrf_exempt
def get_decoder_range(request):
    logger = Logger(LOG_FILE)
    try:
        data = json.loads(request.body)
        range_limits = data['range']
        # logger.log_message('range_limits' + str(range_limits))
    except Exception as e:
        logger.log_error('Error block 1' + str(e))
        response = {'decoder': 903}
    try:
        min = range_limits[0]
        max = range_limits[1]
        decoder_out = {}
        decoder_in = {}
        # logger.log_message('range_limits[0]' + str(min))
        #logger.log_message('range_limits[1]' + str(max))
        #row = Decoder.objects.filter(range__gte=min,range__lte=max).order_by('range','name','field')
        row = Decoder.objects.filter(range__gte=min, range__lte=max).order_by('name', 'field')
        #logger.log_message('row: ' + str(row))
        previous = ''
        for rec in row:
            #logger.log_message('outter loop ' + rec.name+' '+rec.field+' '+rec.value)
            if previous != rec.name:
                if previous != '':
                    decoder_out[previous] = copy.deepcopy(decoder_in)
                    decoder_in = {}
                    #logger.log_message('inner loop: ' +str(previous)+ ' ' +str(decoder_in))
                previous = rec.name
            decoder_in[rec.field] = rec.value
        decoder_out[rec.name] = copy.deepcopy(decoder_in)
        response = {'decoder': decoder_out}
        #logger.log_message('Sending' + str(response))
        #logger.log_message('range_limits[0]' + str(min))
        #logger.log_message('range_limits[1]' + str(max))
        row = Decoder.objects.filter(range__gte=min, range__lte=max)
        #logger.log_message('row: ' + str(row))
        previous = ''
        for rec in row:
            #logger.log_message('outter loop ' + rec.name + ' ' + rec.field + ' ' + rec.value)
            if previous != rec.name:
                if previous != '':
                    decoder_out[previous] = copy.deepcopy(decoder_in)
                    decoder_in = {}
                    # logger.log_message('inner loop: ' +str(previous)+ ' ' +str(decoder_in))
                previous = rec.name
            decoder_in[rec.field] = rec.value
        decoder_out[rec.name] = copy.deepcopy(decoder_in)
        response = {'decoder': decoder_out}
        # logger.log_message('Sending' + str(response))
    except Exception as e:
        logger.log_error('Error retrieving name: ' + str(e))
        response = {'decoder': RESPONSE_FAILED_TO_UPDATE_OCCUPANCY}
    return HttpResponse(json.dumps(response))


@csrf_exempt
def opening_message(request):
    logger = Logger(LOG_FILE)
    response_number = RESPONSE_GENERIC_SUCCESS
    message = {}
    try:
        message = first_message()
    except Exception as e:
        logger.log_error('Error in opening message ' + str(e))
        response_number = RESPONSE_GENERIC_FAILURE
        pass
    response = {'response': response_number}
    for k, v in message.items():
        response[k] = v
    return HttpResponse(json.dumps(response))
