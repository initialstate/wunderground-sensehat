import urllib2
import json
import os
import glob
import time
import RPi.GPIO as io
from ISStreamer.Streamer import Streamer
from sense_hat import SenseHat 

# --------- User Settings ---------
CITY = "Franklin"
GPS_COORDS = "35.9260096,-86.868537"
SENSOR_LOCATION_NAME = "Office"
DARKSKY_API_KEY = "PLACE YOUR DARK SKY API KEY HERE"
BUCKET_NAME = ":partly_sunny: " + CITY + " Weather"
BUCKET_KEY = "shds1"
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

def get_current_conditions():
	api_conditions_url = "https://api.darksky.net/forecast/" + DARKSKY_API_KEY + "/" + GPS_COORDS + "?units=auto"
	try:
		f = urllib2.urlopen(api_conditions_url)
	except:
		return []
	json_currently = f.read()
	f.close()
	return json.loads(json_currently)

def moon_icon(moon_phase):
	if moon_phase == 0:
		return ":new_moon:"
	if moon_phase < .125:
		return ":waxing_crescent_moon:"
	if moon_phase < .25:
		return ":first_quarter_moon:"
	if moon_phase < .5:
		return ":waxing_gibbous_moon:"
	if moon_phase == .5:
		return ":full_moon:"
	if moon_phase < .625:
		return ":waning_gibbous_moon:"
	if moon_phase < .75:
		return ":last_quarter_moon:"
	if moon_phase < 1:
		return ":waning_crescent_moon:"
	return ":crescent_moon:"

def weather_icon(ds_icon):
	icon = {
		"clear-day"            	: ":sunny:",
		"clear-night"           : ":new_moon_with_face:",
		"rain"         			: ":umbrella:",
		"snow"              	: ":snowflake:",
		"sleet"             	: ":sweat_drops: :snowflake:",
		"wind"     				: ":wind_blowing_face:",
		"fog"      				: ":fog:",
		"cloudy"     			: ":cloud:",
		"partly-cloudy-day"		: ":partly_sunny:",
		"partly-cloudy-night"   : ":new_moon_with_face:",
		"unknown"          		: ":sun_with_face:",
	}
	return icon.get(ds_icon,":sun_with_face:")

def weather_status_icon(ds_icon,moon_phase):
	icon = weather_icon(ds_icon)
	if (icon == ":new_moon_with_face:"):
		return moon_icon(moon_phase)
	return icon

def wind_dir_icon(wind_bearing):
	if (wind_bearing < 20):
		return ":arrow_up:"
	if (wind_bearing < 70):
		return ":arrow_upper_right:"
	if (wind_bearing < 110):
		return ":arrow_right:"
	if (wind_bearing < 160):
		return ":arrow_lower_right:"
	if (wind_bearing < 200):
		return ":arrow_down:"
	if (wind_bearing < 250):
		return ":arrow_lower_left:"
	if (wind_bearing < 290):
		return ":arrow_left:"
	if (wind_bearing < 340):
		return ":arrow_upper_left:"
	return ":arrow_up:"

def main():
	sense = SenseHat()	
	curr_conditions = get_current_conditions()
	if ('currently' not in curr_conditions):
		print "Error! Dark Sky API call failed, check your GPS coordinates and make sure your Dark Sky API key is valid!\n"
		print curr_conditions
		exit()
	else:
		streamer = Streamer(bucket_name=BUCKET_NAME, bucket_key=BUCKET_KEY, access_key=ACCESS_KEY)
		streamer.log(":house: Location",GPS_COORDS)
		a = 1
	while True:
		# -------------- Sense Hat --------------
		# Read the sensors
		temp_c = sense.get_temperature()
		humidity = sense.get_humidity() 
		pressure_mb = sense.get_pressure() 

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

		# -------------- Dark Sky --------------		
		curr_conditions = get_current_conditions()
		if ('currently' not in curr_conditions):
			print "Error! Dark Sky API call failed. Skipping a reading then continuing ...\n"
			print curr_conditions
		else:
			if isFloat(curr_conditions['currently']['humidity']):
				streamer.log(":droplet: Humidity(%)", curr_conditions['currently']['humidity']*100)

			if isFloat(curr_conditions['currently']['temperature']): 
				streamer.log("Temperature",curr_conditions['currently']['temperature'])

			if isFloat(curr_conditions['currently']['apparentTemperature']): 
				streamer.log("Feels Like",curr_conditions['currently']['apparentTemperature'])

			if isFloat(curr_conditions['currently']['dewPoint']):
				streamer.log("Dewpoint",curr_conditions['currently']['dewPoint'])

			if isFloat(curr_conditions['currently']['windSpeed']):
				streamer.log(":dash: Wind Speed",curr_conditions['currently']['windSpeed'])

			if isFloat(curr_conditions['currently']['windGust']):
				streamer.log(":dash: Wind Gust",curr_conditions['currently']['windGust'])

			if isFloat(curr_conditions['currently']['windBearing']):
				streamer.log(":dash: Wind Direction",wind_dir_icon(curr_conditions['currently']['windBearing']))

			if isFloat(curr_conditions['currently']['pressure']):
				streamer.log("Pressure",curr_conditions['currently']['pressure'])

			if isFloat(curr_conditions['currently']['precipIntensity']):
				streamer.log(":umbrella: Precipitation Intensity",curr_conditions['currently']['precipIntensity'])

			if isFloat(curr_conditions['currently']['precipProbability']):
				streamer.log(":umbrella: Precipitation Probabiity(%)",curr_conditions['currently']['precipProbability']*100)

			if isFloat(curr_conditions['currently']['cloudCover']):
				streamer.log(":cloud: Cloud Cover(%)",curr_conditions['currently']['cloudCover']*100)

			if isFloat(curr_conditions['currently']['uvIndex']):
				streamer.log(":sunny: UV Index:",curr_conditions['currently']['uvIndex'])

			streamer.log(":cloud: Weather Summary",curr_conditions['currently']['summary'])

			if 'hourly' in curr_conditions:
				streamer.log("Today's Forecast",curr_conditions['hourly']['summary'])

			if 'daily' in curr_conditions:
				moon_phase = curr_conditions['daily']['data'][0]['moonPhase']
				streamer.log(":crescent_moon: Moon Phase",moon_icon(moon_phase))
				streamer.log(":cloud: Weather Conditions",weather_status_icon(curr_conditions['currently']['icon'],moon_phase))

			streamer.flush()
		time.sleep(60*MINUTES_BETWEEN_READS)

if __name__ == "__main__":
    main()

