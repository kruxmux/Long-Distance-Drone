
import time, serial, glob

from dronekit import connect, VehicleMode, Command
from pymavlink import mavutil



class FlightController:

    def __init__(self, station):
        self.station = station
        print("Connecting to pixhawk")
        devices = []
        # Look for Pixhawk that is connected by USB
        while len(devices) < 2: # Pixhawk shows up as two devices. The one with lower ID is the right one
            print("Looking for Pixhawk serial device")
            devices = glob.glob("/dev/ttyACM*")
            devices.reverse()
            print("devices: ", devices)

            time.sleep(0.5)

        port = devices[0]
        vehicle = connect(port, wait_ready=True, baud=115200)


        # Get some vehicle attributes (state)
        print("GPS: %s" % vehicle.gps_0)
        print("Battery: %s" % vehicle.battery)
        print("Last Heartbeat: %s" % vehicle.last_heartbeat)
        print("Is Armable?: %s" % vehicle.is_armable)
        print("System status: %s" % vehicle.system_status.state)
        print("Mode: %s" % vehicle.mode.name)   # settable)

        # Add listener in order to output mavlink messages to the terminal
        vehicle.add_message_listener('*', self.mavlink_msg_callback)

        print("mode: ", str(vehicle.mode))

        # Arming the vehicle (Done manually via the RC-Controller)
        print("Vehicle armed: %s" % vehicle.armed)
        while not vehicle.armed:
            print("Waiting for vehicle to be armed...")
            #vehicle.armed = True
            vehicle.flush()
            time.sleep(0.2)

        #vehicle.mode = VehicleMode("RTL")
        print("Vehicle armed!")
        self.connection = vehicle
        self.set_flight_mode("STABILIZE")
        #self.set_flight_mode("LAND (AUTO)")
        time.sleep(1)
        print("MODE:", vehicle.mode.name)

    # Sets the current mode and behaviour of the connected vehicle
    def set_flight_mode(self, mode):
        self.connection.mode = VehicleMode(mode)
        #self.station.send_current_flight_mode(self.connection.mode.name)

    # Send mavlink message to the flight controller
    def send_mavlink(self, msg):
        #self.connection.mav.send(msg)
        self.connection.send_mavlink(msg)

    # Listeners for information from the flight controller
    def mavlink_msg_callback(self, vehicle, attr_name, msg):
        #print("Received mavlink message from APM", str(msg), attr_name)
        if self.station != None:
            self.station.send_mavlink(msg) 
            pass

    def mode_callback(self, attr_name):
        print("Vehicle Mode", self.mode)
