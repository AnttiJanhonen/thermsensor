# -*- coding: utf-8 -*-
import time
import os.path
from os.path import normpath, basename
from glob import glob
import re
import requests
import configparser

config = configparser.ConfigParser()
config.read("temperatures.cfg")

filePath = config.get('writetofile', 'file_location')
file_write_enabled = config.getboolean('writetofile', 'enabled')

influxdb_db_print_response = config.getboolean('InfluxDB', 'print_response')
influxdb_db_enabled = config.getboolean('InfluxDB', 'enabled')
influxdb_address = config.get('InfluxDB', 'influxdb_address')
influxdb_api = config.get('InfluxDB', 'influxdb_api')
influxdb_db = config.get('InfluxDB', 'influxdb_db')
influxdb_region = config.get('InfluxDB', 'region')
influxdb_host = config.get('InfluxDB', 'host')
influxdb_measurement_name = config.get('InfluxDB', 'measurement_name')

temperature_cutoff = config.getint('common', 'temperature_cutoff')


def read_temperatures(sensor_paths):
    # Loop through the sensors and read them and write their value to avgtemperatures array.
    avgtemperatures = []
    for sensor in range(len(sensor_paths)):
        temperatures = []
        for polltime in range(0, 3):
            text = ''
            while text.split("\n")[0].find("YES") == -1:
                tfile = open(sensor_paths[sensor] + "w1_slave")
                text = tfile.read()
                tfile.close()
                time.sleep(1)

            secondline = text.split("\n")[1]
            temperaturedata = secondline.split(" ")[9]
            temperature = round(float(temperaturedata[2:]), 3)
            temperatures.append(temperature / 1000)

        realtemp = round(sum(temperatures) / float(len(temperatures)), 3)
        if (influxdb_db_enabled and realtemp >= temperature_cutoff):
            post_temp(sensor_paths, sensor, realtemp)
        avgtemperatures.append(round(sum(temperatures) / float(len(temperatures)), 3))
    if (file_write_enabled):
        write_temp_to_file(avgtemperatures)
    return "Complete"


def post_temp(sensor_paths, sensor, temp):
    influxdb_full_url = "http://{0}{1}{2}".format(influxdb_address, influxdb_api, influxdb_db)
    payload = '{0},host={1},region={2},sensor={3} value={4}'.format(influxdb_measurement_name,
                                                                    influxdb_host, influxdb_region,
                                                                    basename(normpath(sensor_paths[sensor])),
                                                                    temp)
    response = requests.post(influxdb_full_url, data=payload)
    if (influxdb_db_print_response):
        print ('Posted: {0} ').format(payload) + str(response)


def sensor_paths():
    # Find out which sensors exist assuming all devices connected to the pi are temperature sensors
    sensor_paths = glob("/sys/bus/w1/devices/*/")
    regex = re.compile(r'(([^\']+)w1_bus_master1([^\']+))')
    # Remove w1_bus_master from the array as it is not a sensor.
    sensor_paths = [x for x in sensor_paths if not regex.match(x)]
    return sensor_paths


def main():
    print (read_temperatures(sensor_paths()))


def write_temp_to_file(avgtemperatures):
    print (avgtemperatures)
    lampo = str(avgtemperatures)
    file = open(filePath, "w")
    file.write("Temperature:")
    file.write(lampo)
    file.close()


if __name__ == "__main__":
    main()
