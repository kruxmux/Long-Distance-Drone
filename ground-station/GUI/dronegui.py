from Tkinter import *
from PIL import ImageTk,Image
from time import sleep
import datetime
import ctypes
import os
import signal
import threading
import subprocess
import tkMessageBox

from planner_connection import PlannerConnection

# Change to True if you have arduino RC decoder connected
USE_DECODER = False

HOST = "localhost"
PORT = 6000

flight_serv = 0


def startup():
    planner = PlannerConnection()
    flight_serv = FlightServer()
    planner.flight_serv = flight_serv
    flight_serv.planner = planner

    if USE_DECODER:
        RC_decoder = Decoder(flight_serv)


#-- Quit confirmation
def ask_quit():
    if tkMessageBox.askokcancel("Quit", "Quit this program?"):
        flight_serv.shutdown()
        planner.shutdown()
        root.destroy()
        sys.exit()

#-- Controll button handlers
def arducopter_handler():
    send_text_to_window("ABCDEFGHIJKLMNOPqrstuvxyzAbCdEkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkfdkuivlasd") #37

def lowvid_handler():
    send_text_to_window("Changed to low quality")

def medvid_handler():
    send_text_to_window("Changed to medium quality")

def highvid_handler():
    send_text_to_window("Changed to high quality")

def stopvid_handler():
    send_text_to_window("Stopped video")

# Handler for opening a video connection
def openplayer_handler():
    global playerFlag
    if playerFlag == False:
        send_text_to_window("Starting gStreamer...")
        global gst
        cmd = ["gst-launch-1.0.exe", "-e", "-v", "udpsrc", "port=5000", "!", "application/x-rtp," "payload=96", "!", "rtpjitterbuffer", "!", "rtph264depay", "!", "avdec_h264", "!", "fpsdisplaysink", "sync=false", "text-overlay=false"]

        gst = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        playerFlag = True
    else:
        send_text_to_window("Player is already launched")

# Handler for closing the video connection
def closeplayer_handler():
    global gst
    if gst != 0:
        #specifically for windows
        subprocess.Popen("TASKKILL /F /PID {pid} /T".format(pid=gst.pid))
        gst = 0
        global playerFlag
        playerFlag = False
    send_text_to_window("gStreamer stopped")

# Handler for photo
def photo_handler():
    send_text_to_window("Photo saved to GUI/photos/")

# Hnadler for reboot
def reboot_handler():
    global REBOOTNR
    REBOOTNR +=1
    REBOOTVAR.set("Number of reboots: " + str(REBOOTNR))
    send_text_to_window("Reboot")

#-- Mode button handlers

def stabilize_handler():
    MODEVAR.set("Current mode: Stabilize")
    send_text_to_window("Changed mode to: Stabilize")

def rtl_handler():
    MODEVAR.set("Current mode: RTL")
    send_text_to_window("Changed mode to: RTL")


def flip_handler():
    MODEVAR.set("Current mode: Flip")
    send_text_to_window("Changed mode to: Flip")


#-- Other functions
def send_text_to_window(msg):
    time = str(datetime.datetime.now().time())
    time = time[0:5]
    if len(msg) > 37:
        T.insert(END,"[" + time + "] " +  msg + "\n\n")
    else:
        T.insert(END,"[" + time + "] " + msg + "\n")
    if endFlag.get() == 1:
        T.see("end")

#-- mainloop, if we need to react to something we can do it here, ex read some input.
def my_mainloop():
    send_text_to_window("Woho")
    root.after(5000,my_mainloop)

#-- first arg = [("Button name",func name)], second arg = tkinter frame to add buttons to
def addButtonsToFrame(btn_tuple_list,frame):
    i = 0
    for name_handler_tuple in btn_tuple_list:
        Button(frame,text=name_handler_tuple[0], command = name_handler_tuple[1]).grid(row = i+1, column = 0, sticky=E + W ,pady = 2)
        i+=1

#Only executes if run as main process. Will NOT run if the file is imported, which it would otherwise. (hence buggs with duplicating GUIs)
if __name__ == '__main__':

    startup()


    #-- Root window
    root = Tk()
    root.protocol("WM_DELETE_WINDOW", ask_quit)

    #-- Height and width of the window is decided by current resolution
    WIDTH = int(ctypes.windll.user32.GetSystemMetrics(0) * 0.8)
    HEIGHT =  int(ctypes.windll.user32.GetSystemMetrics(1) * 0.6)

    #-- Global variables
    REBOOTVAR = StringVar()
    REBOOTNR = 0
    REBOOTVAR.set("Number of reboots: " + str(REBOOTNR))

    MODEVAR = StringVar()
    MODESTR = "RTL"
    MODEVAR.set("Current mode: " + MODESTR)

    endFlag = IntVar()
    gst = 0
    playerFlag = False




    #-- If row or col is not specified it's 0.
    INFOCOL = 0

    TEXTCOL = 1

    BTNCOL = 2

    MODECOL = 3

    IMAGECOL = 4

    #-- Settings for root window
    root.geometry(str(WIDTH) + "x" + str(HEIGHT))
    root.title("Drone GUI")
    root.resizable(False, False)



    #-- List of tuples, first = name of the button, second = name of handler
    btnnames = [("ArduPlane",arducopter_handler), ("Low Video", lowvid_handler), ("Med Video", medvid_handler), ("High video", highvid_handler),("Stop Video",stopvid_handler),("Open Player",openplayer_handler),("Close Player",closeplayer_handler),("Photo",photo_handler),("Reboot",reboot_handler)]

    btnframe = Frame(root)

    Label(btnframe,text="Kontroll", font ="Helvetica 12 bold").grid(row=0)

    addButtonsToFrame(btnnames,btnframe)

    #-- Container for info
    infoframe = Frame(root, height = 400, width = 150, bg = "black")
    infoframe.pack_propagate(False)

    rebootlabel = Label(infoframe, textvariable=REBOOTVAR ,fg='#4ee44e', bg="black")
    rebootlabel.pack()

    modelabel = Label(infoframe, textvariable=MODEVAR,fg='#4ee44e', bg="black")
    modelabel.pack()

    #-- Container for modes
    modeframe = Frame(root)
    Label(modeframe, text="Modes", font="Helvetica 12 bold").grid(row = 0, sticky = N, padx = 2)

    modebtnnames = [("Stabilize",stabilize_handler),("RTL",rtl_handler),("Flip",flip_handler)]
    modeframe.pack_propagate(False)
    addButtonsToFrame(modebtnnames, modeframe)

    #-- Text window
    textframe = Frame(root, height = 400, width = 300)
    textframe.pack_propagate(False)
    T = Text(textframe)
    scrollbar = Scrollbar(textframe)
    scrollbar.config(command = T.yview)
    scrollbar.pack(side =RIGHT, fill=Y)
    checkbtn = Checkbutton(textframe, text="Autoscroll", variable=endFlag)
    checkbtn.pack(side = TOP)
    T.pack()


    #-- Container for picture
    canvas = Canvas(root, width = 500, height = 500)
    canvas.pack_propagate(False)
    img = ImageTk.PhotoImage(Image.open("testBild.jpg"))
    canvas.create_image(20, 20, anchor=NW, image=img)

    #-- Adding the frames to root
    canvas.grid(row = 0, column = IMAGECOL, columnspan = 4, padx = 10, pady = 10)
    textframe.grid(row = 0, column = TEXTCOL, rowspan = 1, padx = 10, pady = 10, sticky=NSEW)
    infoframe.grid(row = 0, column = INFOCOL, padx = 10, pady = 10, sticky=N+W)
    btnframe.grid(row = 0, column = BTNCOL, sticky = N)
    modeframe.grid(row = 0, column = MODECOL, rowspan = 4, sticky = N, padx = 10)

    root.after(5000,my_mainloop)
    root.mainloop()
