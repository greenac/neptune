import django
#django.setup()

class FileReader:
    def __init__(self):
        self.file_base_path = 'spreadsheet_files/'
        self.merchant_file = 'merchants.csv'
        self.event_file = 'events.csv'
        self.deliminator = '^'
        self.merchants = []
        self.constants = Constants()

    def all_files(self):
        return [self.merchant_file, self.event_file]

    def get_object_for_file(self, file_name):
        if file_name == self.merchant_file:
            return DataMerchant()
        elif file_name == self.event_file:
            return Event()
        else:
            return None

    def add_to_merchants(self, file_name, db_object):
        if file_name == self.merchant_file:
            self.merchants.append(db_object)
        elif file_name == self.event_file:
            index = int(db_object.all_fields[self.constants.id])
            merchant = self.merchants[index]
            merchant.events.append(db_object)
        else:
            return None

    def read_fields(self, file_name):
        if file_name == self.merchant_file:
            fields = DataMerchant().keys
        elif file_name == self.event_file:
            fields = Event().keys
        with open(self.file_base_path + file_name, 'r') as file:
            for line in file:
                if line != '' or line != '\n':
                    columns = line.split(self.deliminator)
                    if columns[0] != '':
                        db_object = self.get_object_for_file(file_name)
                        counter = 0
                        is_first_column = True
                        for column in columns:
                            if column != '\n' and counter < len(fields):
                                if is_first_column:
                                    db_object.all_fields[self.constants.id] = self.decrement_id_field(column)
                                    is_first_column = False
                                else:
                                    db_object.all_fields[fields[counter]] = column
                                counter += 1
                        self.add_to_merchants(file_name, db_object)
        file.close()
        return None

    def decrement_id_field(self, field_number):
        new_field_number = int(field_number) - 1
        return str(new_field_number)

    def print_merchants(self):
        counter = 0
        for merchant in self.merchants:
            for key in merchant.keys:
                if key == self.constants.food_truck or key == self.constants.happy_hour:
                    print(key, ":")
                    item_list = merchant.all_fields[key]
                    for item in item_list:
                        print(item)
                else:
                    print(key, ':', merchant.all_fields[key])
            print('\n')
            counter += 1
        return None

class Constants:
    def __init__(self):
        #constants for all models
        self.address                = ['street_number', 'city', 'state', 'zip', 'latitude', 'longitude']
        self.days                   = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        self.recurring_weekly       = 'recurring_weekly'
        self.recurring_daily        = 'recurring_daily'
        self.name                   = 'name'
        self.merchant_name          = 'merchant_name'
        self.day                    = 'day'
        self.month                  = 'month'
        self.year                   = 'year'
        self.start                  = 'start'
        self.end                    = 'end'
        self.message                = 'message'
        self.id                     = 'id'
        self.type                   = 'type'
        self.type_ext               = 'type_ext'
        self.password               = 'password'
        self.email                  = 'email'
        self.description            = 'description'
        self.phone_number           = 'phone_number'
        self.contact                = 'contact'
        self.logo                   = 'logo'
        self.website                = 'website'
        self.yelp                   = 'yelp'
        self.facebook               = 'facebook'
        self.instagram              = 'instagram'
        self.open_table             = 'open_table'
        self.twitter                = 'twitter'
        self.all_day                = 'all_day'
        self.fixed_address          = 'fixed_address'
        self.location_description   = 'location_description'
        self.food_truck             = 'food_truck'
        self.happy_hour             = 'happy_hour'
        #scene constants
        self.scene_days             = ['monday1', 'monday2', 'tuesday1', 'tuesday2', 'wednesday1', 'wednesday2', 'thursday1', 'thursday2',
                                       'friday1', 'friday2', 'saturday1', 'saturday2', 'sunday1', 'sunday2']
        self.events                 = 'events'


class DataMerchant:
    def __init__(self):
        # keys are mirrors of the spread sheet fields
        self.constants = Constants()
        self.keys = [self.constants.id,                 #0
                     self.constants.type,               #1
                     self.constants.name,               #3
                     self.constants.contact,            #4
                     self.constants.email,              #5
                     self.constants.password,           #6
                     self.constants.address[0],         #7
                     self.constants.address[1],         #8
                     self.constants.address[2],         #9
                     self.constants.address[3],         #10
                     self.constants.scene_days[0],      #11
                     self.constants.scene_days[1],      #12
                     self.constants.scene_days[2],      #13
                     self.constants.scene_days[3],      #14
                     self.constants.scene_days[4],      #15
                     self.constants.scene_days[5],      #16
                     self.constants.scene_days[6],      #17
                     self.constants.scene_days[7],      #18
                     self.constants.scene_days[8],      #19
                     self.constants.scene_days[9],      #20
                     self.constants.scene_days[10],     #21
                     self.constants.scene_days[11],     #22
                     self.constants.scene_days[12],     #23
                     self.constants.scene_days[13],     #24
                     self.constants.logo,               #25
                     self.constants.description,        #26
                     self.constants.phone_number,       #27
                     self.constants.website,            #28
                     self.constants.yelp,               #29
                     self.constants.open_table,         #30
                     self.constants.twitter,            #31
                     self.constants.facebook,           #32
                     self.constants.message             #33
                     ]
        self.events = []
        self.all_fields = self.fill_all_fields()

    def fill_all_fields(self):
        fields = {}
        for field in self.keys:
            if field == self.constants.events:
                fields[field] = []
            else:
                fields[field] = ''
        return fields

    def update_events_addresses(self):
        for event in self.events:
            if event.all_fields[self.constants.address[0]] == '':
                event.all_fields[self.constants.address[0]] = self.all_fields[self.constants.address[0]]
                event.all_fields[self.constants.address[1]] = self.all_fields[self.constants.address[1]]
                event.all_fields[self.constants.address[2]] = self.all_fields[self.constants.address[2]]
                event.all_fields[self.constants.address[3]] = self.all_fields[self.constants.address[3]]
        return None

class Event():
    def __init__(self):
        self.constants = Constants()
        self.keys = [self.constants.id,
                     self.constants.merchant_name,
                     self.constants.type,
                     self.constants.type_ext,
                     self.constants.fixed_address,
                     self.constants.address[0],
                     self.constants.address[1],
                     self.constants.address[2],
                     self.constants.address[3],
                     self.constants.recurring_weekly,
                     self.constants.days[0],
                     self.constants.days[1],
                     self.constants.days[2],
                     self.constants.days[3],
                     self.constants.days[4],
                     self.constants.days[5],
                     self.constants.days[6],
                     self.constants.day,
                     self.constants.month,
                     self.constants.year,
                     self.constants.start,
                     self.constants.end,
                     self.constants.message
        ]

        self.all_fields = self.fill_all_fields()

    def fill_all_fields(self):
        fields = {}
        for field in self.keys:
            fields[field] = ''
        return fields

    def __str__(self):
        return str(self.all_fields)

class DjangoAroundParser:
    def __init__(self):
        self.file_reader = FileReader()

    def read_from_files(self):
        for file_name in self.file_reader.all_files():
            self.file_reader.read_fields(file_name)
        return None

