#!/usr/bin/python
from __future__ import with_statement
import json
import glob
import sys
import os
import csv
import re
import math

from waypoints import WAYPOINTS

## we use this string to mark cells as not applicable -- i.e. there's no
## final robot location because the test harness crashed
na = "n/a"

def dist(x1, y1, x2, y2):
    if na in [x1,x2,y1,y2]:
        return na
    return math.sqrt((float(x2) - float(x1))**2 + (float(y2) - float(y1))**2)

def get_map_coord(name):
    filtered = filter(lambda waypoint: waypoint["node-id"] == name, WAYPOINTS)
    if len(filtered) != 1:
        return {'x': "0.0", 'y' : "0,0"}
    wp = filtered[0]['coord']
    wp['x'] = str(wp['x'])
    wp['y'] = str(wp['y'])
    return wp

# find last location of robot
def get_log_entries(path):
    lines = []
    with open("%s/log" % path) as log:
        for line in log:
            lines.append(json.loads(line))
    return lines

def get_final_sim_time(path):
    lines = []
    with open("%s/results.json" % path) as log:
        lines = json.load(log)
    for i in lines:
        if "/action/done" in i["ENDPOINT"]:
            return int(i["ARGUMENTS"]["sim_time"])
    return 0

def get_final_location(path):
    end_time = get_final_sim_time(path)
    try:
        with open("%s/observe.log" % path) as obs:
            for line in obs:
                observation = json.loads(line)
                observation = observation["RESULT"]
                if end_time <= int(observation["sim_time"]):
                    observation["x"] = str(observation["x"])
                    observation["y"] = str(observation["y"])
                    observation["voltage"] = str(observation["voltage"])
                    return observation
    except IOError:
        return {"x" : na, "y" : na, "voltage" : na}
    except TypeError:
        return {"x" : na, "y" : na, "voltage" : na}

# Get the obstacle information from the log entries (test/log)
# Return empty array if it does not exist
def get_observations(log):
    info = {}
    remove_time_in_next_observe = False
    battery_time_in_next_observe = False
    kinect_time_in_next_observe = False

    def process_next_observe():
        return remove_time_in_next_observe or battery_time_in_next_observe or kinect_time_in_next_observe;

    sim_time_pattern = re.compile('sim_time.: .(\d+)')

    for line in log:
        if "place_obstacle hit" in line["MESSAGE"]:
            message = line["MESSAGE"][len("/action/place_obstacle hit with "):]
            message = message.replace("u'", "'")
            message = message.replace("'", '"')
            loc = json.loads(message)
            info['x'] = str(loc["ARGUMENTS"]['x'])
            info['y'] = str(loc["ARGUMENTS"]['y'])
        elif "place_obstacle returning" in line["MESSAGE"]:
            message = line["MESSAGE"]
            m = sim_time_pattern.search(message)
            info['place_time'] = m.group(1)
        elif "remove_obstacle hit" in line["MESSAGE"]:
            remove_time_in_next_observe = True
        elif "set_battery hit" in line["MESSAGE"]:
            message = line["MESSAGE"][len("/action/set_voltage hit with "):]
            message = message.replace("u'", "'")
            message = message.replace("'", '"')
            loc = json.loads(message)
            info['voltage'] = str(loc["ARGUMENTS"]['voltage'])
            battery_time_in_next_observe = True
        elif "perturb_sensor hit" in line["MESSAGE"]:
            kinect_time_in_next_observe = True;
        elif "observe returning" in line["MESSAGE"] and process_next_observe():
            m = sim_time_pattern.search(line["MESSAGE"])
            if remove_time_in_next_observe:
                remove_time_in_next_observe = False
                info['remove_time'] = m.group(1)
            if battery_time_in_next_observe:
                battery_time_in_next_observe = False
                info['battery_time'] = m.group(1)
            if kinect_time_in_next_observe:
                kinect_time_in_next_observe = False
                info['kinect_time'] = m.group(1)
    return info

# take directory of interest on the command line as the first argument.
target_dir = sys.argv[1]

## functions per column, named as in header.csv
def cp_level():
    return json_parts[0]

def case():
    return test_dir_parts[2]

def start_name():
    return test_data['configParams']['testInit']['start_loc']

def start_x():
    return get_map_coord(test_data['configParams']['testInit']['start_loc'])['x']

def start_y():
    return get_map_coord(test_data['configParams']['testInit']['start_loc'])['y']

def target_name():
    return test_data['configParams']['testInit']['target_loc']

def target_x():
    return target_location['x']

def target_y():
    return target_location['y']

def obstacle():
    return test_data['configParams']['testRun']['obsPert']

def removed():
    if test_data['configParams']['testRun']['obsPert']:
        return test_data['configParams']['testRun']['obs_delay']
    return na

def battery_perturbed():
    return test_data['configParams']['testRun']['battPert']

def batt_reduce():
    if 'voltage' in observations:
        return observations['voltage']
    return na

def batt_delay():
    if 'battery_time' in observations:
        return observations['battery_time']
    return na

def kinect():
    return test_data['configParams']['testRun']['sensorPert']

def kinect_delay():
    if 'kinect_time' in observations:
        return observations['kinect_time']
    return na

def outcome():
    return test_data['test_outcome']

def accuracy():
    return test_data[test_dir_parts[2]][0][1]

def timing():
    if json_parts[0] == "CP1":
        return test_data[test_dir_parts[2]][1][1]
    return na

def safety():
    if json_parts[0] == "CP1":
        return test_data[test_dir_parts[2]][2][1]
    return na

def detection():
    if json_parts[0] == "CP2":
        return test_data[test_dir_parts[2]][1][1]
    return na

def final_x():
    return final_location["x"]

def final_y():
    return final_location["y"]

def final_voltage():
    return final_location["voltage"]

def distance_to_goal():
    return dist(target_location['x'],target_location['y'],
                final_location["x"],final_location["y"])

def obstacle_x():
    if 'x' in observations:
        return observations['x']
    return na

def obstacle_y():
    if 'y' in observations:
        return observations['y']
    return na

def obstacle_time():
    if 'place_time' in observations:
        return observations['place_time']
    return na

def removal_time():
    if 'remove_time' in observations:
        return observations['remove_time']
    return na

def number_of_notifications():
    return num_notifications

def pert_detect_sim_time():
    return pert_simtime

def first_observed_sim_time():
    return first_simtime

def done_sim_time():
    return done_simtime

def json_path():
    return j_path

def data_path():
    return test_dir



## read in the header file
with open('header.csv') as header_file:
    header_names = map(lambda elem: elem.replace(' ', '_'),
                       header_file.read().splitlines())

for j_path in glob.glob('%s/*.json' % target_dir):
    ## skip the aggregated files; i don't know what they mean yet
    if 'aggregate' in j_path:
        continue

    basename = os.path.basename(j_path)

    ## split out the hash
    json_parts = basename.split('_')

    ## parts[2] ends in a '.json' because python basename isn't posix
    ## standard, so this grabs just the hash that they use to name each
    ## test.
    test_name = (json_parts[2].split('.'))[0]

    with open(j_path) as test_json:
        test_data = json.load(test_json)

        for test_dir in glob.glob('%s/*%s*/' % (target_dir, test_name)):

            ## if valid, call bradley's with ('%s/test/' % test_dir)
            log_entries = get_log_entries('%s/test' % test_dir)
            final_location = get_final_location('%s/test' % test_dir)

            observations = get_observations(log_entries)

            # store the target x and y coordinates, because we use them
            # several times below
            target_location = {'x' : get_map_coord(test_data['configParams']['testInit']['target_loc'])['x'],
                               'y' : get_map_coord(test_data['configParams']['testInit']['target_loc'])['y']}

            ## todo: make a co-ordinate object

            # count the number of lines in notifications.txt to count how
            # many times we send notifications
            num_notifications = na
            try:
                if json_parts[0] == "CP1":
                    num_notifications = 0
                    with open('%s/test/mars_notifications.txt' % test_dir) as note_file:
                        for l in note_file:
                            num_notifications += 1
            except IOError:
                num_notifications = na

            # read ll-api.log to compute the simtimes for when we
            # detect the perturbation and when we hit /action/done
            pert_simtime = na
            done_simtime = na

            done_time_hit = False
            try:
                with open('%s/test/ll-api.log' % test_dir) as api_file:
                    for line in api_file:
                        if "PERTURBATION_DETECTED" in line:
                            data = json.loads(((":").join((line.split(':'))[1:])))
                            pert_simtime = str(data['MESSAGE']['sim_time'])

                        # we may hit done many times, or none at all. this
                        # will record the first, leaving the values as n/a
                        # if there are none (i.e. because we hit time out
                        # and never notified)
                        if (not done_time_hit) and ("/action/done" in line):
                            done_time = True
                            data = json.loads(((":").join((line.split(':'))[1:])))
                            done_simtime = str(data['ARGUMENTS']['sim_time'])
            except IOError:
                pert_simtime = na
                done_simtime = na

            first_simtime = na
            # find the sim time in the first time they hit our
            # observe. this is somewhat redundant to the get_observations
            # above, but since it only looks at a prefix of the file, it's
            # faster and fine for now.
            try:
                with open('%s/test/log' % test_dir) as log_file:
                    for line in log_file:
                        if "/action/observe returning response" in line:
                            ## easier to grab it with a regex as above,
                            ## because it's in escaped json in a string
                            sim_time_pattern = re.compile('sim_time..: ..(\d+)')
                            m = sim_time_pattern.search(line)
                            first_simtime = m.group(1)
                            break
            except IOError:
                first_simtime = na

            test_dir_parts = test_dir.split("_")

            print (",").join([str(locals()[name]()) for name in header_names])
