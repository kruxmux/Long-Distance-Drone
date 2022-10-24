from Tkinter import *
from PIL import ImageTk,Image
from time import sleep
import datetime, ctypes, os, signal, threading, subprocess, tkMessageBox
import socket, pickle, sys
import gui_as_class

def ask_decode():
    print("Use RC-decoder? Y/N")
    ans = input()
    if ans == Y:
        return True
    elif ans == N:
        return False
    else:
        return ask_decode

def ask_port():
    print("Enter communication port (COMX or /dev/tty/USBx): ")
    port = raw_input()
    return port


if __name__ == "__main__":

    #GUI = gui_as_class.GUIWINDOW(False)
    rc_dec = ask_decode()
    port = ""
    if rc_dec:
        port = ask_port()
    GUI = gui_as_class.GUIWINDOW(rc_dec, port)

    pass
