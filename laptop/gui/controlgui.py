from laptop.gui.controlframe import MotorFrame, LEDFrame
from laptop.gui.statusframe import StatusFrame


class ControlGUI:
    def __init__(self, master):
        master.title("Control")
        master.geometry("1000x200")

        self.status = StatusFrame(master)
        self.status.grid(row=0, sticky="nsew")

        self.motor = MotorFrame(master)
        self.motor.grid(row=1, sticky="nsew", pady=20)

        self.led = LEDFrame(master)
        self.led.grid(row=2, sticky="nsew")

        master.grid_columnconfigure(0, weight=1)

        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)
        master.grid_rowconfigure(2, weight=1)

        master.bind("<Key>", func=self.key_press)

    def key_press(self, char):
        self.motor.key_press(char)
        self.led.key_press(char)
