#https://hackaday.io/project/12922-bluetooth-data-owon-b35t-multimeter#menu-description
#https://github.com/gregpinero/ArduinoPlot/blob/master/Arduino_Monitor.py
#https://github.com/reaper7/M5Stack_BLE_client_Owon_B35T/blob/master/M5Stack_BLE_client_Owon_B35T.ino
#https://code-maven.com/interactive-shell-with-cmd-in-python

#TODO - timeouts
#TODO - odzkouset deltu na vsech rozsazich
#TODO - tlacitka z https://github.com/reaper7/M5Stack_BLE_client_Owon_B35T/blob/master/M5Stack_BLE_client_Owon_B35T.ino

import serial
import threading
import datetime
import operator
import sys
import logging as log


DATA_LENGTH = 14
ABSOLUTE_ERROR = 5 #max least significant digit deviation
RELATIVE_ERROR = 10 #in %, max difference between two measurements


received_data = [] #global variable for transfering the from serial_thread

###############################################################################################################################
#                                                       WARNINGS                                                              #
#                                                                                                                             #
###############################################################################################################################
#0.001 does NOT equal 10 ** (-3) (python2 only) --> all unit prefixes must be in scientific format (10e(n))

#Mode 48 - occurs when rotating the switch - handled by try...except in the serial thread

#Python 3 handles strings differenty (The string type in Python 2 is a list of 8-bit characters, 
#but the bytes type in Python 3 is a list of 8-bit integers.
#http://python3porting.com/problems.html) --> removed ord(), use bytearray()

#Amps range does contain 00 00 (00 and units),
#so I have to check for more 00 bytes in a sequence)


###############################################################################################################################
#                                                   Others - classes                                                          #
#                                                                                                                             #
###############################################################################################################################
class B35T_MeasuredValue(object):
    #digits,
    #units,
    #mode,
    #dateTime
    
    def __init__(self, dateTime, digits, units, mode, LSD_position):
        self.digits = digits
        self.units = units
        self.mode = mode
        self.dateTime = dateTime
        self.LSD_position = LSD_position #position of the least significant digit (e.g. 0.1, 0.01, ...)
        
    def matches(self, B):
        log.info('Entered matches')
        log.debug('matches - Comparing {} to {}'.format(str(self), str(B)))
        if not self.mode == B.mode: return(False)

        valA = round(self.digits * self.units.prefix, 12) #round because 1986 * 0.1 = 198.60000000000002
        valB = round(B.digits * B.units.prefix, 12)
        
        if valA == 0: #to prevent division by zero
            if valB == 0 : difference = 0
            else : difference = 99999 #to fail in the % condition
        else:
            difference = abs((valB - valA) / valA * 100) #in %, relative to A
        if difference > RELATIVE_ERROR:
            log.debug('matches - % difference too high ({}% > {}%)'.format(difference, RELATIVE_ERROR))
            absolute_difference = abs(valA - valB)
            if absolute_difference > (self.LSD_position * ABSOLUTE_ERROR * self.units.prefix + B.LSD_position * ABSOLUTE_ERROR * B.units.prefix):
                log.debug('matches - Absolute difference too high ({}). Returning False'.format(absolute_difference))
                return(False)
        log.debug('matches - Returning True')
        return(True)
                            
    def __str__(self):
        return ('{};{};{};{}'.format(self.dateTime, self.digits, self.units, self.mode))  
        
    def __repr__(self):
        return ('{}({}, {}, {}, {})'.format(self.__class__.__name__, repr(self.dateTime), repr(self.digits), repr(self.units), repr(self.mode), repr(self.LSD_position)))
               
class B35T_Unit(object):
    #_prefix,
    #unitStr
    
    
    def __init__(self, prefix, unitStr):
        self.prefix = prefix
        self.unitStr = unitStr
    
    def prefixStr(self, prefix):
        prefixDict = {
        1e-9: 'n',
        1e-6: 'u',
        1e-3: 'm',
        1: '',
        1e3: 'k',
        1e6: 'M',
        }
        return(prefixDict.get(prefix, 'BAD'))
        
    prefix = property(operator.attrgetter('_prefix')) #validation
    @prefix.setter
    def prefix(self, p):
        if (self.prefixStr(p) == 'BAD'): raise Exception("Invalid prefix: {}".format(p))
        self._prefix = p    
            
    def __str__(self):
        return('{}{}'.format(self.prefixStr(self.prefix), self.unitStr))
        
    def __repr__(self):
        return ('{}({}, {})'.format(self.__class__.__name__, repr(self.prefix), repr(self.unitStr)))
        
class serial_thread(threading.Thread):
    def __init__(self, ser):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.ser = ser
        self.alive = True
        
    def run(self):
        global received_data
        recv_data = bytearray('', 'ascii')
        log.info('serial_thread - Syncing')
        self._ser_sync()
        while not self.stop_event.is_set():
            log.debug('serial_thread - Waiting')
            while not self.ser.inWaiting() >= DATA_LENGTH : pass #wait for the data
            log.debug('serial_thread - Receiving')
            recv_data = self.ser.read(DATA_LENGTH)
            try:
                log.debug('serial_thread - Received: {}'.format(recv_data))
                received_data.append(self._getValue(bytearray(recv_data))) #list.append() is thread safe https://stackoverflow.com/questions/6319207/are-lists-thread-safe
                log.info('serial_thread - Added value: {}'.format(str(received_data[-1]))) #nothing else is writing to this variable
            except Exception as e:
                log.error('serial_thread - Exception {} occured.'.format(str(e)))
                self._ser_sync() #resynchronize
                #raise #cannot re-raise the same exception because it wouldn't be handled
        log.info('serial_thread - Thread killed')
        self.alive = False

    def _ser_sync(self):
        '''Drops everything and waits for valid data'''
        log.info('Entered _ser_sync')
        self.ser.flushInput()
        skip = 0
        a = bytearray('abcd', 'ascii')
        while skip >= 0:
            if self.ser.inWaiting() > 0:
                for i in range(3): #shift the array
                    a[i] = a[i + 1]
                a[3] = ord(self.ser.read(1))
                log.debug('_ser_sync - a = {}'.format(repr(a)))

                if a == bytearray([0,0,0,0]): #drop the first n logs (zeros, DMM ID and junk) (see warnings)
                    skip = 4 #skip the next 5 logs (including the zeros) (see protokol.txt)
                    log.debug('_ser_sync - zeros')

                if a[-2:] == bytearray('\r\n', 'ascii'):
                    skip -= 1
                    log.debug('_ser_sync - newline')

    def _getValue(self, raw_data):
        '''Gets value from raw data'''
        (digits, LSD_position) = self._digitsFloat(raw_data[:5], raw_data[6])
        units = self._unitsObj(raw_data[9:11])
        mode = self._modeStr(raw_data[7])
        return (B35T_MeasuredValue(datetime.datetime.now(), digits, units, mode, LSD_position))
    
    
    def _unitsObj(self, units): 
        '''Returns Unit eg. mV = Unit(0.001, 'V')'''
        unitsDict = {
            (64, 128): (1e-3, 'V'),
            (0, 128): (1, 'V'),
            (0, 32): (1, 'Ohm'),
            (32, 32): (1e3, 'Ohm'),
            (16, 32): (1e6, 'Ohm'),
            (0, 64): (1, 'A'),
            (64, 64): (1e-3, 'A'),
            (128, 64): (1e-6, 'A'),
            (0, 1): (1, u'degF'),
            (0, 2): (1, u'degC'),
            (0, 8): (1, 'Hz'),
            (2, 0): (1, '%'),
            (0, 16): (1, 'hFE'),
            (4, 128): (1, 'V-diode'),
            (0, 4): (1e-9,'F'),
            (128, 4): (1e-6, 'F'),
            (8, 32): (1, 'Ohm-continuity'),
        }
        (prefix, unit) = unitsDict.get((units[0], units[1]), (0, 0))
        if prefix == 0 and unit == 0:
            raise Exception('<unknown unit {} {}>'.format(repr(units[0]), repr(units[1])))
     
        return(B35T_Unit(prefix, unit))

    def _modeStr(self, mode):
        '''Returns string representing the current mode'''
        modeDict = {
            0: '', #DUTY, hFE, temperature, V-diode
            1: '(Ohm-manual)', #manual ranging + continuity
            8: '(AC-minmax)',
            9: '(AC-manual)',
            12: '(AC delta)', #may be something else, but it is present when AC delta
            16: '(DC-minmax)',
            17: '(DC-manual)',
            20: '(delta)', #may be wrong
            #21 - when switching to delta - did not occur during debugging
            32: '', #Hz, F
            33: '(Ohm-auto)',
            41: '(AC-auto)',
            #48 I think it occurs when rotating the range switch
            49: '(DC-auto)',
            51: '[HOLD]',
        }
        modeS = modeDict.get(mode, 'BAD')
        if modeS == 'BAD': raise Exception('<unknown mode {}>'.format(repr(mode)))
        return(modeS)

    def _digitsFloat(self, sign_digits_str, decimal_position):
        '''Converts the received digits to a float. Returns (digits, LSD_position)'''
        log.info('Entered _digitsFloat')
        coefDict = {
            48: 1,
            49: 0.001,
            50: 0.01,
            52: 0.1,
        }
        if sign_digits_str[1] == ord('?') and sign_digits_str[4] == ord('?'):
          result = 99999 #O.L
        else: 
            try:
                result = int(sign_digits_str)
            except Exception as e:
                log.error('_digitsFloat - Exception {} occured.'.format(str(e)))
                log.info('_digitsFloat - Exception - Data: sign_digits_str: {}, decimalpos: {}'.format(sign_digits_str, decimal_position))
                raise Exception('Could not convert to int: {}'.format(sign_digits_str))
        
        coef = coefDict.get(decimal_position, 'BAD')
        log.debug('_digitsFloat - coef: {}, result: {}'.format(coef, result))
        if coef != 'BAD': result *= coef
        else: raise Exception('Could not get coefficient: {}'.format(repr(decimal_position)))
        result = round(result, 4) #to remove floating point operations least significant digit junk
        log.debug('_digitsFloat - returning ({}, {})'.format(result, coef))
        return((result, coef))
    
###############################################################################################################################
#                                                      B35T class                                                             #
#                                                                                                                             #
###############################################################################################################################
class B35T(object):
    #ser,
    #logFile
    
    def __init__(self, port, verbose=False, logFileName=None):
        if verbose:
            log.basicConfig(format='%(asctime)s    %(levelname)s: %(message)s', filename=logFileName, level=log.DEBUG)
            log.info("Verbose output.")
        else:
            log.basicConfig(filename=logFileName)
        
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=9600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
        except serial.serialutil.SerialException:
            self.ser = None
            log.error('Bad serial port')
        else:
            self.serialThread = serial_thread(self.ser)
            self.serialThread.start()
            
    def __del__(self):
        if not self.ser is None:
            self.serialThread.stop_event.set()
            while self.serialThread.alive:
                pass #wait for the thread to die
            self.ser.close()
        
    
    def measure(self, count=3, retries=10):
        '''measures (takes readings until the last [count] don't differ)'''
        log.info('Entered measure')
        i = 0
        ok = False
        error_counter = 0
        last_time = datetime.datetime.now()
        readings = [None] * count
        while not ok:
            #get reading
            temp = received_data[-1] #because of the thread
            if temp.dateTime > last_time:
                readings[i] = temp
                last_time = datetime.datetime.now()
                log.debug('measure - New reading (i={}): {}'.format(i, str(temp)))
                i+= 1    
            
            if i >= count : #process the data
                log.debug('measure - i >= {}'.format(count))
                readingsMatch = True
                for r in readings:
                    log.debug('measure - Processing {}    ;    comparing to {}'.format(str(r), str(readings[0])))
                    if not readings[0].matches(r):
                        readingsMatch = False
                        log.debug('measure - Readings do not match')
                  
                if readingsMatch: #the last [count] readings are OK
                    ok = True
                else:
                    if error_counter >= retries - 1:
                        log.error('measure - Value is not stable') 
                        raise Exception('Value is not stable')

                    error_counter += 1
                    for j in range(count - 1): readings[j] = readings[j + 1] #shift the array
                    i-= 1 #take another reading

        log.info('measure - returned {}'.format(str(readings[-1])))
        return(readings[-1])
        
    def read(self):
        '''Reads a value from the DMM (does not check for unstability and may return old value in case the program freezes)'''
        return(received_data[-1])
        
    def __str__(self):
        return('B35T DMM on port {}'.format(str(ser)))