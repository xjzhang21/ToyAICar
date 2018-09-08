#include <Servo.h>
#include "MsTimer2.h"

#define PWM_STEER   10
#define PWM_MOTOR   11

#define ENC_A   2
#define ENC_B   3

Servo steer_servo, motor_servo;

float steering = 0, velocity = 0;
int encoder_count = 0;

String message = "";

void encoder()
{
    if (digitalRead(ENC_A) == digitalRead(ENC_B)) 
        encoder_count++;
    else
        encoder_count--;
}

float PID_P = 0.2, PID_I = 0.01, PID_D = 0;

void pid()
{
    static float last_error = 0, int_error = 0;
    
    float current_velocity = encoder_count * 3.1415926 * 3 / 190 / 0.01;
    Serial.println(current_velocity);

    float error = velocity - current_velocity;
    int u = PID_P * error + PID_I * int_error + PID_D * (error - last_error);
    last_error = error;
    int_error += error;
    
    if (int_error > 2000)
        int_error = 2000;
    if (int_error < -2000)
        int_error = -2000;
    
    if (u > 300) u = 300;
    if (u < -300) u = -300;
    if (u > 0)
        motor_servo.writeMicroseconds(1620 + u);
    else if (u < 0)
        motor_servo.writeMicroseconds(1310 + u);
    else
        motor_servo.writeMicroseconds(1465);

    encoder_count = 0;
}

void setup()
{
    // put your setup code here, to run once:
    Serial.begin(9600);

    // Servos
    steer_servo.attach(PWM_STEER);
    steer_servo.write(90);
    
    motor_servo.attach(PWM_MOTOR);
    motor_servo.writeMicroseconds(1465);

    delay(5000);

    // Encoder
    pinMode(ENC_A, INPUT_PULLUP);
    pinMode(ENC_B, INPUT_PULLUP);
    attachInterrupt(0, encoder, CHANGE);   // PIN 2
    
    // PID interrupt
    MsTimer2::set(10, pid);
    MsTimer2::start();
}

void loop()
{
    // put your main code here, to run repeatedly:
    if(Serial.available())
    { 
        char inchar = Serial.read();
        if (inchar != '\n')
            message += inchar;
        else
        {
            if (message[0]=='S')
            {
                steering = message.substring(2).toFloat();
                if (steering > 30) steering = 30;
                if (steering < -30) steering = -30;
                steer_servo.write(90 + steering);
            }
            else if (message[0]=='V')
                    velocity = message.substring(2).toFloat();
            else if (message[0]=='P')
                    PID_P = message.substring(2).toFloat();
            else if (message[0]=='I')
                    PID_I = message.substring(2).toFloat();
            else if (message[0]=='D')
                    PID_D = message.substring(2).toFloat();
                    
            message = "";
        }
    }
}
