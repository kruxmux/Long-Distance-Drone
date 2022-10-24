#define ch6 13
#define ch5 12
#define ch4 11
#define ch3 10
#define ch2 9
#define ch1 8


long int ch[6];

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

  ch[0] = pulseInLong(ch1, HIGH);
  ch[1] = pulseInLong(ch2, HIGH);
  ch[2] = pulseInLong(ch3, HIGH);
  ch[3] = pulseInLong(ch4, HIGH);
  ch[4] = pulseInLong(ch5, HIGH);
  ch[5] = pulseInLong(ch6, HIGH);
 
  for(int i = 0; i<6; i++) {
    Serial.print(ch[i]);
    Serial.print("\t");
  }
  Serial.print("\n");
  
  
}
