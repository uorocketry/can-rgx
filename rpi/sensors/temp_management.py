#import RPi.GPIO as GPIO
import concurrent.futures
import time
import tkinter

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

import numpy as np
from scipy.interpolate import BSpline, make_interp_spline
from temperature_sensor_mgmt import ThermoList

class GetCurrentTemp():
    def setup(self):
        #max workers defaults to the number of processors on the machine, multiplied by 5
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=None)
        
        #with ThreadPoolExecutor(max_workers=None) as executor:
        #ID's of sensors to poll
        BOTTOM_RIGHT = '00000bc743d3' or '1'
        TOP_LEFT = '00000bc743d3' or '2'
        CENTER = '00000bc743d3' or '4'

        sensor_id = [BOTTOM_RIGHT, TOP_LEFT, CENTER]  
        total_sensors = 3

        return_data = []

        #calls target func and sends iterable sensor id, returning values respectively
        for result in executor.map(temperature_sensor_mgmt.Thermolist.pass_value, sensor_id):
        #for result in executor.map(self.dummy_func, sensor_id):
            print('temp: {0}'.format(result))
            return_data.append(result)

        sum_list = sum(return_data)
                    
        avg_temp = sum_list/total_sensors
        print(f'Average temp: {avg_temp}')
        return avg_temp

    def dummy_func(self, id):
        #this is to emulate the thermometer code
        return(id*2)


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
        self.SetPoint = 0.0   
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
        """
        error = self.SetPoint - feedback_value    #i.e. desired - actual

        self.current_time = current_time if current_time is not None else time.time()
        delta_time = self.current_time - self.last_time
        delta_error = error - self.last_error

        if (delta_time >= self.sample_time):
            self.PTerm = self.Kp * error
            self.ITerm += error * delta_time

            if (self.ITerm < -self.windup_guard):
                self.ITerm = -self.windup_guard
            elif (self.ITerm > self.windup_guard):
                self.ITerm = self.windup_guard
            
            self.DTerm = 0.0
            if delta_time > 0:
                self.DTerm = delta_error / delta_time

            #save last time and last error for next calculation
            self.last_time = self.current_time
            self.last_error = error

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
    PIN = 16

    def setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PIN, GPIO.OUT)

    def motor_on(pin):
        GPIO.output(pin, GPIO.HIGH)  # Turn relay on

    def motor_off(pin):
        GPIO.output(pin, GPIO.LOW)  # Turn relay off
    

    def call_pid(P, I, D, L):
        pid = PID(P, I, D)

        pid.SetPoint = 35    #desired temp. val
        pid.setSampleTime(0.05)

        END = L
        feedback = GetCurrentTemp.setup

        feedback_list = []
        time_list = []
        setpoint_list = []

        for i in range(1, END):
            pid.update(feedback)
            output = pid.output
            if pid.SetPoint > 0:
                feedback += (output - (1/i))
            if i>9 :
                pid.SetPoint = 1
            time.sleep(0.02)

            feedback_list.append(feedback)
            setpoint_list.append(pid.SetPoint)
            time_list.append(i)

        time_sm = np.array(time_list)
        time_smooth = np.linspace(time_sm.min(), time_sm.max(), 300)

        helper_x3 = make_interp_spline(time_list, feedback_list)
        feedback_smooth = helper_x3(time_smooth)

        plt.plot(time_smooth, feedback_smooth)
        plt.plot(time_list, setpoint_list)
        plt.xlim((0, L))
        plt.ylim((min(feedback_list)-0.5, max(feedback_list)+0.5))
        plt.xlabel('time(s)')
        plt.ylabel('PID (PV)')
        plt.title('PID Test')

        plt.ylim((1-0.5, 1+0.5))

        plt.grid(True)
        plt.show()

if __name__ == "__main__":
    start = time.perf_counter()
    GetCurrentTemp().setup()
    finish = time.perf_counter()
    print(f'Finished in {round(finish-start, 2)} second(s)')

    time.sleep(1)

    t = TempManagement.call_pid(1.2, 1, 0.001, L=10)


