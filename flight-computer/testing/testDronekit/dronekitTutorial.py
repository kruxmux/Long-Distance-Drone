from dronekit import connect, VehicleMode, Command, LocationGlobal, LocationGlobalRelative
from pymavlink import mavutil

import time
import math
# Code and functions comes from dronekit-python examples
import dronekit_sitl


sitl = dronekit_sitl.start_default()
connectionString = sitl.connection_string()

"""
Connect to APM (vehicle) for USB on Linux
You may have to use /dev/ttyUSB0 if ttyACM0 is not found
UDP online connection uses localhost:14550 instead of /dev/tty
dronekit_sitl uses tcp:127.0.0.1:5760
"""
connectionAdress = "tcp:127.0.0.1:5760"
print("Connecting to vehicle on: %s" % connectionAdress)
vehicle = connect(connectionString, wait_ready=True)

# Example of printing vehicle data from APM
print("Mode: %s" % vehicle.mode.name)
print("Attitude: %s" % vehicle.attitude)
print("Velocity: %s" % vehicle.velocity)


def get_location_metres(original_location, dNorth, dEast):
    """
    Returns a LocationGlobal object that contains the lat and lon of the
    location specified by dNorth and dEast, can be used by vehicle funcitons
    that requires LocalGlobal as parameter
    """
    earth_radius = 6378137.0
    dLat = dNorth / earth_radius
    dLon = dEast / (earth_radius*math.cos(math.pi*original_location.lat / 180))

    newLat = original_location.lat + (dLat * 180/math.pi)
    newLon = original_location.lon + (dLon * 180/math.pi)

    return LocationGlobal(newLat, newLon, original_location.alt)


# Returns the distance in meters between two LocalGlobal objects
def get_distance_metres(location1, location2):
    dLat = location2.lat - location1.lat
    dLon = location2.lon - location2.lon
    return math.sqrt((dLat * dLat) + (dLon * dLon)) * 1.113195e5


# Gets the current waypoint and calculates the distance
def distance_to_current_waypoint():
    nextWayPoint = vehicle.commands.next
    # Returns None for the first waypoint (Home Location)
    if nextWayPoint == 0:
        return None
    missionItem = vehicle.commands[nextWayPoint - 1]
    lat = missionItem.x
    lon = missionItem.y
    alt = missionItem.z
    targetWaypointLocation = LocationGlobalRelative(lat, lon, alt)
    distanceToPoint = get_distance_metres(vehicle.location.global_frame,
                                          targetWaypointLocation)
    return distanceToPoint


# Gets the missions from the vehicle
def get_vehicle_mission():
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()


# Creates and uploads dummy missions to vehicle
def adds_mission(location, size):
    cmds = vehicle.commands
    cmds.clear()

    # MAVLink automatic takeoff command
    cmds.add(Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                     mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0,
                     0, 10))
    # Dummy points for drone to fly too
    point1 = get_location_metres(location, size, -size)
    point2 = get_location_metres(location, size, size)
    point3 = get_location_metres(location, -size, size)
    point4 = get_location_metres(location, -size, -size)

    # Add waypoint commands via MAVLink
    cmds.add(Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                     mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0,
                     point1.lat, point1.lon, 11))
    cmds.add(Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                     mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0,
                     point2.lat, point2.lon, 12))
    cmds.add(Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                     mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0,
                     point3.lat, point3.lon, 13))
    cmds.add(Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                     mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0,
                     point4.lat, point4.lon, 14))
    # Destination confirmation
    cmds.add(Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                     mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0,
                     point4.lat, point4.lon, 15))

    print("Uploading waypoints to vehicle")
    cmds.upload()


# Function is intended for copter drones, gliders may not be supported
# Arms and initiates takeoff of the vehicle
def arm_and_takeoff(targetAltitude):
    print("Basic pre-arm checks")
    while not vehicle.is_armable:
        print("Initialising vehicle, please wait...")
        time.sleep(1)

    print("Arming motors")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print("Arming vehicle...")
        time.sleep(1)

    print("Attempting takeoff")
    vehicle.simple_takeoff(targetAltitude)

    while True:
        print("Rising, Altitude: ", vehicle.location.global_relative_frame.alt)
        if vehicle.location.global_relative_frame.alt >= targetAltitude*0.95:
            print("Reached target altitude")
            break
        else:
            time.sleep(1)


# Prints vehicle mission data for monitoring purposes
print("Creating dummy mission")
adds_mission(vehicle.location.global_frame, 100)

# Vehicle flies up to an altitude of 10 meters
arm_and_takeoff(10)

print("Starting dummy mission")
vehicle.commands.next = 0
vehicle.mode = VehicleMode("AUTO")

while True:
    nextWayPoint = vehicle.commands.next
    print("Distance to waypoint %s: %s lat: %s lon: %s" % (nextWayPoint,
                                                           distance_to_current_waypoint(),
                                                           vehicle.location.global_relative_frame.lat,
                                                           vehicle.location.global_relative_frame.lon))
    if nextWayPoint == 5:
        print("Destination reached, returning to original launch location")
        break
    time.sleep(1)

print("Returning to original launch location")
vehicle.mode = VehicleMode("RTL")


# Close vehicle object before exiting script
print("Close vehicle object")
vehicle.close()

if sitl is not None:
    sitl.stop()
