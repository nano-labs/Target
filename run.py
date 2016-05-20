# -​*- coding: utf-8 -*​-
u"""Identificador de tiro de arco e flecha."""

import os
import json
from flask import Flask, Blueprint, jsonify, request, render_template, send_file
import cv2
import numpy
from PIL import Image

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


@home.route('/', methods=['GET'])
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
    r = perspectiva(imagem, dados, (594, 420))
    r.show()
    return jsonify(dados), 200


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
