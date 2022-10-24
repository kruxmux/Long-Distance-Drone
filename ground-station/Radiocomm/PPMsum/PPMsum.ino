#include "TimerOne.h"

#define ch6 13
#define ch5 12
#define ch4 11
#define ch3 10
#define ch2 9
#define ch1 8
#define sig 3

volatile short ch[7] = {1500, 1500, 800, 1500, 1500, 1500, 1000};  // Array of servo channel values (last value is not being used, just marks end of pulse train)

volatile int state = LOW;
volatile int channel = 0;
volatile int elapsed;

/* The 0 at the end of PCMSK0, PCINT0 etc indicate port B.
 * Pins range: PCINT0-PCINT7, although PCINT6 and 7 are not usable physically.
 * Port C (analog) is PCINT1 and port D is PCINT2
 */
void setup() {
  for(int i=ch1; i<=ch6; i++) { pinMode(i, INPUT); }

  pinMode(sig, OUTPUT);

  Timer1.initialize(2200);          // just a random number, gets changed quickly
  Timer1.attachInterrupt(timer_ISR);

  Serial.begin(115200);
}

void loop() {

  ch[0] = pulseInLong(ch1, HIGH);
  ch[1] = pulseInLong(ch2, HIGH);
  ch[2] = pulseInLong(ch3, HIGH);
  ch[3] = pulseInLong(ch4, HIGH);
  ch[4] = pulseInLong(ch5, HIGH);
  ch[5] = pulseInLong(ch6, HIGH);

  // Prints all the channel values
  // Serial.println(String(String(ch[0]) + "\t" + String(ch[1]) + "\t" + String(ch[2]) + "\t" + String(ch[3]) + "\t" + String(ch[4]) + "\t" + String(ch[5])));


}


ISR (PCINT0_vect) {
  // old code
}

void timer_ISR() {
  if(channel > 6) {
    channel = 0;
    int tmp = 21000 - elapsed;
    Timer1.initialize(tmp); // 21000 is frame size, subtracting sum of pulse times for correct sync
    elapsed = 0;
    return;

  }
  if(state == LOW) {
    digitalWrite(sig, HIGH);
    state = HIGH;
    Timer1.initialize(350);
  }
  else {
    digitalWrite(sig, LOW);
    state = LOW;
    short val = ch[channel++];
    Timer1.initialize(val - 350);
    elapsed += val;

  }
}
