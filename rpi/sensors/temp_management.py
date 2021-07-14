import configparser
import logging
import threading
import time

import RPi.GPIO as GPIO
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# desired temp
from shared.customlogging.errormanager import ErrorManager

SetPoint = 37

# relay pin on pi
RELAY_PIN = 21

# ID's of sensors to poll - change when lay out finalized.
sensor_id_list = ['2', '3']


class PID:
    def __init__(self, P, I, D, SetPoint, current_time=None):
        # pid initialization
        self.Kp = P
        self.Ki = I
        self.Kd = D
        self.SetPoint = SetPoint
        self.sample_time = 0.00
        self.current_time = current_time if current_time is not None else time.time()
        self.last_time = self.current_time
        self.clear()

    def clear(self):
        """ 
        Clear PID computations and coefficients
        """
        self.ITerm = 0.0
        self.DTerm = 0.0
        self.last_error = 0.0

        # windup guard
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
        self.error = self.SetPoint - feedback_value  # desired - actual
        self.current_time = current_time if current_time is not None else time.time()
        delta_time = self.current_time - self.last_time
        delta_error = self.error - self.last_error

        if delta_time >= self.sample_time:
            self.PTerm = self.Kp * self.error
            self.ITerm += self.error * delta_time

            if self.ITerm < -self.windup_guard:
                self.ITerm = -self.windup_guard
            elif self.ITerm > self.windup_guard:
                self.ITerm = self.windup_guard

            self.DTerm = 0.0
            if delta_time > 0:
                self.DTerm = delta_error / delta_time

            # save last time and last error for next calculation
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


class TempManagement(threading.Thread):
    def __init__(self):
        super().__init__()
        self.em = ErrorManager(__name__)

        self.feedback_list = []
        self.time_list = []
        self.setpoint_list = []

        # read config file and loop through sections
        config = configparser.ConfigParser()
        config.read('pid.ini')
        P = int(config['values']['P'])
        I = int(config['values']['I'])
        D = int(config['values']['D'])

        self.pid = PID(P, I, D, SetPoint)
        self.pid.setSampleTime(0.05)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RELAY_PIN, GPIO.OUT)

        # Logger used to eventually send the current state to the laptop
        self.stateLogger = logging.getLogger('sensorlog.temp_management')

        self.lastStateSend = time.time()

        # uncomment following three lines and delete fourth when relay is attached to pi
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(RELAY_PIN, GPIO.OUT)
        # self.call_pid(p, i, d, L=10)
        # feedback = self.get_current_avg_temp()

    def get_current_avg_temp(self):
        from rpi.sensors.thermometer import ThermometerList

        # Get the list of temperatures from the thermometer thread
        current_temps = ThermometerList.get_temperature_data_list(sensor_id_list)

        sum = 0
        count = 0
        for key, value in current_temps.items():
            # handle 'none' passed in for cases where sensor is disconnected
            try:
                sum += value
                count += 1

                self.em.resolve(f"Temperature sensor {key} now providing acceptable data", key, False)
            except TypeError:
                self.em.error(f"Not all sensors are providing acceptable temperature data. "
                      f"Cannot perform designated operation on sensor: ({key} | value: '{value}') - Discarded", key)
                pass

        avg_temp = sum / count if count != 0 else 0

        return avg_temp

    def heater_on(self):
        if time.time() - self.lastStateSend > 1:
            self.stateLogger.info("Heater on", extra={'heaterOn': True})
            self.lastStateSend = time.time()

        GPIO.output(RELAY_PIN, GPIO.HIGH)  # Turn relay on

    def heater_off(self):
        if time.time() - self.lastStateSend > 1:
            self.stateLogger.info("Heater off", extra={'heaterOn': False})
            self.lastStateSend = time.time()

        GPIO.output(RELAY_PIN, GPIO.LOW)  # Turn relay off

    def pid_loop(self):
        time.sleep(1)

        # get feedback aka avg (current) temperature
        feedback = self.get_current_avg_temp()
        self.pid.update(feedback)

        if self.pid.error > 0:
            self.heater_on()
        elif -0.1 <= self.pid.error <= 0.1:
            self.heater_off()
        else:
            self.heater_off()

        if feedback > (SetPoint + 2):
            self.em.error(f"Temperature at {feedback}. Please cool down system.", "HIGH_TEMP")
        else:
            self.em.resolve(f"Temperature now at {feedback}", "HIGH_TEMP", False)


        return feedback

    def run(self):
        while True:
            #comment out next line after for plot testing
            self.pid_loop()

    def plot(self, i):
        feedback = self.pid_loop()

        self.feedback_list.append(feedback)
        self.setpoint_list.append(self.pid.SetPoint)
        self.time_list.append(time.time())  # time in seconds since UNIX time Jan 1, 1970 (UTC)

        plt.cla()
        plt.plot(self.time_list, self.feedback_list)
        plt.plot(self.time_list, self.setpoint_list)

        plt.xlabel('time(s)')
        plt.ylabel('PID (PV)')
        plt.title('PID Test')

        plt.grid(True)

    def start_plotting(self):
        self.ani = FuncAnimation(plt.gcf(), self.plot, interval=1000)
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
