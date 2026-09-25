"""First page:Welcome screen for app
Import the video 
This page allow import the video and start process """

import streamlit as st
import os
import sys
import time
import cv2
import subprocess
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from integration import 