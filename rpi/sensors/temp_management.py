import logging
import RPi.GPIO as GPIO
import threading
import time
import tkinter
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import BSpline, make_interp_spline
from rpi.sensors.thermometer import ThermometerList

class GetCurrentTemp():
    def setup(self):
        #ID's of sensors to poll - change when lay out finalized.
        BOTTOM_RIGHT = '00000bc743d3' or '1'
        TOP_LEFT = '00000bcada' or '2'

        total_sensors = 2
        sensor_id_list = [BOTTOM_RIGHT, TOP_LEFT]

        #call thread in thermometer.py to retrieve data
        current_temp_list = threading.Thread(target=ThermometerList.get_temperature_data_list(sensor_id_list))

        self.current_avg_temp(current_temp_list, total_sensors)

    def current_avg_temp(self, current_temps, total_sensors):
        sum = 0
        for key,value in current_temps.items():
            #print(value)
            sum += value

        avg_temp = sum/total_sensors

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
    PIN = 16

    def setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PIN, GPIO.OUT)

        self.call_pid(1.2, 1, 0.001, L=10)


    def motor_on(self, pin):
        GPIO.output(pin, GPIO.HIGH)  # Turn relay on

    def motor_off(self, pin):
        GPIO.output(pin, GPIO.LOW)  # Turn relay off
    

    def call_pid(self, P, I, D):
        pid = PID(P, I, D)

        pid.SetPoint = 35    #desired temp. val
        pid.setSampleTime(0.05)

        feedback_list = []
        time_list = []
        setpoint_list = []

        while True:
            #get feedback aka avg (current) temperature
            feedback = GetCurrentTemp.setup()
            pid.update(feedback)
            output = pid.output
            
            if pid.error > 0:
                self.motor_on(self.PIN)
            
            elif -0.1 <= pid.error <= 0.1:
                self.motor_off(self.PIN)

            else:
                 print("Unprecedented temperature. Hotter than 35 C. No means of mitigation.") 

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


"""
if __name__ == "__main__":
    start = time.perf_counter()
    GetCurrentTemp().setup()
    finish = time.perf_counter()
    print(f'Finished in {round(finish-start, 2)} second(s)')

    time.sleep(0.01)

    t = TempManagement.call_pid(1.2, 1, 0.001, L=10)

"""
