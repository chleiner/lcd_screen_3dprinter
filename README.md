# lcd_screen_3dprinter
contains python scripts for the lcd 16x2 screen qapass 1602a controled by raspberry pi

The scripts work with joes octoapi.py and use them to get the right data of the dictionnairies of the 3d printer.
GPIO is configurated with setmode(GPIO.BCM).
The lcd is controlled by the raspberry and uses GPIOports 7, 8, 18, 23, 24, 25.
Pin 7 decides weather there is a data or an instruction input.
Pin 8 writes, enables the data inputs.
Pins 18, 23, 24, and 25 are the data pins and are used for instruction or data input (depends on pin 7).
