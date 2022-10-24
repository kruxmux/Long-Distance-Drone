from Tkinter import *
from PIL import ImageTk,Image
from time import sleep
import datetime, ctypes, os, signal, threading, subprocess, tkMessageBox
import socket, pickle, sys

from flight_server import FlightServer
from planner_connection import PlannerConnection
from decoder import Decoder
from constants import *

class GUIWINDOW:
    def ask_quit(self):
        if tkMessageBox.askokcancel("Quit", "Quit this program?"):
            if self.RC_decoder != None:
                self.RC_decoder.close()
            self.flight_serv.shutdown()
            self.planner.shutdown()
            self.root.destroy()
            sys.exit(0)

    def __init__(self, rcFlag, dec_port):
        # Following code is just GUI design
        #-- Root window
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.ask_quit)

        #-- Height and width of the window is decided by current resolution
        try:
            WIDTH = int(ctypes.windll.user32.GetSystemMetrics(0) * 0.5)
            HEIGHT =  int(ctypes.windll.user32.GetSystemMetrics(1) * 0.6)
        except: # Linux
            WIDTH = 800
            HEIGHT = 800


        # Ground station things
        self.USE_DECODER = rcFlag # True if Arduino is connected
        self.RC_decoder = None
        self.HOST = "localhost"
        self.PORT = 6000

        self.planner = PlannerConnection()
        self.flight_serv = FlightServer(self)
        self.planner.flight_serv = self.flight_serv
        self.flight_serv.planner = self.planner

        if self.USE_DECODER:
            self.RC_decoder = Decoder(self.flight_serv, dec_port)

        self.MODEVAR = StringVar()
        self.MODEVAR.set("Current mode: UNKNOWN")

        self.PINGVAR = StringVar()
        self.PINGVAR.set("Ping: 0")

        self.endFlag = IntVar()
        self.gst = 0
        self.playerFlag = False


        #-- If row or col is not specified it's 0.
        INFOCOL = 0
        TEXTCOL = 1
        BTNCOL = 2
        MODECOL = 3
        #IMAGECOL = 4

        #-- Settings for root window
        self.root.geometry(str(WIDTH) + "x" + str(HEIGHT))
        self.root.title("Drone GUI")
        self.root.resizable(False, False)

        #-- List of tuples, first = name of the button, second = name of handler
        player_names = [
                    ("Open", self.openplayer_handler),
                    ("Close", self.closeplayer_handler)
                    ]

        quality_names = [
                    ("LOW", self.lowvid_handler),
                    ("MEDIUM", self.medvid_handler),
                    ("HIGH", self.highvid_handler)
        ]
        btnframe = LabelFrame(self.root, text="Video Controls",font ="Helvetica 12 bold", padx = 5, pady = 5)
        Label(btnframe,text="Video Window", font ="Helvetica 10").grid(row=1)

        self.add_buttons_to_frame(player_names,btnframe,2)
        Label(btnframe,text="Video Quality", font ="Helvetica 10").grid(row=4)
        self.add_buttons_to_frame(quality_names,btnframe,5)



        #-- Container for info
        infoframe = Frame(self.root, height = 400, width = 150, bg = "black")
        infoframe.pack_propagate(False)



        modelabel = Label(infoframe, textvariable=self.MODEVAR,fg='#4ee44e', bg="black")
        modelabel.pack()

        modelabel = Label(infoframe, textvariable=self.PINGVAR,fg='#4ee44e', bg="black")
        modelabel.pack()

        #-- Container for modes
        modeframe = LabelFrame(self.root, text="Flight Modes",font ="Helvetica 12 bold", padx = 5, pady = 5)

        modebtnnames = [("FBWA (assisted)",self.fbwa_handler),("RTL",self.rtl_handler),("Loiter",self.loiter_handler)]
        modeframe.pack_propagate(False)
        self.add_buttons_to_frame(modebtnnames, modeframe,1)

        #-- Text window
        textframe = Frame(self.root, height = 400, width = 300)
        textframe.pack_propagate(False)

        self.T = Text(textframe)
        scrollbar = Scrollbar(textframe)
        scrollbar.config(command = self.T.yview)
        scrollbar.pack(side =RIGHT, fill=Y)
        checkbtn = Checkbutton(textframe, text="Autoscroll", variable=self.endFlag)
        checkbtn.pack(side = TOP)
        self.T.pack()




        #-- Adding the frames to root
        textframe.grid(row = 0, column = TEXTCOL, rowspan = 1, padx = 10, pady = 10, sticky=NSEW)
        infoframe.grid(row = 0, column = INFOCOL, padx = 10, pady = 10, sticky=N+W)
        btnframe.grid(row = 0, column = BTNCOL, sticky = N)
        modeframe.grid(row = 0, column = MODECOL, rowspan = 4, sticky = N, padx = 10)

        self.root.after(5000,self.my_mainloop)
        self.root.mainloop()



    def send_text_to_window(self, msg):
        time = str(datetime.datetime.now().time())
        time = time[0:5]
        if len(msg) > 37:
            self.T.insert(END,"[" + time + "] " +  msg + "\n\n")
        else:
            self.T.insert(END,"[" + time + "] " + msg + "\n")
        if self.endFlag.get() == 1:
            self.T.see("end")




    # -- Controll button handlers

    def lowvid_handler(self):
        self.flight_serv.send_message(MSG_TYPE_VIDEO_LOW, bytearray())
        self.send_text_to_window("Changing to low quality")


    def medvid_handler(self):
        self.flight_serv.send_message(MSG_TYPE_VIDEO_MED, bytearray())
        self.send_text_to_window("Changing to medium quality")


    def highvid_handler(self):
        self.flight_serv.send_message(MSG_TYPE_VIDEO_HIGH, bytearray())
        self.send_text_to_window("Changing to high quality")


    # -- Mode button handlers
    def fbwa_handler(self):
        self.flight_serv.send_flight_mode("FBWA")
        self.send_text_to_window("Attempting to set mode FBWA...")


    def rtl_handler(self):
        self.flight_serv.send_flight_mode("RTL")
        self.send_text_to_window("Attempting to set mode RTL...")


    def loiter_handler(self):
        self.flight_serv.send_flight_mode("LOITER")
        self.send_text_to_window("Attempting to set mode Loiter...")



    # Handler for opening a video connection
    def openplayer_handler(self):
        #probably broken

        if self.playerFlag == False:
            self.send_text_to_window("Starting gStreamer...")

            cmd = ["gst-launch-1.0.exe", "-e", "-v", "udpsrc", "port=5000", "!", "application/x-rtp," "payload=96", "!", "rtpjitterbuffer", "!", "rtph264depay", "!", "avdec_h264", "!", "fpsdisplaysink", "sync=false", "text-overlay=false"]

            self.gst = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            self.playerFlag = True
        else:
            self.send_text_to_window("Player is already launched")

    # Handler for closing the video connection
    def closeplayer_handler(self):

        if self.gst != 0:
            #specifically for windows
            subprocess.Popen("TASKKILL /F /PID {pid} /T".format(pid=self.gst.pid))
            self.gst = 0
            self.playerFlag = False
        self.send_text_to_window("gStreamer stopped")




    #-- mainloop, if we need to react to something we can do it here, ex read some input.
    def my_mainloop(self):
        #send_text_to_window("Woho")
        self.root.after(5000,self.my_mainloop)

    #-- first arg = [("Button name",func name)], second arg = tkinter frame to add buttons to
    def add_buttons_to_frame(self, btn_tuple_list, frame, start_row):
        i = start_row
        for name_handler_tuple in btn_tuple_list:
            Button(frame, text=name_handler_tuple[0], command=name_handler_tuple[1]).grid(
                row=i, column=0, sticky=E+W, pady=2)
            i += 1
