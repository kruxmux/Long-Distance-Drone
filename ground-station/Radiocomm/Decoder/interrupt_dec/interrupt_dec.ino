#include "TimerOne.h"

#define ch6 13
#define ch5 12
#define ch4 11
#define ch3 10
#define ch2 9
#define ch1 8


volatile short ch[6] = {0, 0, 0, 0, 0, 0};  // Array of servo channel values
volatile short pinIndex = 0;               // Keeps track of what pin we're currently reading
volatile short rc_flag = true;              // if true, there are issues with RC communication
volatile unsigned long tlast;               // time since last IRQ
volatile bool printFlag = false;            // when to send message (will be at 50Hz due to how receiver works)
volatile bool sent_error = false;

volatile bool error = false;                // debug


/* The 0 at the end of PCMSK0, PCINT0 etc indicate port B. 
 * Pins range: PCINT0-PCINT7, although PCINT6 and 7 are not usable physically. 
 * Port C (analog) is PCINT1 and port D is PCINT2
 */
void setup() {
  for(int i=ch1; i<=ch6; i++) { pinMode(i, INPUT); }
/* What pins to listen to for D8 - D13 */
  PCMSK0 |= 0b00111111;
  /* Clear interrupts on port B */
  PCIFR |= bit(PCIF0);
  /* Enable interrupts */
  PCICR |= bit(PCIE0);
  
  // No need for more than 2200 micros
  Timer1.initialize(2200);
  
  Serial.begin(115200);
}

void loop() {
  unsigned long temp = millis();
  if(temp > tlast) {  
    int delta = temp - tlast;
    if(delta > 200 && rc_flag == false) { 
      rc_flag = true; 
      sent_error = false;  
    }
  }   
    if(printFlag) {
      String payload = String(String(ch[0]) + "\t" + 
                              String(ch[1]) + "\t" + 
                              String(ch[2]) + "\t" + 
                              String(ch[3]) + "\t" + 
                              String(ch[4]) + "\t" + 
                              String(ch[5]));
      Serial.println(payload);
      printFlag = false;
    }
    
  if(rc_flag && sent_error == false) {
    Serial.println("Error: lost connection to transmitter"); 
    sent_error = true;
  }
}


/*  Pin change subroutine for port B (pins 8-13)
 *  Pulses arrive back to back so not really considering the rising/falling case
 *  Just treating the last edge differently (if no pin is high on port B)
 */
ISR (PCINT0_vect) {
  unsigned int pins = PINB;
  switch(pins) {
      case 0b0:
        pinIndex = 5;
        break;
      case 0b1:  
        Timer1.start();
        pinIndex = -1;
        return;
        break;
      case 0b10:
        pinIndex = 0;
        break;
      case 0b100:
        pinIndex = 1;
        break;
      case 0b1000:
        pinIndex = 2;
        break;
      case 0b10000:
        pinIndex = 3;
        break;
      case 0b100000:
        pinIndex = 4;
        break;
      default:
        error = true; // at this point some weird overlap has occured, variable is for debugging
        break;
  }
  
  
  
  unsigned short val = Timer1.read();
  if(pinIndex != 5) {
    Timer1.start(); // restart
  }
  else {
    Timer1.stop();
    printFlag = true;
  }
  if(val > 850 && val < 2020) {
      ch[pinIndex] = val + 100;
  }
 rc_flag = false;
 tlast = millis();
}
