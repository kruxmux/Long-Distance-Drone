from flight_controller_handler import FlightController
from station_connection import StationConnection
import os


# What is going to happen:
# 1. Open a connection to APM/Pixhawk through USB
# 2. Connect to the groundstation and recieve mavlink messages
# 3. Send the messages directly to the APM/Pixhawk
# 4. Read the camera and send frames to the groundstation
# 5. Listen to mavlink messages from APM/Pixhawk and send these to the groundstation


def startup():
    #Connect to VPN
    os.system("wg-quick up droneuser")

    # Connect to the Vehicle.

    station = StationConnection()

    #station.send_test_message()
    flight_controller = FlightController(station)

    print("setting fc")
    station.flight_controller = flight_controller

    #msg = flight_controller.connection.message_factory.manual_control_encode(
        #0,    # system to be controlled
        #100,
        #100,
        #100,
        #100,
        #0)    # buttons

    #station.send_message(msg)


# Construct and send mavlink message
# Changes the mode of the vehicle
def send_mode_message(controller):
    msg = controller.message_factory.set_mode_encode(
        0,    # system to be controlled
        192,
        0)
    controller.send_mavlink(msg)
    controller.flush()
    print("sent message to change mode")


# Send message for manual steering
# Takes in pitch, roll, thrust and yaw as floats
# TODO: Check if it is float that is used
def send_manual_control_message(controller, pitch, roll, thrust, yaw):
    msg = controller.message_factory.manual_control_encode(
        0,    # system to be controlled
        pitch,
        roll,
        thrust,
        yaw,
        0)    # buttons
    controller.send_mavlink(msg)
    controller.flush()
    print("sent message with manual control")


def close():
    #TODO close all connections
    pass


if __name__ == '__main__':
    startup()

    while True:
        try:
            pass
        except KeyboardInterrupt:
            station.close()
            #flight_controller.close()
            break
    # Close vehicle object before exiting script
    vehicle.close()
