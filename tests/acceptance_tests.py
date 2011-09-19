#!/usr/bin/env python3

from subprocess import Popen, PIPE
from unittest import main, TestCase


class AcceptanceTest(TestCase):

    def test_version(self):
        command = './lis.py --version'.split()
        output = Popen(command, stdout=PIPE).communicate()[0]
        self.assertEqual(output, b'v0.1\n')

    def test_run_file(self):
        command = './lis.py tests/test_data/display_123.lis'.split()
        output = Popen(command, stdout=PIPE).communicate()[0]
        self.assertEqual(output, b'123\n456\n')

    
if __name__ == '__main__':
    main()

