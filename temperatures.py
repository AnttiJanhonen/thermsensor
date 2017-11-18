#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import os.path
from glob import glob
import re
import requests

filePath = "./www/lampo.txt"

influxdb_address = "10.8.0.100:8086"
influxdb_api = "/write"
influxdb_db = "?db=Lämpötilat"
region = "mokki"
server = "xorppo"
write_temps_to_file = True


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
        print post_temp(sensor_paths, sensor, realtemp)
        avgtemperatures.append(round(sum(temperatures) / float(len(temperatures)), 3))
    write_temp_to_file(avgtemperatures)
    return "Complete"


def post_temp(sensor_paths, sensor, temp):
    influxdb_full_url = "http://{0}{1}{2}".format(influxdb_address, influxdb_api, influxdb_db)
    payload = 'lampotila,host={0},region={1},sensor={2} value={3}'.format(server, region, sensor_paths[sensor], temp)
    response = requests.post(influxdb_full_url, data=payload)
    return response


def sensor_paths():
    # Find out which sensors exist assuming all devices connected to the pi are temperature sensors
    sensor_paths = glob("/sys/bus/w1/devices/*/")
    regex = re.compile(r'(([^\']+)w1_bus_master1([^\']+))')
    # Remove w1_bus_master from the array as it is not a sensor.
    sensor_paths = [x for x in sensor_paths if not regex.match(x)]
    return sensor_paths


def main():
    print read_temperatures(sensor_paths())


def write_temp_to_file(avgtemperatures):
    print (avgtemperatures)
    lampo = str(avgtemperatures)
    file = open(filePath, "w")
    file.write("Temperature:")
    file.write(lampo)
    file.close()


if __name__ == "__main__":
    main()