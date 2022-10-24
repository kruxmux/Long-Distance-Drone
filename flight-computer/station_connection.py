import socket, pickle, threading, struct,time
from msg_constants import *
from datetime import datetime
import os
import subprocess
import signal



# Grab the next value in the bytearray. The 'fmt' parameter specifies what datatype the value is
def next_value(self, fmt, received_bytes):
    n = struct.calcsize(fmt)
    value_bytes = received_bytes[:n] # Grab the bytes that make up this value
    value = struct.unpack(fmt, value_bytes) # Convert the value from bytes to the datatype
    remaining_bytes = received_bytes[n:]
    return (value[0], remaining_bytes)

# Collects requested bytes and outputs what how many were recieved and how many
# are remaining
def wait_for_bytes(size, connection, receivedBytes):
    while len(receivedBytes) < size:
        print("Waiting for more bytes. Has %s of %s" % ( len(receivedBytes), size))
        try:
            moreBytes = bytearray(connection.recv(16384))
        except Exception as e:
            return None, 0
        if len(moreBytes) == 0:
            print("Received 0 bytes")
            return None, 0
        receivedBytes.extend(moreBytes)

    requestedBytes = receivedBytes[:size]
    remaining = receivedBytes[size:]
    return requestedBytes, remaining

 # Makes sure we have n bytes before continuing
def wait_for_value(fmt, connection, receivedBytes):

    size = struct.calcsize(fmt)

    value_bytes, remaining = wait_for_bytes(size, connection, receivedBytes)
    if value_bytes == None:
        return None, 0

    value = struct.unpack(fmt, value_bytes)[0]
    #print("value: ", value)

    return value, remaining

# Facilitates a connection to the groundstation
class StationConnection:

    def __init__(self):
        self.flight_controller = None
        while True:
            try:
                self.connect()
                break
            except Exception as e:
                print("Failed to connect. Retrying...", str(e))
        self.last_message_received = datetime.now()
        print("last_message_received: ", self.last_message_received)
        self.socket_lock = threading.Lock()

        receive_thread = threading.Thread(target=self.receive_thread, args=())
        receive_thread.daemon = True
        receive_thread.start()

        connection_watch_thread = threading.Thread(target=self.connection_watch_thread, args=())
        connection_watch_thread.daemon = True
        connection_watch_thread.start()

    # Open a connection to the groundstation
    # TODO: Replace localhost with an static IP-address when available
    def connect(self):
        self.last_message_received = datetime.now() #reset connect timeout
        #HOST = "localhost"
        HOST = "10.6.0.3"
        #HOST = "10.6.0.4"
        #HOST = "192.168.43.136"
        #HOST = "10.0.138.157"
        PORT = 6000
        new_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        print("connecting")
        new_conn.settimeout(10)
        new_conn.connect((HOST, PORT))
        new_conn.settimeout(None) # Go back to non blocking socket
        self.conn = new_conn
        print("connected")

        # UDP
        #self.conn.send(struct.pack(FMT_BYTE, 0))


    # Background thread that checks if the connection to the server is alive
    def connection_watch_thread(self):
        while True:

            # Try to reconnect if no message has been received for 20 seconds
            MAX_SECONDS = 20
            time_since_last_message = datetime.now() - self.last_message_received
            seconds = time_since_last_message.total_seconds()
            if seconds > MAX_SECONDS and self.conn is not None:
                print("No message received for %s seconds" % MAX_SECONDS)
                # Close connection. Reconnection will be handled below
                self.close()

            if self.conn == None:
                try:
                    self.connect()
                    print("Trying to reconnect")
                except Exception as e:
                    print("Failed to reconnect", str(e))
            time.sleep(1)

    # Receive message from ground station
    def receive_thread(self):
        c = 0
        print("Starting receive from ground station thread")
        spillover_bytes = bytearray()

        cmd = "raspivid -n -t 0 -rot 180 -w 960 -h 720 -fps 30 -b 2000000 -co 60 -sh 30 -sa 10 -o - | gst-launch-1.0 -e -vvvv fdsrc ! h264parse ! rtph264pay pt=96 config-interval=5 ! udpsink host=10.6.0.3 port=5000"
        gstr = subprocess.Popen(cmd,stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        print("Starting Gstreamer")

        while True:
            c+=1
            if self.conn != None:
                data = bytearray()
                data.extend(spillover_bytes)

                # Check message type
                msg_type, data = wait_for_value(FMT_BYTE, self.conn, data)
                print("msg_type: ", msg_type)
                if msg_type == None:
                    self.close()
                    continue

                length, data = wait_for_value(FMT_UINT, self.conn, data)
                if length == None:
                    self.close()
                    continue

                self.last_message_received = datetime.now()

                if msg_type == MSG_TYPE_RADIO_ERROR:
                    print("Received radio error")
                    if self.flight_controller is not None:
                        if self.flight_controller.connection.mode.name != "LOITER":
                            self.flight_controller.set_flight_mode("LOITER")

                if msg_type == MSG_TYPE_SET_FLIGHT_MODE:
                    mode_id, data = wait_for_value(FMT_BYTE, self.conn, data)
                    print("Received new flight mode: ", mode_id)
                    mode_name = mode_id_to_name[mode_id]

                    if self.flight_controller is not None:
                        self.flight_controller.set_flight_mode(mode_name)

                if msg_type == MSG_TYPE_VIDEO_LOW:
                    #self.flight_controller.set_flight_mode("RTL")
                    print("SET LOW QUALITY")
                    os.killpg(os.getpgid(gstr.pid), signal.SIGINT) #Kill earlier pipeline
                    cmd = "raspivid -n -t 0 -rot 180 -w 320 -h 240 -fps 30 -b 250000 -co 60 -sh 50 -sa 10 -o - | gst-launch-1.0 -e -vvvv fdsrc ! h264parse ! rtph264pay pt=96 config-interval=5 ! udpsink host=10.6.0.3 port=5000"
                    gstr = subprocess.Popen(cmd,stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)



                if msg_type == MSG_TYPE_VIDEO_MED:
                    #self.flight_controller.set_flight_mode("RTL")
                    print("SET MED QUALITY")
                    os.killpg(os.getpgid(gstr.pid), signal.SIGINT)
                    cmd = "raspivid -n -t 0 -rot 180 -w 640 -h 480 -fps 30 -b 600000 -co 60 -sh 40 -sa 10 -o - | gst-launch-1.0 -e -vvvv fdsrc ! h264parse ! rtph264pay pt=96 config-interval=5 ! udpsink host=10.6.0.3 port=5000"
                    gstr = subprocess.Popen(cmd,stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)



                if msg_type == MSG_TYPE_VIDEO_HIGH:
                    #self.flight_controller.set_flight_mode("RTL")
                    print("SET HIGH QUALITY")
                    os.killpg(os.getpgid(gstr.pid), signal.SIGINT)
                    cmd = "raspivid -n -t 0 -rot 180 -w 960 -h 720 -fps 30 -b 2000000 -co 60 -sh 30 -sa 10 -o - | gst-launch-1.0 -e -vvvv fdsrc ! h264parse ! rtph264pay pt=96 config-interval=5 ! udpsink host=10.6.0.3 port=5000"
                    gstr = subprocess.Popen(cmd,stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)



                if msg_type == MSG_TYPE_RADIO:
                    #self.flight_controller.set_flight_mode("FBWA")
                    if self.flight_controller.connection.mode.name != "FBWA":
                        self.flight_controller.set_flight_mode("FBWA")
                    NUM_CHANNELS = 6
                    channels = []
                    for i in range(6):
                        channel, data = wait_for_value(FMT_USHORT, self.conn, data)
                        if channel == None:
                            print("channel is NONE")
                            #self.close()
                            pass
                            continue
                        channels.append(channel)

                    if len(channels) != NUM_CHANNELS:
                        print("Not matching number of expected channels. Something has gone wrong with the connection")
                        #self.close()
                        pass
                        continue

#
                    # Override to flight controller if connection has been established
                    if self.flight_controller != None:
                        #for i in range(6):
                       # self.flight_controller.connection.channels.overrides[i+1] = channel[i]
                        print("channel:", str(channel))
                        self.flight_controller.connection.channels.overrides[1] = channels[0]
                        self.flight_controller.connection.channels.overrides[2] = channels[1]
                        self.flight_controller.connection.channels.overrides[3] = channels[2]
                        self.flight_controller.connection.channels.overrides[4] = channels[3]
                        self.flight_controller.connection.channels.overrides[5] = channels[4]
                        #skip 5 because its dedicated to flight modes on radio
                        self.flight_controller.connection.channels.overrides[6] = channels[5]

			#self.flight_controller.connection.flush()
                        #mode = self.flight_controller.connection.mode
                        #print("wrote", mode)
                    else:
                        print("Override failed because FC is None")

                elif msg_type == MSG_TYPE_MAVLINK: # Receive a mavlink message from ground station
                    payload, data = wait_for_bytes(length, self.conn, data)
                    if payload == None:
                        self.close()
                        continue
                    msg = pickle.loads(payload)
                    print(msg)
                    if self.flight_controller is not None:
                        self.flight_controller.send_mavlink(msg)


                elif msg_type == MSG_TYPE_PING_REQUEST:
                    self.send_ping_status()

                spillover_bytes = data



    # Send ping response. Some info about the flight computer is included in the ping message, such as current flight mode
    def send_ping_status(self):
        # Include mode id in ping message
        if self.flight_controller is not None:
            mode_id = mode_id_to_name.index(self.flight_controller.connection.mode.name) # get mode id from string name
        else:
            mode_id = mode_id_to_name.index("UNKNOWN")
        print("sending mode id : ", mode_id)

        payload = bytearray()
        payload.extend(struct.pack(FMT_BYTE, mode_id))

        self.send_message(MSG_TYPE_PING_RESPONSE, payload)


    def send_test_message(self):
        f = open("msg.dump", "rb")
        data = f.read()
        self.conn.send(data)

    # Sends a mavlink-message to the groundstation
    def send_mavlink(self, msg):
        payload = pickle.dumps(msg)
        #f = open("msg.dump", "wb+")
        #f.write(payload)
        if len(payload) < 100:
            print("wrong length on payload", msg)
        self.send_message(MSG_TYPE_MAVLINK, payload)


    # Sends a message in form of a bytearray to the groundstation
    def send_message(self, msg_type, payload):
        data = bytearray()
        # add msg type
        data.extend(struct.pack(FMT_BYTE, msg_type))
        # add payload length
        data.extend(struct.pack(FMT_UINT, len(payload)))
        data.extend(payload)
        if self.conn == None:
            print("Failed to send message of type %s because self.conn is None" % msg_type)
            return

        self.socket_lock.acquire()
        try:
            self.conn.sendall(data)
        except Exception as e:
            print("Failed to send message with exception %s" % str(e))
            self.close()

        self.socket_lock.release()

    # TODO: try to reconnect when we have lost connection to server
    def close(self):
        # Return to landing when connection is closed
        if self.flight_controller is not None:
            self.flight_controller.set_flight_mode("RTL")
        print("Connection with server closed")
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
            self.conn.close()
        except Exception as e:
            print("Failed to close connection to server properly", str(e))
        self.conn = None
