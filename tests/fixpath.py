'''
Append parent dir to sys.path so that tests can import from it
'''
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

