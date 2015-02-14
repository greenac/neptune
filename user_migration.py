import django
import os, sys
import json
import datetime
import MySQLdb
import urllib2

from django.conf import settings

sys.path.append(os.path.join(os.path.dirname(__file__), 'around'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'around.settings'
django.setup()

from data_models.models import BanterUser
from django.contrib.auth.models import User

class UsersToJson:
    def __init__(self):
        self.user_file_name = 'users.json'
        self.users_path = self.current_dir_path() + 'user_json_files/' + self.user_file_name

    def current_dir_path(self):
        current_path = os.path.dirname(os.path.abspath(__file__))
        if current_path[len(current_path)-1] != '/':
            current_path += '/'
        return current_path

    def server_endpoints(self):
        urls = ['http://54.172.170.219/',
                'http://54.235.81.108/',
                'http://54.83.51.249/'
                ]
        return urls

    def users_from_servers(self):
        urls = self.server_endpoints()
        for url in urls:
            # get users from each production database
            try:
                response = urllib2.urlopen(url + 'data_models/all_users/')
                users_data = json.loads(response.read())
                self.save_to_file(users_data)
            except Exception as e:
                print 'ERROR connecting to: ' + url + ' .Failed with error: ' + str(e)
        return None

    def save_to_file(self, users):
        with open(self.users_path, 'r') as user_file:
            try:
                prev_users = json.load(user_file)
            except ValueError:
                prev_users = []
        user_file.close()
        users = users + prev_users
        with open(self.users_path, 'w') as user_file:
            json.dump(users, user_file)
        user_file.close()
        return None

    def load_users_from_file_to_db(self):
        with open(self.users_path, 'r') as users_file:
            complete_users = json.load(users_file)
        users_file.close()
        for complete_user_dict in complete_users:
            user_dict = complete_user_dict['user']
            save_successful = self.save_user(user_dict)
            if save_successful:
                bu_dict = complete_user_dict['banter_user']
                self.save_banter_user(bu_dict)
        return None

    def user_as_dict(self, user):
        user_dict = {'id':user.id,
                     'password':user.password,
                     'last_login':self.date_to_dict(user.last_login),
                     'is_superuser':user.is_superuser,
                     'username':user.username,
                     'first_name':user.first_name,
                     'last_name':user.last_name,
                     'email':user.email,
                     'is_staff':user.is_staff,
                     'is_active':user.is_active,
                     'date_joined':self.date_to_dict(user.date_joined)
        }
        return user_dict

    def banter_user_as_dict(self, banter_user):
        bu_dict = {'id':banter_user.id,
                   'user_id':banter_user.user_id,
                   'date_updated':self.date_to_dict(banter_user.date_updated),
                   'type':banter_user.type,
                   'profile_id':banter_user.profile_id,
                   'notification_token':banter_user.notification_token,
                   'profile_url':banter_user.profile_url,
                   'pic':banter_user.pic,
        }
        return bu_dict

    def user_from_dict(self, user_dict):
        user = User(last_login=self.dict_to_date(user_dict['last_login']),
                    is_superuser=user_dict['is_superuser'],
                    username=user_dict['username'],
                    first_name=user_dict['first_name'],
                    last_name=user_dict['last_name'],
                    email=user_dict['email'],
                    is_staff=user_dict['is_staff'],
                    is_active=user_dict['is_active'],
                    date_joined=self.dict_to_date(user_dict['date_joined'])
        )
        return user

    def banter_user_from_dict(self, bu_dict, user):
        banter_user = BanterUser(user=user,
                                 date_updated=self.dict_to_date(bu_dict['date_updated']),
                                 type=bu_dict['type'],
                                 profile_id=bu_dict['profile_id'],
                                 notification_token=bu_dict['notification_token'],
                                 profile_url=bu_dict['profile_url'],
                                 pic=bu_dict['pic']
        )
        return banter_user

    def save_user_password(self, user, password):
        # used to save hashed password directly to database to avoid double hashing
        try:
            connection = MySQLdb.connect(host='localhost',
                                         user='andre',
                                         passwd='Perhar@6221',
                                         db='around_db')
        except:
            print 'could not connect to database'
        #query = 'UPDATE auth_user SET first_name="' + 'stems' + '" WHERE id=' + str(user.id)
        cursor = connection.cursor()
        try:
            cursor.execute("""UPDATE auth_user SET first_name=%s WHERE id=%s""", ('bb king', user.id))
            cursor.close()
            connection.commit()
            user.save()
        except Exception as e:
            print 'could not save ' + user.email + "'s password: " + password
            print 'Error: ' + str(e)
            connection.rollback()
        connection.close()
        return None

    def date_to_dict(self, date):
        date_dict = {'year':date.year,
                     'month':date.month,
                     'day':date.day,
                     'hour':date.hour,
                     'minute':date.minute,
                     'second':date.second
        }
        return date_dict

    def dict_to_date(self, date_dict):
        date = datetime.datetime(date_dict['year'],
                                 date_dict['month'],
                                 date_dict['day'],
                                 date_dict['hour'],
                                 date_dict['minute'],
                                 date_dict['second']
        )
        return date

    def string_from_date(self, date):
        year = str(date.year)
        month = self.add_zero_to_date_time_string(str(date.month))
        day = self.add_zero_to_date_time_string(str(date.day))
        hour = self.add_zero_to_date_time_string(str(date.hour))
        minute = self.add_zero_to_date_time_string(str(date.minute))
        second = self.add_zero_to_date_time_string(str(date.second))
        return year + '-' + month + '-' + day + ' ' + hour + ':' + minute + ':' + second

    def add_zero_to_date_time_string(self, value):
        if len(value) == 1:
            value = '0' + value
        return value

    def string_from_bool(self, value):
        if value:
            return '1'
        return '0'

    def user_in_db(self, user):
        try:
            User.objects.get(email=user.email)
            return True
        except:
            return False

    def connection(self):
        connection = MySQLdb.connect(host='localhost',
                                     user='andre',
                                     passwd='Perhar@6221',
                                     db='around_db')
        return connection

    def is_user_in_db(self, email):
        user_in_db = False
        query = """SELECT * FROM auth_user WHERE email='%s'""" % email
        conn = self.connection()
        cursor = conn.cursor()
        data = []
        try:
            cursor.execute(query)
            data = cursor.fetchall()
        except Exception as e:
            print 'ERROR querying database for user ' + email + '. Failed with error: ' + str(e)
        conn.close()
        if len(data) > 0:
            user_in_db = True
        return user_in_db

    def save_user(self, user):
        success = True
        email = user['email']
        if self.is_user_in_db(email):
            print 'user with email: ' + email + ' is already in database'
            success = False
        else:
            last_login = self.string_from_date(self.dict_to_date(user['last_login']))
            date_joined = self.string_from_date(self.dict_to_date(user['date_joined']))
            is_superuser = self.string_from_bool(user['is_superuser'])
            is_staff = self.string_from_bool(user['is_staff'])
            is_active = self.string_from_bool(['is_active'])
            query = """INSERT INTO auth_user
                        (password,last_login,is_superuser,username,first_name,last_name,email,is_staff,is_active,date_joined)
                        VALUES ("%s","%s",%s,"%s","%s","%s","%s",%s,%s,"%s")""" % \
                    (user['password'],
                     last_login,
                     is_superuser,
                     user['username'],
                     user['first_name'],
                     user['last_name'],
                     email,
                     is_staff,
                     is_active, date_joined
                    )
            connection = self.connection()
            cursor = connection.cursor()
            try:
                cursor.execute(query)
                connection.commit()
            except Exception as e:
                print query
                print 'Error: ' + str(e) + '\n'
                connection.rollback()
                success = False
            connection.close()
        return success

    def user_id_for_email(self, email):
        id_num = -1
        if self.is_user_in_db(email):
            conn = self.connection()
            cursor = conn.cursor()
            query = """SELECT * from auth_user WHERE email='%s'""" % email
            try:
                cursor.execute(query)
                data = cursor.fetchall()
                id_num = data[0][0]
                print 'user: ' + email + ' id #: ' + str(id_num)
            except Exception as e:
                print 'ERROR: in query for user id. Failed with error: ' + str(e)
        return id_num

    def save_banter_user(self, banter_user):
        user_email = banter_user['email']
        user_id = self.user_id_for_email(user_email)
        if user_id != -1:
            date_updated = self.string_from_date(self.dict_to_date(banter_user['date_updated']))
            query ="""INSERT INTO data_models_banteruser
                      (user_id,date_updated,type,profile_id,notification_token,profile_url,pic)
                      VALUES (%s, '%s', '%s', '%s', '%s', '%s', '%s')""" % \
                        (user_id,
                         date_updated,
                         banter_user['type'],
                         banter_user['profile_id'],
                         banter_user['notification_token'],
                         banter_user['profile_url'],
                         banter_user['pic']
                        )
            conn = self.connection()
            cursor = conn.cursor()
            try:
                cursor.execute(query)
                conn.commit()
            except Exception as e:
                print query
                print 'Error: ' + str(e) + '\n'
                conn.rollback()
            conn.close()
        return None


