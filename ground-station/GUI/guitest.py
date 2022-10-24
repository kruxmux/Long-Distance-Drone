from Tkinter import *

master = Tk()



def callback1():
    text.insert(INSERT, "button1!\n")

def callback2():
    text.insert(INSERT, "button2!\n")

def callback3():
    text.insert(INSERT, "button3!\n")

def callback4():
    text.insert(INSERT, "button4!\n")

def callback5():
    text.delete('2.0', END) #rensar all text på och efter 2a raden
    text.insert(INSERT, "\n ") #Lägger till ny rad



button1 = Button(master, text="button1", command=callback1)
button1.pack()

button2 = Button(master, text="button2", command=callback2)
button2.pack()

button3 = Button(master, text="button3", command=callback3)
button3.pack()

button4 = Button(master, text="button4", command=callback4)
button4.pack()

button5 = Button(master, text="Rensa", command=callback5)
button5.pack()

text = Text(master, background="black", foreground="green")
text.insert(INSERT, "Senast tryckta knapp:\n")
text.pack()



mainloop()
