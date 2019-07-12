#!/usr/bin/env python

import unittest
from unittest.mock import patch
import os
import time
import B35T

script_dir = os.path.dirname(__file__)  # absolute dir the script is in
fixtures_dir = os.path.join(script_dir, 'fixtures', 'serial_thread')
fixture_log = os.path.join(fixtures_dir, 'log.data')

requested_full = 0


def fixture_log_remaining():
    # print('inWaiting: {}'.format(len(fixture_log_data)))
    return(len(fixture_log_data) - 1)  # -1 to prevent exception on last message


def fixture_log_read(data_length):
    global requested_full

    if data_length > 1:
        requested_full += 1
    else:
        requested_full = 0

    data = fixture_log_data[0:data_length]
    del fixture_log_data[0:data_length]
    # print('requestsed: {}'.format(data_length))
    # print('returning: {}'.format(data))
    if fixture_log_remaining() <= B35T.DATA_LENGTH * 50:
        time.sleep(1)  # poison the thread
    return(data)


def mocked_Serial(*args, **kwargs):
    return None


class TestBasic(unittest.TestCase):
    def setUp(self):
        global fixture_log_data

        file = open(fixture_log, 'rb')
        fixture_log_data = bytearray(file.read())
        file.close()

    @patch('serial.Serial.inWaiting', side_effect=fixture_log_remaining)
    @patch('serial.Serial.read', side_effect=fixture_log_read)
    @patch('serial.Serial.__init__', side_effect=mocked_Serial)
    @patch('serial.Serial.flushInput')
    @patch('serial.Serial.close')
    def test_if_decodes(self, mocked_inWaiting, mocked_read, mocked_Serial, mocked_flush, mocked_close):
        global requested_full

        error = False

        try:
            DMM = B35T.B35T('COM_fake', verbose=False)

            while requested_full == 0:
                pass  # wait until full message requested

            # print('_______________________join________________________')  # joining in

            while fixture_log_remaining() >= B35T.DATA_LENGTH * 100:  # wait for some data
                pass

            readings = B35T.received_data
            readings.append('last')
            found = {}
            for reading in readings:
                if reading == 'last':
                    print('Got to the last reading - something is wrong')
                    error = True
                    break

                found[reading.units.unitStr] = True

                if len(found) >= 3 and 'V' in found:
                    break

        except Exception as e:
            error = True
            print(e)
            print('++++++++++++++++++++++++++++++++++++++++++++++++++')
            # raise  # re-raise for debug
        finally:
            del DMM

        self.assertFalse(error)


if __name__ == '__main__':
    unittest.main()
