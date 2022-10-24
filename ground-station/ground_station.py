import socket, pickle, time, sys

from pymavlink import mavutil
from flight_server import FlightServer
from planner_connection import PlannerConnection
from decoder import Decoder
#from planner_connection import FlightServer
import serial
from constants import *
import gui_as_class

# Ground station things
USE_DECODER = False # True if Arduino is connected
RC_decoder = None
HOST = "localhost"
PORT = 6000


def startup():

    planner = PlannerConnection()
    flight_serv = FlightServer(None)
    planner.flight_serv = flight_serv
    flight_serv.planner = planner

    if USE_DECODER:
        RC_decoder = Decoder(flight_serv)





if __name__ == "__main__":
    startup()

while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print("Received keyboard interupt")
        flight_serv.shutdown()
        planner.shutdown()
        sys.exit(0)
        break
