# -​*- coding: utf-8 -*​-
u"""Identificador de tiro de arco e flecha."""

import os
import json
from cStringIO import StringIO
from flask import Flask, Blueprint, jsonify, request, render_template, send_file
import cv2
from redis import Redis
import numpy
from PIL import Image, ImageMath, ImageEnhance

DB = Redis(host="127.0.0.1", port=6379, db=0)

IMAGE_DIR = "/Users/nano/Pictures/MPlayerX/"


tamanho = (400, 400)


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


@home.route('/<index>', methods=['GET'])
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
    e.save(arquivo, "png")
    arquivo.seek(0)
    response = send_file(arquivo, as_attachment=False, attachment_filename="diferenca.png")
    return response


@home.route('/setup', methods=['GET'])
def home_view():
    """Home."""
    context = {}
    return render_template('home.html', **context), 200


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
    app.run(host="0.0.0.0", port=5000, threaded=True)
