#!/usr/bin/env python
# -​*- coding: utf-8 -*​-
u"""Identificador de tiro de arco e flecha."""

import os
import json
from cStringIO import StringIO
from flask import Flask, Blueprint, jsonify, request, render_template, send_file
import cv2
from redis import Redis
import numpy
from PIL import Image, ImageMath, ImageEnhance, ImageOps, ImageFilter

DB = Redis(host="127.0.0.1", port=6379, db=0)

IMAGE_DIR = "/Users/nano/Pictures/MPlayerX/"


tamanho = (400, 400)


def diferenca(a, b):
    pontos = json.loads(DB.get("pontos_perspectiva"))
    a = a.convert("L")
    b = b.convert("L")
    # a.show()
    c = ImageMath.eval("a - b", a=a, b=b)
    e = Image.new("RGB", c.size, 0)
    f = e.load()
    d = c.load()
    for x in xrange(c.width):
        for y in xrange(c.height):
            cor = d[x, y]
            f[x, y] = (0, 0, 0) if cor < 0 else (cor, cor, cor)
    e = ImageOps.invert(e)
    e = e.filter(ImageFilter.BLUR)
    enhancer = ImageEnhance.Brightness(e)
    e = enhancer.enhance(2)
    enhancer = ImageEnhance.Contrast(e)
    e = enhancer.enhance(8)

    return e


def perspectiva(imagem, pontos, tamanho):
    pa = ((0, 0), (tamanho[0], 0), (0, tamanho[1]), (tamanho[0], tamanho[1]))
    pb = pontos

    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])

    A = numpy.matrix(matrix, dtype=numpy.float)
    B = numpy.array(pb).reshape(8)

    res = numpy.dot(numpy.linalg.inv(A.T * A) * A.T, B)
    b = imagem.transform(tamanho, Image.PERSPECTIVE, numpy.array(res).reshape(8),
                         Image.BICUBIC)
    return b


app = Flask(__name__)
app.secret_key = 's3cr3t'

home = Blueprint('home', __name__)


@home.route('/diferenca/<index>', methods=['GET'])
def diferenca_view(index):
    """Home."""
    index = int(index)
    pontos = json.loads(DB.get("pontos_perspectiva"))

    b = Image.open(IMAGE_DIR + os.listdir(IMAGE_DIR)[index]).convert("L")
    b = perspectiva(b, pontos, (594, 420))
    # b.show()
    a = Image.open(IMAGE_DIR + os.listdir(IMAGE_DIR)[index - 1]).convert("L")
    a = perspectiva(a, pontos, (594, 420))
    # a.show()
    c = ImageMath.eval("a - b", a=a, b=b)
    e = Image.new("RGB", c.size, 0)
    f = e.load()
    d = c.load()
    for x in xrange(c.width):
        for y in xrange(c.height):
            cor = d[x, y]
            f[x, y] = (0, 0, 0) if cor < 0 else (cor, cor, cor)
    # e.show()

    arquivo = StringIO()
    e = ImageOps.invert(e)
    e = e.filter(ImageFilter.BLUR)
    enhancer = ImageEnhance.Brightness(e)
    e = enhancer.enhance(2)
    enhancer = ImageEnhance.Contrast(e)
    e = enhancer.enhance(8)
    e.save(arquivo, "png")
    e.save("/Users/nano/Desktop/teste.png")
    arquivo.seek(0)

    im = cv2.imread("/Users/nano/Desktop/teste.png")
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, numpy.pi/180, 150)
    # for rho, theta in lines[0]:
    #     a = numpy.cos(theta)
    #     b = numpy.sin(theta)
    #     x0 = a*rho
    #     y0 = b*rho
    #     x1 = int(x0 + 1000*(-b))
    #     y1 = int(y0 + 1000*(a))
    #     x2 = int(x0 - 1000*(-b))
    #     y2 = int(y0 - 1000*(a))
    if lines is not None:
        for x1, y1, x2, y2 in lines[0]:
            cv2.line(im, (x1, y1), (x2, y2), (0, 0, 255), 2)

    frame_string = im.tostring()
    e = Image.frombytes('RGB', (im.shape[1], im.shape[0]), frame_string)

    # # Create a detector with the parameters
    # params = cv2.SimpleBlobDetector_Params()

    # # Change thresholds
    # params.minThreshold = 10
    # # params.maxThreshold = 200

    # # Filter by Area.
    # params.filterByArea = True
    # params.minArea = 150

    # # Filter by Circularity
    # params.filterByCircularity = True
    # params.minCircularity = 0.1

    # # Filter by Convexity
    # params.filterByConvexity = True
    # params.minConvexity = 0.87

    # # Filter by Inertia
    # params.filterByInertia = True
    # params.minInertiaRatio = 0.01

    # # Set up the detector with default parameters.
    # # detector = cv2.SimpleBlobDetector()
    # detector = cv2.SimpleBlobDetector(params)

    # # Detect blobs.
    # keypoints = detector.detect(im)
    # print keypoints

    # # Draw detected blobs as red circles.
    # # cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS ensures the size of the circle corresponds to the size of blob
    # im_with_keypoints = cv2.drawKeypoints(im, keypoints, numpy.array([]), (0,255,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    # frame_string = im_with_keypoints.tostring()
    # e = Image.frombytes('RGB', (im_with_keypoints.shape[1], im_with_keypoints.shape[0]), frame_string)



    arquivo = StringIO()
    e.save(arquivo, "png")
    arquivo.seek(0)


    response = send_file(arquivo, as_attachment=False, attachment_filename="diferenca.png")
    return response


@home.route('/', methods=['GET'])
def home_view():
    """Home."""
    context = {}
    return render_template('home.html', **context), 200


@home.route('/setup', methods=['GET', 'POST'])
def setup_view():
    """Setup do sistema."""
    if request.method == "POST":
        dados = request.json.get("pontos")
        dados = [(i["x"], i["y"]) for i in dados]
        DB.set("pontos_perspectiva", json.dumps(dados))
        print dados
    context = {}
    return render_template('setup.html', **context), 200


@home.route('/camera_feed', methods=['GET', 'POST'])
def camera_feed():
    """Recebe e serve o feed de frames"""
    if request.method == "POST":
        arquivo = request.files.get('file').stream.read()
        DB.rpush("frames", arquivo)
        DB.ltrim("frames", -3, -1)
        return jsonify({"status": "ok"}), 200

    else:
        arquivo = StringIO()
        arquivo.write(DB.lrange("frames", -2, -1)[0])
        arquivo.seek(0)
        if request.args.get("corrected"):
            imagem = Image.open(arquivo)
            dados = json.loads(DB.get("pontos_perspectiva"))
            r = perspectiva(imagem, dados, (594, 420))
            arquivo = StringIO()
            r.save(arquivo, "png")
            arquivo.seek(0)

        elif request.args.get("difference"):
            imagem = Image.open(arquivo)
            dados = json.loads(DB.get("pontos_perspectiva"))
            a = perspectiva(imagem, dados, (594, 420))

            anterior = StringIO()
            anterior.write(DB.lrange("frames", -3, -2)[0])
            anterior.seek(0)
            imagem = Image.open(anterior)
            b = perspectiva(imagem, dados, (594, 420))

            d = diferenca(b, a)
            arquivo = StringIO()
            d.save(arquivo, "png")
            arquivo.seek(0)
        f = send_file(arquivo, as_attachment=False, attachment_filename="bla.png")
    return f


@home.route('/frame', methods=['GET'])
def frame_view():
    """Home."""
    arquivo = open(IMAGE_DIR + os.listdir(IMAGE_DIR)[2], "ro")
    f = send_file(arquivo, as_attachment=False, attachment_filename="bla.png")
    return f


@home.route('/perspectiva', methods=['GET'])
def perspectiva_view():
    """Home."""
    imagem = Image.open(IMAGE_DIR + os.listdir(IMAGE_DIR)[2])
    dados = json.loads(request.args['pontos'])
    dados = [(i["x"], i["y"]) for i in dados]
    DB.set("pontos_perspectiva", json.dumps(dados))
    r = perspectiva(imagem, dados, (594, 420))
    arquivo = StringIO()
    r.save(arquivo, "png")
    arquivo.seek(0)
    response = send_file(arquivo, as_attachment=False, attachment_filename="corrigida.png")
    return response

app.register_blueprint(home)


@app.errorhandler(404)
def rotas(error):
    u"""Retorna o status 404 e alista das urls diponíveis."""
    urls = [["%s - %s" % (m, i.rule) for m in i.methods
             if m not in ("HEAD", "OPTIONS")]
            for i in app.url_map.iter_rules()]
    reposta = {'erro': 'url not found', 'status_code': 404,
               'urls_disponiveis': urls}
    return jsonify(reposta), 200

if __name__ == '__main__':
    app.use_reloader = True
    app.debug = True
    app.run(host="0.0.0.0", port=5001, threaded=True)
