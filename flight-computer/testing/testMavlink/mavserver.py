from pymavlink import mavutil
from dronekit import connect

def onAPMMessage(self, name, msg):
    print(" message name: ", name, msg)
    plannerConnection.mav.send(msg)
    try:
        pass
    except Exception as e:
        pass
        #print("erroro on message name: ", name, str(e), msg)

    #print(msg.severity)
    #print(type(msg))
    #print("msg: ", name)

# change to tcpin:yourLocalIP:5000
plannerConnection = mavutil.mavlink_connection("tcpin:localhost:5000", planner_format=True, notimestamps=True, robust_parsing=True)

apmConnection = connect("/dev/ttyACM0", wait_ready=True, baud=115200)

apmConnection.add_message_listener("*", onAPMMessage)

print(type(plannerConnection.mav))

print("Connection: ", plannerConnection )
while True:
    print("Waiting")
    msg = plannerConnection.recv_match(blocking=True)
    try: 
        apmConnection.send_mavlink(msg)
    except Exception as e:
        pass
        print("error on:")
        print(type(msg))
        print(msg.name)

    # Needed for keeping MP session alive
    #plannerConnection.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER, mavutil.mavlink.MAV_AUTOPILOT_INVALID,0,0,0)




