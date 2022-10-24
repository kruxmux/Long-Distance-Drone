#define ch6 13
#define ch5 12
#define ch4 11
#define ch3 10
#define ch2 9
#define ch1 8


short ch[6];
unsigned long time;

void setup() {
  // put your setup code here, to run once:
  pinMode(ch1, INPUT);
  pinMode(ch2, INPUT);
  pinMode(ch3, INPUT);
  pinMode(ch4, INPUT);
  pinMode(ch5, INPUT);
  pinMode(ch6, INPUT);
  
  Serial.begin(115200);
}

void loop() {

  if(digitalRead(ch1)) {
    time = micros();
    while(digitalRead(ch1));
    ch[0] = micros() - time;
  }
  
  if(digitalRead(ch2)) {
    time = micros();
    while(digitalRead(ch2));
    ch[1] = micros() - time;
  }

    if(digitalRead(ch3)) {
    time = micros();
    while(digitalRead(ch3));
    ch[2] = micros() - time;
  }

    if(digitalRead(ch4)) {
    time = micros();
    while(digitalRead(ch4));
    ch[3] = micros() - time;
  }


    if(digitalRead(ch5)) {
    time = micros();
    while(digitalRead(ch5));
    ch[4] = micros() - time;
  }

    if(digitalRead(ch6)) {
    time = micros();
    while(digitalRead(ch6));
    ch[5] = micros() - time;
  }
  
 
  for(int i = 0; i<6; i++) {
    Serial.print(String(ch[i] + "\t"));
    }
  Serial.print("\n");
  
  
}

