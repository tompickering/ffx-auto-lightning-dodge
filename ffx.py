#!/usr/bin/env python3

import cv2
import subprocess
from datetime import datetime

WIN_LEN = 10

TIME_SINCE_MOVE = None


def move():
    print('MOVE')
    global TIME_SINCE_MOVE
    TIME_SINCE_MOVE = datetime.now()
    subprocess.run(['/home/tom/projects/ps2_teensy/send_fwd_bg.sh'])
    print('MOVE DONE')


def flash():
    print('FLASH')
    try:
        subprocess.run(['/home/tom/projects/ps2_teensy/send_x.sh'])
        move()
    except:
        pass


class FlashDetector(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.win = [255]*WIN_LEN
        self.idx = 0

    def avg(self):
        return sum(self.win)/len(self.win)

    def isFlash(self, frame):
        new_val = frame[self.y][self.x].mean()

        flash = None

        avg = self.avg()

        if new_val >= 1.1 * avg:
            flash = True

        if new_val <= 0.9 * avg:
            flash = False

        if avg >= 252:
            flash = None

        self.win[self.idx] = new_val
        self.idx = (self.idx + 1) % len(self.win)

        return flash


def make_detector(frame, x_prop, y_prop):
    ymax = len(frame)
    xmax = len(frame[0])
    return FlashDetector(int(x_prop*xmax), int(y_prop*ymax))


cv2.namedWindow('FFX')
vc = cv2.VideoCapture(0)
vc.set(cv2.CAP_PROP_FPS, 30)

rval = None

if vc.isOpened():
    rval, frame = vc.read()

PROP_MIN = 0.35
PROP_DIV = 8
PROPS = [PROP_MIN + i*((1-2*PROP_MIN)/PROP_DIV) for i in range(PROP_DIV)]

detectors = [make_detector(frame, xp, yp) for yp in PROPS for xp in PROPS]

cooldown = 0

while rval:
    #cv2.imshow('FFX', frame)

    if TIME_SINCE_MOVE is None:
        move()
    elif (datetime.now() - TIME_SINCE_MOVE).seconds > 20:
        move()

    rval, frame = vc.read()

    if cooldown > 0:
        cooldown -= 1
    else:
        flashes = [d.isFlash(frame) for d in detectors]
        n_yes = len([x for x in flashes if x is True])
        n_no = len([x for x in flashes if x is False])
        n_q = len([x for x in flashes if x is None])
        if n_no < 4 and n_q < 30:
            cooldown = 30
            flash()

    for d in detectors:
        for dx in range(-2,2):
            for dy in range(-2,2):
                frame[d.y+dy][d.x+dx][0] = 0x00;
                frame[d.y+dy][d.x+dx][1] = 0x00;
                frame[d.y+dy][d.x+dx][2] = 0xFF;

    cv2.imshow('FFX', frame)
    key = cv2.waitKey(1)
    if key == 27:
        break

