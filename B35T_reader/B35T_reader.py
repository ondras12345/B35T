import sys
sys.path.append('C:/Users/ondra/Documents/Visual Studio 2017/Projects/Skripty/B35T/B35T') #to be able to import the B35T library while not in the same directory.
import B35T
from cmd import Cmd
import datetime
import time

#TODO - datetime - do not show milliseconds

COM_DEFAULT = 'COM19'

class MyPrompt(Cmd, object):
    prompt = '\n[disconnected] DMM> '
    logFileName = None
    verbose = False
    
    def do_logfile(self, inp):
        '''Logs errors into a file instead of displaying them. This has to be run before connect. Argument: filename.extension'''
        if dmm is None and not inp == '':
            self.logFileName = inp
        else:
            print('logfile has to be run before connect. Specify the path to file.')

    def do_verbose(self, inp):
        '''Turns on verbose mode. This has to be run before connect.'''
        if dmm is None:
            self.verbose = True
        else:
            print('verbose has to be run before connect.')

    def do_connect(self, inp):
        '''Connects to the DMM. Argument: COM_port'''
        global dmm
        if dmm is None:
            if inp == '':
                print('Defaulting to {}'.format(COM_DEFAULT))
                port = COM_DEFAULT
            else:
                print(inp)
                port = inp
            dmm = B35T.B35T(port, verbose = self.verbose, logFileName = self.logFileName)
            if not dmm.ser is None:
                self.prompt = '\n[connected] DMM> '
            else:
                dmm = None
        else:
            print('Already connected')
             
    def do_measure(self, inp):
        '''Measure the value and return it as text. Also logs if verbose'''
        if not dmm is None:
            try:
                print('Measurement: '), 
                print(str(dmm.measure()))
            except Exception as e:
                print('Exception: {} occured.'.format(str(e)))
        else:
            print('You have to connect first')
        
    def do_read(self, inp):
        '''Reads a value from the DMM (does not check for unstability and may return old value in case the program freezes)'''
        if not dmm is None:
            try:
                reading = dmm.read()
                timediff = datetime.datetime.now() - reading.dateTime            
                print('{} ({} ago)'.format(str(reading), timediff))
            except Exception as e:
                print('Exception: {} occured.'.format(str(e)))
        else:
            print('You have to connect first')
            
    def do_ping(self, inp):
        '''Prints the time elapsed since last reading. Argument: number_of_pings (each ping takes 1 second)'''
        if not dmm is None:
            if inp != '':
                count = int(inp)
                if count == 0 or count > 20:
                    print('Please enter a valid count.')
                    count = 0
            else:
                count = 5 #default

            for i in range(count):
                try:
                    reading = dmm.read()
                    timediff = datetime.datetime.now() - reading.dateTime            
                    print('{}   The last reading was taken {} ago:   {}'.format(datetime.datetime.now(), timediff, str(reading)))
                except Exception as e:
                    print('Exception: {} occured.'.format(str(e)))
                time.sleep(1)
            print ('Ping completed')
        else:
            print('You have to connect first')   
        
    def do_exit(self, inp):
        '''Exit the application'''
        return (True)
    
    do_EOF = do_exit
    do_quit = do_exit
        
if __name__ == '__main__':

    dmm = None
    
    p = MyPrompt()
    p.cmdloop() #the CLI
    print('End')
    del dmm
    sys.exit(1)