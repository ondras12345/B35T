#!/usr/bin/env python

# This script runs tests according to files in tests/unit/fixtures/decoder directory
# Each test consists of test_name.log and test_name.val file_extension
# test_name.val contains reference object and is evaluated - it must pass a regex

import unittest
import os
import re
import datetime  # used by evaluated expressions in .val files
import B35T

script_dir = os.path.dirname(__file__)  # absolute dir the script is in
fixtures_dir = os.path.join(script_dir, 'fixtures', 'decoder')

EVAL_VALUE_REGEX_STRING = ("^B35T\.B35T_MeasuredValue\("
                           "dateTime=datetime\.datetime\.now\(\), "
                           "digits=[0-9.]{1,}, "
                           "units=B35T\.B35T_Unit\([0-9e\-]{1,}, '[a-zA-Z\-]{1,}'\), "
                           "mode='[\(\)a-zA-Z\-]{0,}', "
                           "LSD_position=[01.]{1,}"
                           "\)$")

EVAL_VALUE_REGEX_PATTERN = re.compile(EVAL_VALUE_REGEX_STRING)


def check_eval(text):
    return EVAL_VALUE_REGEX_PATTERN.match(text)


class TestBasic(unittest.TestCase):

    def test_basic_values(self):
        test_filenames = {}
        for filename in os.listdir(fixtures_dir):  # build dictionary of test files
            (file_name, file_extension) = os.path.splitext(filename)

            if file_name not in test_filenames:
                test_filenames[file_name] = {}

            if file_extension == '.data':
                test_filenames[file_name]['message'] = filename
            elif file_extension == '.val':
                test_filenames[file_name]['value'] = filename
            else:
                raise Exception('Unexpected file: {}'.format(filename))

        for test in test_filenames:  # run the test
            print('testing: {}'.format(test), end='')
            if 'message' not in test_filenames[test] or 'value' not in test_filenames[test]:
                raise Exception('File missing for test: {}'.format(test))

            message_filename = test_filenames[test]['message']
            value_filename = test_filenames[test]['value']

            message_file = open(os.path.join(fixtures_dir, message_filename), 'rb')
            message = bytearray(message_file.read())
            message_file.close()

            if not len(message) == B35T.DATA_LENGTH:
                raise Exception('Unexpected message length: {}  message: {}'.format(len(message), message))

            value_file = open(os.path.join(fixtures_dir, value_filename), 'r')
            value_text = value_file.read()
            value_file.close()

            if check_eval(value_text):
                value = eval(value_text)
            else:
                raise Exception('BAD value object definition: {}'.format(value_text))

            decoder = B35T.B35T_protocol_decoder(message)
            value_decoded = decoder.get_value()

            error = False
            # B35T_MeasuredValue.matches() doesn't check for these:
            if not value.LSD_position == value_decoded.LSD_position:
                error = True

            if not value.digits == value_decoded.digits:
                error = True

            if not repr(value.units) == repr(value_decoded.units):
                error = True

            match = value.matches(value_decoded)
            OK = bool(match and not error)
            spaces = ' ' * (40 - len(test))
            print('{}{}'.format(spaces, OK))
            if not OK:
                print('    decoded: {}'.format(value_decoded))
            self.assertTrue(OK)


if __name__ == '__main__':
    unittest.main()
