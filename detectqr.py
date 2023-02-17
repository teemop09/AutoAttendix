import gc
import os
import time
from datetime import datetime

import cv2
import numpy as np
import pyautogui


def detect_otp_from_qr() -> str:
    """
    Detect for QR code indefinitely by taking screenshots.
    Once QR code is decoded, returns the OTP in str.
    """
    # the number of digits in the OTP
    # this variable is a constant
    OTP_LENGTH = 3
    # directory to save results
    cwd = os.path.abspath(os.getcwd())  # current working directory
    path = os.path.join(cwd, "results")
    # initialize the cv2 QRCode detector
    detector = cv2.QRCodeDetector()

    while True:
        # screenshot to get real time screen info
        ss = pyautogui.screenshot()
        # detect and decode
        data, bbox, straight_qr = detector.detectAndDecode(np.array(ss))
        # if a QR code is found
        # validate 'data' is the OTP we want
        if not data and not(data.isdigit() and len(data) == OTP_LENGTH):
            del ss, bbox, straight_qr
            gc.collect()
            # reduce cpu usage
            time.sleep(2)
            continue
        # Display and notify user if data is valid
        print(f"QRCode OTP: {data}")
        return data


if __name__ == '__main__':
    detect_otp_from_qr()
