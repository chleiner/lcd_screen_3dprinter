#!/usr/bin/python
#--------------------------------------
#Autor: Christoph Leiner, Date:17.05.17
# The wiring for the LCD is as follows:
# 1 : GND					 - GROUND from GPIO
# 2 : 5V					 - 5V from GPIO
# 3 : Contrast (0-5V)*		 - GROUND from GPIO
# 4 : RS (Register Select)	 - GPIO 7
# 5 : R/W (Read Write)       - GROUND from GPIO
# 6 : Enable				 - GPIO 8
# 7 : Data Bit 0             - NOT USED
# 8 : Data Bit 1             - NOT USED
# 9 : Data Bit 2             - NOT USED
# 10: Data Bit 3             - NOT USED
# 11: Data Bit 4			 - GPIO 25
# 12: Data Bit 5			 - GPIO 24
# 13: Data Bit 6			 - GPIO 23
# 14: Data Bit 7			 - GPIO 18
# 15: LCD Backlight +5V**	 - 5V from USB hub
# 16: LCD Backlight GND		 - GROUND from USB hub
#
#This programm gives data from octoprint to lcd screen qapass 1602a.
#
#The write mode is disabled (R/W is on GROUND).
#
#The LCD gets the 5V and ground from an extern USB hub.
#
#You can run the programm in the background by adding "&" 
#at the end of the python xy command on the terminal.
 
#--------------------------------------
#import
import RPi.GPIO as GPIO
import time
import sys
from clear_lcd import *
from octoapi import *
from threading import Thread
from singleton import*

#--------------------------------------
#global variables
# Define GPIO to LCD mapping
LCD_RS = 7
LCD_E  = 8
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 18
# Define some device constants
LCD_WIDTH = 16    # Maximum characters per line
LCD_CHR = True
LCD_CMD = False
LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

#--------------------------------------
#definitions
def main():
	#declar Thread
	t1 = Thread(target = clockthread)

	#make sure that only one single instance of the programm is running
	me = SingleInstance()
  
	#gpio settings (config pins/ setup pins (in/out))
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)      #standard config
	GPIO.setup(LCD_E, GPIO.OUT)  
	GPIO.setup(LCD_RS, GPIO.OUT) 
	GPIO.setup(LCD_D4, GPIO.OUT) 
	GPIO.setup(LCD_D5, GPIO.OUT) 
	GPIO.setup(LCD_D6, GPIO.OUT) 
	GPIO.setup(LCD_D7, GPIO.OUT) 
  
	#clear ddram lcd from lib clear_lcd
	reset_ddram_content()

	#Initialise display
	lcd_init()

	#change var init is changed by Thread t1
	global lcd_switch
  
	#start Thread
	t1.start()
	print("clockthread started")

	#infinity loop
	while True:
		#check weather 3dprinter is printing, operational or pause
		if get_printing_value() and actual_is_target_temp(): #printing and temperature is right
			#get status
			printstate = get_completion()
			if printstate ==  None: # proof if printstate is None
				printstate = 0
			elif printstate > 100:
				printf("Error - printstate value >100")
				sys.exit()	

			#calculate Times
			timeinseconds =get_printTimeLeft()
			if timeinseconds == None: #case get_prinTimeLeft() returns None value
				hours = 0
				minutes = 0
			elif timeinseconds>=0: #case get_printTimeLeft() returns int value >=0
				hours = int(timeinseconds/3600)
				resttimehours = (timeinseconds/float(3600)) - hours 
				minutes = int((resttimehours * 60))
			else: #case get_printTimeLeft() returns value <0
				print("Error - get_printTimeLeft() returns value <0")
			outputstring = str(hours) + "h " + str(minutes) + "m " 

			#send Display output
			if (lcd_switch): #output printstate
				lcd_string("Druckerstatus:",LCD_LINE_1)
				lcd_string("%i Prozent" %printstate,LCD_LINE_2) 
			elif (not(lcd_switch)): #output remaining time
				lcd_string("Restzeit:", LCD_LINE_1)
				lcd_string(outputstring , LCD_LINE_2)
	
		elif get_printing_value() and not(actual_is_target_temp()): #aufheizen
			lcd_string("Aufheizen", LCD_LINE_1)	  
			lcd_string("", LCD_LINE_2)
  
		#printing paused		
		elif get_paused_value():	  
			lcd_string("Druck pausiert", LCD_LINE_1)
			lcd_string("", LCD_LINE_2)

		#printer is operating
		elif get_operational_value():
			lcd_string("Bereit", LCD_LINE_1)	  
			lcd_string("", LCD_LINE_2)
	  
def lcd_init():
	# Initialise display
	lcd_byte(0x33,LCD_CMD) # 00110011 Initialise
	lcd_byte(0x32,LCD_CMD) # 00110010 Initialise
	lcd_byte(0x06,LCD_CMD) # 00000110 Cursor move direction
	lcd_byte(0x0C,LCD_CMD) # 00001100 Display On,Cursor Off, Blink Off
	lcd_byte(0x28,LCD_CMD) # 00101000 Data length, number of lines, font size
	lcd_byte(0x01,LCD_CMD) # 00000001 Clear display
	time.sleep(E_DELAY)
 
def lcd_byte(bits, mode):
	# Send byte to data pins
	# bits = data
	# mode = True  for character, False for command
	GPIO.output(LCD_RS, mode) # RS, Register Select
	# High bits/ left nibble
	GPIO.output(LCD_D4, False)
	GPIO.output(LCD_D5, False)
	GPIO.output(LCD_D6, False)
	GPIO.output(LCD_D7, False)
	if bits&0x10==0x10:
		GPIO.output(LCD_D4, True)
	if bits&0x20==0x20:
		GPIO.output(LCD_D5, True)
	if bits&0x40==0x40:
		GPIO.output(LCD_D6, True)
	if bits&0x80==0x80:
		GPIO.output(LCD_D7, True)
 
	#Toggle 'Enable' pin
	lcd_toggle_enable()
 
	#Low bits/ right nibble
	GPIO.output(LCD_D4, False)
	GPIO.output(LCD_D5, False)
	GPIO.output(LCD_D6, False)
	GPIO.output(LCD_D7, False)
	if bits&0x01==0x01:
		GPIO.output(LCD_D4, True)
	if bits&0x02==0x02:
		GPIO.output(LCD_D5, True)
	if bits&0x04==0x04:
		GPIO.output(LCD_D6, True)
	if bits&0x08==0x08:
		GPIO.output(LCD_D7, True)

	#Toggle 'Enable' pin
	lcd_toggle_enable()
 
def lcd_toggle_enable():
	#Toggle enable
	time.sleep(E_DELAY)
	GPIO.output(LCD_E, True)
	time.sleep(E_PULSE)
	GPIO.output(LCD_E, False)
	time.sleep(E_DELAY)
 
def lcd_string(message,line):
	#Send string to display
	message = message.ljust(LCD_WIDTH," ")
	lcd_byte(line, LCD_CMD)
	for i in range(LCD_WIDTH):
		lcd_byte(ord(message[i]),LCD_CHR)

#thread-function for clockthread	
def clockthread ():
	#define global variables
	global thread_interrupt
	global lcd_switch
	thread_interrupt = True
	while thread_interrupt:
		lcd_switch = False
		time.sleep(5)
		lcd_switch = True
		time.sleep(5)	
	print("clockthread interrupted")
  
#--------------------------------------
#actual programm 
if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:	
		print("KeyboardInterrupt")
		thread_interrupt = False
		t1.exit()
	finally:
		thread_interrupt = False
		t1.exit()
		lcd_byte(0x01, LCD_CMD)
		GPIO.cleanup()
		print("programm lcd_resttime.py terminated")
