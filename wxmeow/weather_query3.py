import csv
from flask import Flask, url_for
import os
import requests
import urllib3
import json
import re


# functions for validating user input --------------
def hasperiod(string):
    return '.' in string

def hasnumbers(string):
    return any(char.isdigit() for char in string)

def iszipcode(string):
    string = string.replace(" ", "")
    if len(string) in (5 or 6): # 5 for US, p6 for CA
        return True
    else:
        return False

def islatlong(string):
    arglist = string.replace(",", " ").split(" ")
    latlong = []

    for inc in arglist:
        if inc == "":
            pass
        else:
            latlong.append(inc)

    return latlong


class geo(object):
    url = 'https://maps.googleapis.com/maps/api/geocode/json?address='
    key = '&key=AIzaSyAxXM09e4--F_lBsHw7QK7KqxtvoEhcLrE'

    def __init__(self, location):

        ## find request location
        #  is it a zip code?
        if int(self.location) == True:
            address = (self.location)
            len(str(address)) < 6
        #  is it a friggin decimal lat/long?
        elif re.match('^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$', self.location):
            address = self.location.replace(' ', '+')


class noaa(object):
    """
    NOAA ------------------------------------------------------
    for current conditions, need to get station id from:
        https://api.weather.gov/points/{points}/stations
        https://api.weather.gov/points/44.2774,-72.5799/stations
            "observationStations"
        then use https://api.weather.gov/stations/{stationid}/observations
        e.g. https://api.weather.gov/stations/KMVL/observations
         full list of us zips from 2013 and lat/long here:
    https://gist.githubusercontent.com/erichurst/7882666/raw/5bdc46db47d9515269ab12ed6fb2850377fd869e/US%2520Zip%2520Codes%2520from%25202013%2520Government%2520Data

    for forecast, data must be in dec lat long
    eg: https://api.weather.gov/points/44.2774,-72.5799/forecast/hourly
    focast = requests.get("")
    focast.json()['properties']['periods'][0]['temperature']
    i = 0
    while i < 100:
       print str(poots.json()['properties']['periods'][i]['temperature'])+"\t"+poots.json()['properties']['periods'][i]['shortForecast']+"\t"+poots.json()['properties']['periods'][i]['icon']
       i = i + 1
    """
    import json

    def __init__(self, location):
        self.location = str(location)
        self.baseurl = "https://api.weather.gov/points/"
        self.zipfile = url_for('static', filename='zips.txt')

        try:
            os.path.exists(self.zipfile)
        except:
            z_url = "https://gist.githubusercontent.com/erichurst/7882666/raw/5bdc46db47d9515269ab12ed6fb2850377fd869e/US%2520Zip%2520Codes%2520from%25202013%2520Government%2520Data"
            z = requests.get(z_url)
            with open(self.zipfile, 'wb') as _zipfile:
                _zipfile.write(z.content)

        csv_file = csv.reader(open(self.zipfile, "rt"), delimiter=",")

        try:
            for row in csv_file:
                if self.location == row[0]:
                    lat = row[1].strip()
                    long = row[2].strip()
            #print("zip = {0}, lat = {1}, long = {2}".format(self.location, lat, long))
        except:
            print("unable to find forecast for {0}".format(self.location))

        self.station_reserve = str(requests.get(self.baseurl+lat+","+long+"/stations").json()['features'][1]['id'])
        self.station_reserve2 = str(requests.get(self.baseurl+lat+","+long+"/stations").json()['features'][2]['id'])
        self.station = str(requests.get(self.baseurl+lat+","+long+"/stations").json()['features'][0]['id'])
        self.conditions = requests.get(self.station + "/observations")
        self.conditions_reserve = requests.get(self.station_reserve + "/observations")
        self.conditions_reserve2 = requests.get(self.station_reserve2 + "/observations")
        self.hourly_forecast = requests.get(self.baseurl+lat+","+long+"/forecast/hourly") # hourly forecast...
        self.forecast = requests.get(self.baseurl+lat+","+long+"/forecast/")

        try:
            self.jconditions = json.loads(self.conditions.text)
        except:
            self.jconditions = None
        try:
            self.jforecast = json.loads(self.forecast.text)
        except:
            self.jforecast = None

        try:
            self.jhourly = json.loads(self.hourly_forecast.text)

        except:
            self.jhourly = None

        try:
            self.place = requests.get("https://api.weather.gov/points/"+lat+","+long).json()['properties']['relativeLocation']['properties']
            self.city = self.place['city']
            self.state = self.place['state']

        except:
            print("couldn't get place")
            self.location = "unknown"
            self.city = "wherever"
            self.state = "who cares"

    def format_for_meow(self):
        """
        format noaa response for wxmeow presentation
        """
        pass


class openweathermap(object):
    """ api documentation here:
    forecast: http://openweathermap.org/forecast5
    conditions: http://openweathermap.org/current
    icons: https://openweathermap.org/weather-conditions
    """

    baseurl = 'http://api.openweathermap.org/data/2.5/'
    key = '71ed240536f23211e1b5329e940617f8'

    def __init__(self, location):

        return self

    def locationtype(self):
        # is it a zip code?

        # is it lat/long?

        # is it city/state/country?

        return self
