#!/usr/bin/env python

"""A simple class for controlling a LCD screen based on the HD44780 chip
connected to a Raspberry PI using the GPIO pins.

The wiring for the LCD is as follows:
1 : GND
2 : 5V
3 : Contrast (0-5V)
4 : RS (Register Select)
5 : R/W (Read Write)       - GROUND THIS PIN (we only write to the screen)
6 : Enable or Strobe
7 : Data Bit 0             - NOT USED
8 : Data Bit 1             - NOT USED
9 : Data Bit 2             - NOT USED
10: Data Bit 3             - NOT USED
11: Data Bit 4
12: Data Bit 5
13: Data Bit 6
14: Data Bit 7
15: LCD Backlight +5V
16: LCD Backlight GND

This script is roughly based on the version created by Matt Hawkins
http://www.raspberrypi-spy.co.uk/2012/07/16x2-lcd-module-control-using-python/
"""

__author__ = 'Peter Slump <peter@yarf.nl>'
__license__ = 'MIT'
__version__ = '$Revision$'


import RPi.GPIO as GPIO
import time


class HD44780:
    
    MODE_DATA = True
    MODE_COMMAND = False
    
    DEFAULT_DELAY = 0.00005  # Time between two commands
    
    _lcd_data_pins = []
    _lcd_rs = None
    _lcd_e = None
    
    _num_chars = None
    _lines = []

    def __init__(self, rs, e, data_pins, num_chars, line_memory_positions, gpio_mode=GPIO.BCM):
        """Setup the class by giving the characteristics of the screen and
        how it's pinned to the Raspberry PI

        rs: function select, this port will be high for data (self.MODE_DATA)
            and low for commands (self.MODE_COMMAND)
        e: enable, this will port will be high when all pins ar in their
           correct position. By enabling this pin the LCD controller is
           able to read the data.
        data_pins: a list of 4 pins which is used to send the data.
        num_chars: The number of characters which is supported by the screen.
        line_memory_positions: A memory position for every line the
                               screen supports.
        gpio_mode: The GPIO mode (pinning mode) as you have pinned your
                   screen to the Raspberry PI.

        Example for a four lines display with 20 characters:

        >>> HD44780(rs=7, e=8, data_pins=[25, 24, 23, 18], num_chars=20, line_memory_positions=[0x80, 0xC0, 0x94, 0xD4])
        """

        # Configure all the used GPIO ports: put the all in outgoing mode
        GPIO.setmode(gpio_mode)
        
        GPIO.setup(rs, GPIO.OUT)
        GPIO.setup(e, GPIO.OUT)
        
        for pin in data_pins:
            GPIO.setup(pin, GPIO.OUT)

        # Store characteristics for later usage
        self._lcd_data_pins = data_pins
        self._lcd_rs = rs
        self._lcd_e = e
        
        self._num_chars = num_chars
        self._lines = line_memory_positions
        
        self._init_lcd()
        
    def print_text(self, message):
    
        lines = message.split("\n")
        
        for index, memory_location in enumerate(self._lines):
            self._send_bytes(memory_location, self.MODE_COMMAND)
            
            try:
                line = lines.pop(0).ljust(self._num_chars, " ")
            except IndexError:
                line = " " * self._num_chars                
            
            for character_index in range(self._num_chars):
                self._send_bytes(ord(line[character_index]), self.MODE_DATA)
        
    def _init_lcd(self):
        """Initialize the LCD screen."""

        # Function mode:
        # DB7 DB6 DB5 DB4 DB3 DB2 DB1 DB0

        # Two line mode, Display off
        #  0   0   1   0   1   0   0   0
        self._send_bytes(0x28, self.MODE_COMMAND)

        # Display on, Cursor Off, Blink Off
        #  0   0   0   0   1   1   0   0
        self._send_bytes(0x0C, self.MODE_COMMAND)

        # Clear display
        #  0   0   0   0   0   0   0   1
        self._send_bytes(0x01, self.MODE_COMMAND)
        
    def _send_bytes(self, bytes, mode):
        """Prepare bytes to be send to the screen.

        Since this code is written for a LCD screen which is wired in 4-bit
        mode we have to chunk every byte in two nibbles where the high bits
        go first and then the lower.
        """

        # Send high bits
        self._send_data(
            mode=mode,
            data=[
                bytes & 0x10 == 0x10,
                bytes & 0x20 == 0x20,
                bytes & 0x40 == 0x40,
                bytes & 0x80 == 0x80,
            ]
        )
         
        # Send low bits
        self._send_data(
            mode=mode,
            data=[
                bytes & 0x01 == 0x01,
                bytes & 0x02 == 0x02,
                bytes & 0x04 == 0x04,
                bytes & 0x08 == 0x08,
            ]            
        )
        
    def _send_data(self, mode, data):
        """Send the actual data to the screen."""

        GPIO.output(self._lcd_rs, mode)
        
        for pin in self._lcd_data_pins:
            GPIO.output(pin, data.pop(0))
        
        time.sleep(self.DEFAULT_DELAY)
        GPIO.output(self._lcd_e, True)
        time.sleep(self.DEFAULT_DELAY)
        GPIO.output(self._lcd_e, False)
        time.sleep(self.DEFAULT_DELAY)
        
if __name__ == '__main__':
    """When you run this scrip directly it will run a very simple console. All
    input will be written to the screen.
    """
    try:
        lines = ["Welcome..."]
    
        lcd = HD44780(rs=7, e=8, data_pins=[25, 24, 23, 18], num_chars=20, line_memory_positions=[0x80, 0xC0, 0x94, 0xD4])
        
        while True:
            
            lcd.print_text(message="\n".join(lines))
            
            input = raw_input(">")
        
            lines.append(input)
            lines = lines[-4:]
                    
    except KeyboardInterrupt:
        pass
    
    GPIO.cleanup()