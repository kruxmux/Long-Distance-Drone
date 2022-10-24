import serial, threading, time
#import dronegui






class Decoder():

    def __init__(self, flight_serv, port):
        # Connect arduino (Switch to appropriate port)
        self.decoder = serial.Serial(port, 115200, timeout=.1)
        self.read_thread = threading.Thread(target=self.read_thread, args=())
        self.read_thread.daemon = True
        self.read_thread.start()
        self.should_exit = False
        self.flight_serv = flight_serv

    def read_thread(self):
        isConnected = False
        c = 0
        while True:
            try:
                data = self.decoder.readline()[:-2].split() #readline is blocking, has timeout
                #print("data:", str(data))
            except Exception as e:
                print("Error reading decoder", str(e))
                continue
            #print(data)
            if data:
                c += 1
                if data[0] == "Error:":
                    # Send message abt flight mode change?
                    #if c % 30 == 0:
                    if isConnected:
                        self.flight_serv.send_RC_error()
                        self.flight_serv.gui.send_text_to_window("Transmitter disconnected!")
                        isConnected = False
                    pass
                elif len(data) > 5:
                    # Send channel values
                    self.flight_serv.send_RC(data[0], data[1], data[2], data[3], data[4], data[5])
                    c = 0
                    if not isConnected:
                        self.flight_serv.gui.send_text_to_window("Transmitter connected!")
                        isConnected = True
                    #time.sleep(0.05)
                    pass
                    #print("Sent data")

    def close(self):
        self.decoder.close()
