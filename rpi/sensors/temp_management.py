import RPi.GPIO as GPIO
import time

import RPi.GPIO as GPIO
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import ConfigParser
from rpi.sensors.thermometer import ThermometerList


# import numpy as np


class GetCurrentTemp():
    def __init__(self):
        # ID's of sensors to poll - change when lay out finalized.
        sensor_id_list = ['1', '2', '3', '4']

        # call thermometer thread to retrieve current temperature
        current_temp_val = ThermometerList.get_temperature_data(sensor_id_list)
        print(f'Current temperature retrieved from thermometer thread: {current_temp_val}')

        GetCurrentTemp.current_avg_temp(self, current_temp_val)

    def current_avg_temp(self, current_temps):
        sum = 0
        count = 0
        for key, value in current_temps.items():
            # handle 'none' passed in for cases where sensor is disconnected
            try:
                print(value)
                sum += value
                count += 1
            except TypeError:
                print(f"Not all sensors are providing acceptable temperature data. "
                      f"Cannot perform designated operation on sensor: ({key} | value: '{value}') - Discarded")
                pass

        avg_temp = sum / count

        print(f'Current average temperature : {avg_temp}')
        return avg_temp


class PID():
    def __init__(self, P, I, D, current_time=None):
        #pid initialization
        self.Kp = P
        self.Ki = I
        self.Kd = D
        self.sample_time = 0.00
        self.current_time = current_time if current_time is not None else time.time()
        self.last_time = self.current_time
        self.clear()

    def clear(self):
        """ 
        Clear PID computations and coefficients
        """
        self.SetPoint = 35 #desired temp
        self.ITerm = 0.0
        self.DTerm = 0.0
        self.last_error = 0.0

        #windup guard
        self.int_error = 0.0
        self.windup_guard = 20.0
        self.output = 0.0
    
    def update(self, feedback_value, current_time=None):
        """
        Calculate PID value for given reference feedback
        PSEUDO CODE

        while(1) {
        error = desired_value – actual_value
        integral = integral_prior + error * iteration_time
        derivative = (error – error_prior) / iteration_time
        output = KP*error + KI*integral + KD*derivative + bias
        error_prior = error
        integral_prior = integral
        sleep(iteration_time)
        }
        """
        self.error = self.SetPoint - feedback_value    # desired - actual
        self.current_time = current_time if current_time is not None else time.time()
        delta_time = self.current_time - self.last_time
        delta_error = self.error - self.last_error

        if (delta_time >= self.sample_time):
            self.PTerm = self.Kp * self.error
            self.ITerm += self.error * delta_time

            if (self.ITerm < -self.windup_guard):
                self.ITerm = -self.windup_guard
            elif (self.ITerm > self.windup_guard):
                self.ITerm = self.windup_guard
            
            self.DTerm = 0.0
            if delta_time > 0:
                self.DTerm = delta_error / delta_time

            #save last time and last error for next calculation
            self.last_time = self.current_time
            self.last_error = self.error

            self.output = self.PTerm + (self.Ki * self.ITerm) + (self.Kd * self.DTerm)
        
    
    def setKp(self, proportional_gain):
        """
        Determine how aggressively the PID reacts to the current error in relation to proportional gain
        """
        self.Kp = proportional_gain

    def setKi(self, integral_gain):
        """
        Determine how aggressively the PID reacts to the current error in relation to integral gain
        """
        self.Ki = integral_gain

    def setKd(self, derivative_gain):
        """
        Determine how aggressively the PID reacts to the current error in relation to derivative gain
        """
        self.Kd = derivative_gain

    def setWindup(self, windup):
        """
        Integral windup, also known as integrator windup[1] or reset windup,[2] refers to the situation in a 
        PID feedback controller where a large change in setpoint occurs (say a positive change) and the integral 
        term accumulates a significant error during the rise (windup), thus overshooting and continuing to increase 
        as this accumulated error is unwound (offset by errors in the other direction). The specific problem is 
        the excess overshooting.
        """
        self.windup_guard = windup

    def setSampleTime(self, sample_time):
        """
        PID should be updated at regular intervals.
        Based on a pre-determined sample time, the PID decides if it should compute or return immediately.
        """
        self.sample_time = sample_time


class TempManagement():
    #relay pin on pi
    PIN = 21

    def setup(self):
        self.feedback_list = []
        self.time_list = []
        self.setpoint_list = []

        #read config file and loop through sections
        config = ConfigParser.ConfigParser()
        config.read('pid.cfg')
        for section in config.sections():
            p = config.get(section, 'P')
            i = config.get(section, 'I')
            d = config.get(section, 'D')

            #uncomment following three lines and delete fourth when relay is attached to pi
            #GPIO.setmode(GPIO.BCM)
            #GPIO.setup(self.PIN, GPIO.OUT)
            #self.call_pid(p, i, d, L=10)
            feedback = GetCurrentTemp.__init__(self)

    def motor_on(self, pin):
        GPIO.output(pin, GPIO.HIGH)  # Turn relay on

    def motor_off(self, pin):
        GPIO.output(pin, GPIO.LOW)  # Turn relay off
    

    def call_pid(self, P, I, D):
        self.pid = PID(P, I, D)
        self.pid.SetPoint = 35    #desired temp. val
        self.pid.setSampleTime(0.05)

    def pid_loop(self, i):
        #get feedback aka avg (current) temperature
        self.feedback = GetCurrentTemp.__init__(self)
        output = self.pid.update(self.feedback)

        if self.pid.error > 0:
            self.motor_on(self.PIN)
            
        elif -0.1 <= self.pid.error <= 0.1:
            self.motor_off(self.PIN)

        else:
            print("Unprecedented temperature. Hotter than 35 C. No means of mitigation.")

        time.sleep(0.02)

        self.feedback_list.append(self.feedback)
        self.setpoint_list.append(self.pid.SetPoint)
        self.time_list.append(time.time())  #time in seconds since UNIX time Jan 1, 1970 (UTC)

        plt.cla()
        plt.plot(self.time_list, self.feedback_list)
        plt.plot(self.time_list, self.setpoint_list)

        plt.xlabel('time(s)')
        plt.ylabel('PID (PV)')
        plt.title('PID Test')

        plt.grid(True)

    def start_plotting(self):
        self.ani = FuncAnimation(plt.gcf(), self.pid_loop, interval=1000)
        plt.show()

"""
if __name__ == "__main__":
    start = time.perf_counter()
    GetCurrentTemp().setup()
    finish = time.perf_counter()
    print(f'Finished in {round(finish-start, 2)} second(s)')

    time.sleep(0.01)

    t = TempManagement.call_pid(1.2, 1, 0.001, L=10)

"""
