# -​*- coding: utf-8 -*​-
u"""Código que simula o client que fica enviando imagens."""

from cStringIO import StringIO
from time import sleep
import requests
from PIL import Image
import cv2
import numpy
cv = cv2.cv


TIME_STEP = 2
FRAME_RATE = 24
SERVER_URL = "http://localhost:5000/camera_feed"


def capture():
    u"""Captura continuamente frames da camera e joga no redis."""
    vc = cv2.VideoCapture('/Users/nano/Desktop/p2.m4v')

    # vc = cv2.VideoCapture(0)
    if vc.isOpened():  # try to get the first frame
        rval, frame = vc.read()
    else:
        rval = False

    frame_count = 0
    while rval:
        rval, frame = vc.read()
        frame_count += 1
        print frame_count
        if frame_count >= FRAME_RATE * TIME_STEP:
            frame_count = 0
            # frame = cv2.resize(frame, (720, 480))
            # import ipdb;ipdb.set_trace()
            frame_string = frame.tostring()
            imagem = Image.frombytes('RGB', (frame.shape[1], frame.shape[0]), frame_string)
            b, g, r = imagem.split()
            imagem = Image.merge("RGB", (r, g, b))
            arquivo = StringIO()
            imagem.save(arquivo, "png")
            arquivo.seek(0)
            files = {'file': arquivo}
            try:
                requests.post(SERVER_URL, files=files)
            except Exception, e:
                print e

        key = cv2.waitKey(20)
        if key == 27:  # exit on ESC
            break

capture()
