import urllib2
import json
import os
import glob
import time
from datetime import timedelta, date
from ISStreamer.Streamer import Streamer

# --------- User Settings ---------
STATE = "CA"
CITY = "San_Francisco"
WUNDERGROUND_API_KEY = "PLACE YOUR WUNDERGROUND API KEY HERE"
BUCKET_NAME = ":partly_sunny: " + CITY + " Weather"
BUCKET_KEY = "wu1"
ACCESS_KEY = "PLACE YOUR INITIAL STATE ACCESS KEY HERE"
STARTDATE = date(YYYY,MM,DD)
ENDDATE = date(YYYY,MM,DD)
SECONDS_BETWEEN_SEND = 5
# ---------------------------------

def isFloat(string):
    try:
        float(string)
        if float(string) < 0:
        	raise ValueError
        return True
    except ValueError:
        return False

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

def get_conditions(readDate):
	api_conditions_url = "http://api.wunderground.com/api/" + WUNDERGROUND_API_KEY + "/history_" + readDate + "/q/" + STATE +"/"+ CITY + ".json"
	try:
	  	f = urllib2.urlopen(api_conditions_url)
	except:
		print "Failed to get conditions"
		return False
	json_conditions = f.read()
	f.close()
	return json.loads(json_conditions)	

streamer = Streamer(bucket_name=BUCKET_NAME, bucket_key=BUCKET_KEY, access_key=ACCESS_KEY)


while True:
	for single_date in daterange(STARTDATE,ENDDATE):
		conditions = get_conditions(single_date.strftime("%Y%m%d"))

		if (conditions != False):
			for i in range(len(conditions['history']['observations'])):
				dateInfo = conditions['history']['observations'][i]['date']
				date = dateInfo['mday']+"."+dateInfo['mon']+"."+dateInfo['year']+" "+dateInfo['hour']+":"+dateInfo['min']+":00"
				print date
				pattern = '%d.%m.%Y %H:%M:%S'
				epoch = int(time.mktime(time.strptime(date, pattern)))

				humidity_wu = conditions['history']['observations'][i]['hum']
				temp_wu = conditions['history']['observations'][i]['tempi']
				pressure_wu = conditions['history']['observations'][i]['pressurem']
				precip_wu = conditions['history']['observations'][i]['precipi']
				wind_speed_wu = conditions['history']['observations'][i]['wspdi']

				if isFloat(humidity_wu):
					streamer.log("WU Humidity (%)",humidity_wu,epoch)
				if isFloat(temp_wu):
					streamer.log("WU Temp",temp_wu,epoch)
				if isFloat(pressure_wu):
					streamer.log("WU Pressure",pressure_wu,epoch)
				if isFloat(precip_wu):
					streamer.log("WU Rain",precip_wu,epoch)
				if isFloat(wind_speed_wu):
					streamer.log("WU Wind Speed",wind_speed_wu,epoch)
		
				streamer.flush()
				time.sleep(SECONDS_BETWEEN_SEND)

			if single_date == ENDDATE:
				print("All dates streamed")
				exit()
