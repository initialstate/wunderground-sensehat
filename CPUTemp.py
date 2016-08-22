import os
import urllib2
import json
import glob
import time
import RPi.GPIO as io
from ISStreamer.Streamer import Streamer
from sense_hat import SenseHat 
import subprocess

# --------- User Settings ---------
STATE = "CA"
CITY = "San_Francisco"
SENSOR_LOCATION_NAME = "Office"
WUNDERGROUND_API_KEY = "PLACE YOUR WUNDERGROUND API KEY HERE"
BUCKET_NAME = ":partly_sunny: " + CITY + " Weather"
BUCKET_KEY = "shwu1"
ACCESS_KEY = "PLACE YOUR INITIAL STATE ACCESS KEY HERE"
MINUTES_BETWEEN_READS = 15
METRIC_UNITS = False
# ---------------------------------

def isFloat(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def get_conditions():
	api_conditions_url = "http://api.wunderground.com/api/" + WUNDERGROUND_API_KEY + "/conditions/q/" + STATE + "/" + CITY + ".json"
	try:
	  	f = urllib2.urlopen(api_conditions_url)
	except:
		print "Failed to get conditions"
		return []
	json_conditions = f.read()
	f.close()
	return json.loads(json_conditions)

def get_astronomy():
	api_astronomy_url = "http://api.wunderground.com/api/" + WUNDERGROUND_API_KEY + "/astronomy/q/" + STATE + "/" + CITY + ".json"
	try:
		f = urllib2.urlopen(api_astronomy_url)
	except:
		print "Failed to get astronomy"
		return []		
	json_astronomy = f.read()
	f.close()
	return json.loads(json_astronomy)

def is_night(astronomy):
	sunrise_hour = int(astronomy['moon_phase']['sunrise']['hour'])
	sunrise_min  = int(astronomy['moon_phase']['sunrise']['minute'])
	sunset_hour  = int(astronomy['moon_phase']['sunset']['hour'])
	sunset_min   = int(astronomy['moon_phase']['sunset']['minute'])
	current_hour = int(astronomy['moon_phase']['current_time']['hour'])
	current_min  = int(astronomy['moon_phase']['current_time']['minute'])
	if ( (current_hour < sunrise_hour) or
	     (current_hour > sunset_hour) or
	     ((current_hour == sunrise_hour) and
	      (current_min < sunrise_min)) or 
	     ((current_hour == sunset_hour) and
	      (current_min > sunset_min)) ):
		return True
	return False

def moon_icon(moon_phase):
	icon = {
		"New Moon"        : ":new_moon:",
		"Waxing Crescent" : ":waxing_crescent_moon:",
		"First Quarter"   : ":first_quarter_moon:",
		"Waxing Gibbous"  : ":waxing_gibbous_moon:",
		"Full Moon"       : ":full_moon:",
		"Full"            : ":full_moon:",
		"Waning Gibbous"  : ":waning_gibbous_moon:",
		"Last Quarter"    : ":last_quarter_moon:",
		"Waning Crescent" : ":waning_crescent_moon:",
	}
	return icon.get(moon_phase,":crescent_moon:")

def weather_icon(weather_conditions):
	icon = {
		"clear"            : ":sun_with_face:",
		"cloudy"           : ":cloud:",
		"flurries"         : ":snowflake:",
		"fog"              : ":foggy:",
		"hazy"             : ":foggy:",
		"mostlycloudy"     : ":cloud:",
		"mostlysunny"      : ":sun_with_face:",
		"partlycloudy"     : ":partly_sunny:",
		"partlysunny"      : ":partly_sunny:",
		"sleet"            : ":sweat_drops: :snowflake:",
		"rain"             : ":umbrella:",
		"snow"             : ":snowflake:",
		"sunny"            : ":sun_with_face:",
		"tstorms"          : ":zap: :umbrella:",
		"unknown"          : ":sun_with_face:",
	}
	return icon.get(weather_conditions,":sun_with_face:")

def weather_status_icon(conditions, astronomy):
	moon_phase = astronomy['moon_phase']['phaseofMoon']
	weather_conditions = conditions['current_observation']['icon']
	icon = weather_icon(weather_conditions)
	if is_night(astronomy):
		if ((icon == ":sunny:") or
		    (icon == ":partly_sunny:") or
		    (icon == ":sun_with_face:")):
			return moon_icon(moon_phase)
	return icon

def wind_dir_icon(conditions, astronomy):
	icon = {
		"East"     : ":arrow_right:",
		"ENE"      : ":arrow_upper_right:",
		"ESE"      : ":arrow_lower_right:",
		"NE"       : ":arrow_upper_right:",
		"NNE"      : ":arrow_upper_right:",
		"NNW"      : ":arrow_upper_left:",
		"North"    : ":arrow_up:",
		"NW"       : ":arrow_upper_left:",
		"SE"       : ":arrow_lower_right:",
		"South"    : ":arrow_down:",
		"SSE"      : ":arrow_lower_right:",
		"SSW"      : ":arrow_lower_left:",
		"SW"       : ":arrow_lower_left:",
		"Variable" : ":arrows_counterclockwise:",
		"West"     : ":arrow_left:",
		"WNW"      : ":arrow_upper_left:",
		"WSW"      : ":arrow_lower_left:",
	}
	return icon.get(conditions['current_observation']['wind_dir'],":crescent_moon:")	

def main():
	sense = SenseHat()
	conditions = get_conditions()
	astronomy = get_astronomy()
	if ('current_observation' not in conditions) or ('moon_phase' not in astronomy):
		print "Error! Wunderground API call failed, check your STATE and CITY and make sure your Wunderground API key is valid!"
		if 'error' in conditions['response']:
			print "Error Type: " + conditions['response']['error']['type']
			print "Error Description: " + conditions['response']['error']['description']
		exit()
	else:
		streamer = Streamer(bucket_name=BUCKET_NAME, bucket_key=BUCKET_KEY, access_key=ACCESS_KEY)
		streamer.log(":house: Location",conditions['current_observation']['display_location']['full'])
	while True:
		# -------------- Sense Hat --------------
		# Read the sensors
		temp_c = sense.get_temperature()
		humidity = sense.get_humidity() 
		pressure_mb = sense.get_pressure() 
    cpu_temp = subprocess.check_output("vcgencmd measure_temp", shell=True)
    array = cpu_temp.split("=")
    array2 = array[1].split("'")

    cpu_tempf = float(array2[0]) * 9.0 / 5.0 + 32.0
    cpu_tempf = float("{0:.2f}".format(cpu_tempf))
    streamer.log("CPU Temperature",cpu_tempf)
    print(cpu_tempf)
    
		# Format the data
		temp_f = temp_c * 9.0 / 5.0 + 32.0
		temp_f = float("{0:.2f}".format(temp_f))
		temp_c = float("{0:.2f}".format(temp_c))
		humidity = float("{0:.2f}".format(humidity))
		pressure_in = 0.0295301*(pressure_mb)
		pressure_in = float("{0:.2f}".format(pressure_in))
		pressure_mb = float("{0:.2f}".format(pressure_mb))

		# Print and stream 
		if (METRIC_UNITS):
			print SENSOR_LOCATION_NAME + " Temperature(C): " + str(temp_c)
			print SENSOR_LOCATION_NAME + " Pressure(mb): " + str(pressure_mb)
			streamer.log(":sunny: " + SENSOR_LOCATION_NAME + " Temperature(C)", temp_c)
			streamer.log(":cloud: " + SENSOR_LOCATION_NAME + " Pressure (mb)", pressure_mb)
		else:
			print SENSOR_LOCATION_NAME + " Temperature(F): " + str(temp_f)
			print SENSOR_LOCATION_NAME + " Pressure(IN): " + str(pressure_in)
			streamer.log(":sunny: " + SENSOR_LOCATION_NAME + " Temperature(F)", temp_f)
			streamer.log(":cloud: " + SENSOR_LOCATION_NAME + " Pressure (IN)", pressure_in)
		print SENSOR_LOCATION_NAME + " Humidity(%): " + str(humidity)
		streamer.log(":sweat_drops: " + SENSOR_LOCATION_NAME + " Humidity(%)", humidity)

		# -------------- Wunderground --------------
		conditions = get_conditions()
		astronomy = get_astronomy()
		if ('current_observation' not in conditions) or ('moon_phase' not in astronomy):
			print "Error! Wunderground API call failed. Skipping a reading then continuing ..."
		else:
			humidity_pct = conditions['current_observation']['relative_humidity']
			humidity = humidity_pct.replace("%","")

			# Stream valid conditions to Initial State
			streamer.log(":cloud: " + CITY + " Weather Conditions",weather_status_icon(conditions, astronomy))
			streamer.log(":crescent_moon: Moon Phase",moon_icon(astronomy['moon_phase']['phaseofMoon']))
			streamer.log(":dash: " + CITY + " Wind Direction",wind_dir_icon(conditions, astronomy))
			if (METRIC_UNITS):
				if isFloat(conditions['current_observation']['temp_c']): 
					streamer.log(CITY + " Temperature(C)",conditions['current_observation']['temp_c'])
				if isFloat(conditions['current_observation']['dewpoint_c']):
					streamer.log(CITY + " Dewpoint(C)",conditions['current_observation']['dewpoint_c'])
				if isFloat(conditions['current_observation']['wind_kph']):
					streamer.log(":dash: " + CITY + " Wind Speed(KPH)",conditions['current_observation']['wind_kph'])
				if isFloat(conditions['current_observation']['wind_gust_kph']):
					streamer.log(":dash: " + CITY + " Wind Gust(KPH)",conditions['current_observation']['wind_gust_kph'])
				if isFloat(conditions['current_observation']['pressure_mb']):
					streamer.log(CITY + " Pressure(mb)",conditions['current_observation']['pressure_mb'])
				if isFloat(conditions['current_observation']['precip_1hr_metric']):
					streamer.log(":umbrella: " + CITY + " Precip 1 Hour(mm)",conditions['current_observation']['precip_1hr_metric'])
				if isFloat(conditions['current_observation']['precip_today_metric']):
					streamer.log(":umbrella: " + CITY + " Precip Today(mm)",conditions['current_observation']['precip_today_metric'])
			else:
				if isFloat(conditions['current_observation']['temp_f']): 
					streamer.log(CITY + " Temperature(F)",conditions['current_observation']['temp_f'])
				if isFloat(conditions['current_observation']['dewpoint_f']):
					streamer.log(CITY + " Dewpoint(F)",conditions['current_observation']['dewpoint_f'])
				if isFloat(conditions['current_observation']['wind_mph']):
					streamer.log(":dash: " + CITY + " Wind Speed(MPH)",conditions['current_observation']['wind_mph'])
				if isFloat(conditions['current_observation']['wind_gust_mph']):
					streamer.log(":dash: " + CITY + " Wind Gust(MPH)",conditions['current_observation']['wind_gust_mph'])
				if isFloat(conditions['current_observation']['pressure_in']):
					streamer.log(CITY + " Pressure(IN)",conditions['current_observation']['pressure_in'])
				if isFloat(conditions['current_observation']['precip_1hr_in']):
					streamer.log(":umbrella: " + CITY + " Precip 1 Hour(IN)",conditions['current_observation']['precip_1hr_in'])
				if isFloat(conditions['current_observation']['precip_today_in']):
					streamer.log(":umbrella: " + CITY + " Precip Today(IN)",conditions['current_observation']['precip_today_in'])
			if isFloat(conditions['current_observation']['solarradiation']):
				streamer.log(":sunny: " + CITY + " Solar Radiation (watt/m^2)",conditions['current_observation']['solarradiation'])
			if isFloat(humidity):
				streamer.log(":droplet: " + CITY + " Humidity(%)",humidity)
			if isFloat(conditions['current_observation']['UV']):
				streamer.log(":sunny: " + CITY + " UV Index:",conditions['current_observation']['UV'])
			streamer.flush()
		time.sleep(60*MINUTES_BETWEEN_READS)

if __name__ == "__main__":
    main()

