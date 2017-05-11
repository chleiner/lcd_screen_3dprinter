#!/usr/bin/python
#--------------------------------------

# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*
# 4 : RS (Register Select)
# 5 : R/W (Read Write)       - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0             - NOT USED
# 8 : Data Bit 1             - NOT USED
# 9 : Data Bit 2             - NOT USED
# 10: Data Bit 3             - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND
 
#--------------------------------------
#import
import RPi.GPIO as GPIO
import time
import sys
sys.path.append("/home/pi/scripts/")
from octoapi import *
from threading import Thread



#--------------------------------------
# Define GPIO to LCD mapping
LCD_RS = 7
LCD_E  = 8
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 18

#--------------------------------------
# Define some device constants
LCD_WIDTH = 16    # Maximum characters per line
LCD_CHR = True
LCD_CMD = False
LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line

#--------------------------------------
# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

#--------------------------------------
#definitions
def main():
  
  #gpio settings (config pins/ setup pins (in/out))
  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)      #standard config
  GPIO.setup(LCD_E, GPIO.OUT)  
  GPIO.setup(LCD_RS, GPIO.OUT) 
  GPIO.setup(LCD_D4, GPIO.OUT) 
  GPIO.setup(LCD_D5, GPIO.OUT) 
  GPIO.setup(LCD_D6, GPIO.OUT) 
  GPIO.setup(LCD_D7, GPIO.OUT) 
 
  # Initialise display
  lcd_init()

  #change var init
  global lcd_switch
  
  #start Thread
  t1 = Thread(target = clockthread)
  t1.start()
  print("clockthread started")
 
  #infinity loop
  while True:
    #get status
    printstate = get_completion()
    if printstate ==  None: # proof if printstate is None
        printstate = 0
    elif printstate > 100:
        printf("Error - printstate value >100")
        break
    else:
        pass		

    #calculate Times
    timeinseconds =get_printTimeLeft()
    if timeinseconds == None: #case get_prinTimeLeft() returns None value
      hours = 0
      minutes = 0
      seconds = 0
    elif timeinseconds>=0: #case get_printTimeLeft() returns int value >=0
      hours = int(timeinseconds/3600)
      resttimehours = (timeinseconds/float(3600)) - hours 
      minutes = int((resttimehours * 60))
      resttimeminutes = (resttimehours *float(60)) - minutes
      seconds = int(resttimeminutes * 60)
    else: #case get_printTimeLeft() returns value <0
      print("Error - get_printTimeLeft() returns value <0")
    outputstring = str(hours) + "h " + str(minutes) + "m " + str(seconds) + "s"

    #send Display output
    if (lcd_switch): #output printstate
      lcd_string("Druckerstatus:",LCD_LINE_1)
      lcd_string("%i Prozent" %printstate,LCD_LINE_2) 
    elif (not(lcd_switch)): #output remaining time
      lcd_string("Restzeit:", LCD_LINE_1)
      lcd_string(outputstring , LCD_LINE_2)
     
def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(E_DELAY)
 
def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = data
  # mode = True  for character
  # False for command
  GPIO.output(LCD_RS, mode) # RS
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
 
  # Toggle 'Enable' pin
  lcd_toggle_enable()
 
  # Low bits/ left nibble
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
 
  # Toggle 'Enable' pin
  lcd_toggle_enable()
 
def lcd_toggle_enable():
  # Toggle enable
  time.sleep(E_DELAY)
  GPIO.output(LCD_E, True)
  time.sleep(E_PULSE)
  GPIO.output(LCD_E, False)
  time.sleep(E_DELAY)
 
def lcd_string(message,line):
  # Send string to display
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
#    if thread_interrupt == 1:
#      print("clockthread interrupted")
#      break 
    #clock
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
  finally:
    lcd_byte(0x01, LCD_CMD)
    GPIO.cleanup()
