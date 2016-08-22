#!/usr/bin/python

# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola

import Adafruit_DHT
from ISStreamer.Streamer import Streamer
from time import sleep

# Sensor should be set to Adafruit_DHT.DHT11,
# Adafruit_DHT.DHT22, or Adafruit_DHT.AM2302.
sensor = Adafruit_DHT.DHT22

# Example using a Raspberry Pi with DHT sensor
# connected to GPIO 3.
pin = 3

streamer = Streamer(bucket_key="shwu1", access_key="PLACE YOUR INITIAL STATE ACCESS KEY HERE")

while True:
	# Try to grab a sensor reading.  Use the read_retry method which will retry up
	# to 15 times to get a sensor reading (waiting 2 seconds between each retry).
	humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

	# Note that sometimes you won't get a reading and
	# the results will be null (because Linux can't
	# guarantee the timing of calls to read the sensor).
	# If this happens try again!
	if humidity is not None and temperature is not None:
	    
	    temperatureF = 9.0/5.0*temperature+32
	    streamer.log("Actual Temperature",temperatureF)
	    print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
	    sleep(900)
	else:
	    print('Failed to get reading. Try again!')
