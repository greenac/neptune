import math

def distance_between_points(pt1, pt2):
    #distance between two point in meters
    earth_radius = 6371009  #in meters
    latitude1 = math.radians(pt1['latitude'])
    latitude2 = math.radians(pt2['latitude'])
    d_latitude = latitude1 - latitude2
    d_longitude = math.radians(pt1['latitude'] - pt2['latitude'])
    k = math.sin(d_latitude/2)**2 + math.cos(latitude1)*math.cos(latitude2)*math.sin(d_longitude/2)**2
    d = earth_radius*2*math.asin(math.sqrt(k))
    return d