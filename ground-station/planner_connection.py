from pymavlink import mavutil
import threading

class PlannerConnection():

    def __init__(self):
        self.flight_serv = None
        print("Init planner")
        # Listen for connection from mission planner
        #self.conn = mavutil.mavlink_connection("tcpin:localhost:5000", planner_format=True, notimestamps=True, robust_parsing=True)
        self.conn = mavutil.mavlink_connection("tcpin:localhost:5000", planner_format=True, notimestamps=True, robust_parsing=True)
        self.should_exit = False

        receive_thread = threading.Thread(target=self.receive_thread, args=())
        receive_thread.start()

    def receive_thread(self):
        print("planner receive thread")
        while not self.should_exit:
            # Receive message from mission planner
            msg = self.conn.recv_match(blocking=False)
            if msg == None:
                continue
            print("Message from mission planner: ", msg)
            if self.flight_serv != None:
                # When a message from MP is received, forward it to the flight computer
                self.flight_serv.send_mavlink(msg) 

    def shutdown(self):
        print("Planner shutdown")
        self.conn.close()
        self.should_exit = True
        #self.conn.shutdown(socket.SHUT_RDWR)

    # Send message to MP
    def send_mavlink(self, msg):
        #print("sending message to MP")
        self.conn.mav.send(msg)
