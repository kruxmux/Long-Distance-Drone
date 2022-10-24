import threading, socket, struct, time, pickle, select
#import dronegui
from constants import *


def next_value(fmt, bytesList):
    n = struct.calcsize(fmt)
    valueBytes = bytesList[:n]
    value = struct.unpack(fmt, valueBytes)
    newList = bytesList[n:]
    return (value[0], newList)

# Makes sure we have n bytes before continuing
def wait_for_value(fmt, connection, received_bytes):

    size = struct.calcsize(fmt)

    value_bytes, remaining, addr = wait_for_bytes(size, connection, received_bytes)
    if value_bytes == None:
        return None, 0, None

    value = struct.unpack(fmt, value_bytes)[0]
    #print("value: ", value)

    return value, remaining, addr

# Waits until n bytes has been recieved
def wait_for_bytes(size, connection, received_bytes):
    addr = None

    #print("print")
    MAX_WAIT = 5
    WAIT_TIME = 0.01

    while len(received_bytes) < size:
	has_received_bytes = False
	time_waited = 0.0
	while not has_received_bytes:
            if time_waited >= MAX_WAIT:
		print("Waited for more than 5 sec for a message... not good")
		return None, 0, None
	    try:
                #print("before")
		more_bytes = connection.recv(16384)
                # print("more_bytes: ", len(more_bytes))
                if len(more_bytes) == 0: #TODO close client
                    #print("Received 0 bytes")
                    return None, 0, None
                # print("after")
                has_received_bytes = True
	    except Exception as e:
		#print("Error receiving data with recv", str(e), time_waited)
		time.sleep(WAIT_TIME)
		time_waited += WAIT_TIME
		#print("time_waited: ", time_waited)
		continue

        received_bytes.extend(more_bytes)

    requested_bytes = received_bytes[:size]
    remaining = received_bytes[size:]
    return requested_bytes, remaining, addr



class FlightServer:

    def __init__(self, gui):
        HOST = ""
        PORT = 6000
        self.conn = None
        self.planner = None
        self.prev_channels = None
        self.addr = None
        self.should_exit = False
        self.gui = gui

        # Variables for calcualting data usage
        self.total_number_of_bytes = 0
        self.start_time = int(time.time())
        self.num_msg = 0

        #s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))

        s.listen(1)
        self.server_sock = s
        #msg, self.addr = s.recvfrom(1024) # TODO: move somewhere else
        #self.conn = s
        self.ping_time = 0

        self.accept_thread = threading.Thread(target=self.accept_thread, args=())
        self.accept_thread.daemon = True
        self.accept_thread.start()

        self.receive_thread = threading.Thread(target=self.receive_thread, args=())
        self.receive_thread.start()

        self.ping_thread = threading.Thread(target=self.ping_thread, args=())
        self.ping_thread.start()


    # Used only if we go back to TCP connection
    def accept_thread(self):
        while not self.should_exit:
            print("running accept thread")
            new_conn, self.addr = self.server_sock.accept()
            if self.conn != None:
                self.gui.send_text_to_window("Shutting down old connection...")
                try:
                    self.conn.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                self.conn.close()
                self.conn = None
                # sleep needed for stable reconnections. Don't know why
                time.sleep(5)

	    new_conn.setblocking(0)
            self.conn = new_conn
            self.gui.send_text_to_window("A new connection was established")
            print("new conn", self.addr)
            print("new conn", self.conn)
        print("Accept thread closed")

    # Prints statistics of the data usage
    def calc_data_usage(self, length):
        self.num_msg += 1
        self.total_number_of_bytes += length
        running_time = int(time.time()) - self.start_time
        print("running_time", running_time)
        print("total_number_of_bytes", self.total_number_of_bytes)
        print("num_msg", self.num_msg)

        if running_time == 0:
            return

        bytes_per_sec = float(self.total_number_of_bytes/running_time)
        megabytes_per_sec = bytes_per_sec/1000000.0
        print("Using on avg %s megabytes/second" % (megabytes_per_sec))
        print("Using on avg %s megabytes/minute" % (megabytes_per_sec*60))
        print("Avg  %s msg / second" % (self.num_msg/running_time))

    def close_client(self):
        print("Closing connection with client")
        self.gui.send_text_to_window("Closing connection with client")
        if self.conn != None:
            try:
                self.conn.shutdown(socket.SHUT_RDWR)
            except:
                pass
            self.conn.close()
        self.conn = None

    # Here we will receive data from the drone
    def receive_thread(self):
        print("Starting thread for receiving from drone")

        spillover_bytes = bytearray()
        while not self.should_exit:

            if self.conn != None:
                data = bytearray()
                data.extend(spillover_bytes) # Add the bytes that were left over from the previous receive loop

                msg_type, data, addr = wait_for_value(FMT_BYTE, self.conn, data)
                #print("msg_type: ", msg_type)
                if msg_type == None:
                    #self.close_client()
                    continue

                length, data, addr = wait_for_value(FMT_UINT, self.conn, data)
                #print("length: ", length)
                if length == None:
                    #self.close_client()
                    continue

                #self.calc_data_usage(length)

                #print msg_type
                if msg_type == MSG_TYPE_MAVLINK:
                    payload, data, addr = wait_for_bytes(length, self.conn, data)
                    if payload == None:
                        #self.close_client()
                        continue

                        #print("len:" , len(payload))
                    #print("len:" , (length))
                    try:
                        msg = pickle.loads(payload)
                    #print(msg.name)
                        #debug
                        if msg.name == "COMMAND_ACK":
                            #print("received ack message", str(msg))
                            pass

                        if self.planner != None:
                            self.planner.send_mavlink(msg) # Forward the received message to mission planner
                    except Exception:
                        pass

                elif msg_type == MSG_TYPE_PING_RESPONSE:
                    ping = int(time.time()*1000) - self.ping_time
                    print("ping: %s ms" % ping)
                    payload, data, addr = wait_for_bytes(length, self.conn, data)
                    try:
                        mode_id, payload = next_value(FMT_BYTE, payload)
                    except Exception:
                        print("next_value failed")
                    #mode_id, data, addr = wait_for_value(FMT_BYTE, self.conn, data)
                    print("mode_id: ", mode_id)
                    print("payload len: ", len(payload))
                    print("current flight mode: ", mode_id_to_name[mode_id])
                    self.gui.PINGVAR.set("Ping: " + str(ping))
                    self.gui.MODEVAR.set("Current mode: " + mode_id_to_name[mode_id])

                else:
                    print("Unknown msg type. Serious issue")


                # The remaining bytes belong to the next message. Save them so that we can add them to the next message
                spillover_bytes = data
                #print("spillover_bytes: ", len(spillover_bytes))
        print("Receive thread closed")

    # Sends an error message
    def send_RC_error(self):
        self.send_message(MSG_TYPE_RADIO_ERROR, bytearray())

    # Send RC-signals to appropriate channels if formatted correctly
    def send_RC(self, *channels):
        if len(channels) != 6:
            print("Wrong number of channels in send_RC")

        should_send = True

        # Send only if the the value of one channel has changed more than the threshold
        """
        if self.prev_channels != None:
            for i in range(len(channels)):
                if abs(int(channels[i]) - int(self.prev_channels[i])) >= 10:
                    should_send = True
        else:
            should_send = True
        """
        if not should_send:
        #    print("not sending RC")
            return

        payload = bytearray()

        try:
            #payload.extend(struct.pack("!Q", long(time.time()*1000)))
            for channel in channels:
                payload.extend(struct.pack(FMT_USHORT, int(channel)))
            self.send_message(MSG_TYPE_RADIO, payload)
            self.prev_channels = channels
            #print("Sent successfully")
        except Exception as e:
            print(str(e))
    #        pass

    # Send message to set flight mode
    def send_flight_mode(self, mode_name):
        mode_id = mode_id_to_name.index(mode_name)
        print("mode_id: ", mode_id)
        print("send mode id %s  %s" % (mode_id, mode_name))
        payload = bytearray()
        payload.extend(struct.pack(FMT_BYTE, mode_id))
        self.send_message(MSG_TYPE_SET_FLIGHT_MODE, payload)

    # Send mavlink-message
    def send_mavlink(self, msg):
        payload = pickle.dumps(msg)
        self.send_message(MSG_TYPE_MAVLINK, payload)

    # Send argument message
    def send_message(self, msg_type, payload):
        data = bytearray()
        # add msg type
        data.extend(struct.pack(FMT_BYTE, msg_type))
        # add payload length
        data.extend(struct.pack(FMT_UINT, len(payload)))
        # add the payload
        data.extend(payload)

        #self.conn.sendto(data, self.addr)
        if self.conn == None:
            print("Failed to send message type %s because self.conn is None" % msg_type)
        else:
            try:
                self.conn.sendall(data)
            except Exception as e:
                print("Failed to send message", str(e))
                self.gui.send_text_to_window("Failed to send message because client closed connection")
                #self.close_client()

    def ping_thread(self):
        while not self.should_exit:
            print("send ping")
            self.send_ping()
            time.sleep(3)

        print("Ping thread closed")

    # Shuts down the flight server
    def shutdown(self):
        print("Received shutdown")
        self.should_exit = True
        self.close_client()
        try:
            self.server_sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            print("Couldn't close server_sock properly")
        self.server_sock.close()
        print("closed server sock")

    # Pings the connection
    def send_ping(self):
        self.ping_time = int(time.time()*1000)
        self.send_message(MSG_TYPE_PING_REQUEST, bytearray())
