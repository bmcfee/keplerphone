#!/usr/bin/env python

import argparse
import flask
import ConfigParser
import mimetypes
import os
import re
import sys
import ujson as json
import keplerphone

DEBUG = True

# construct application object
app = flask.Flask(__name__)
app.config.from_object(__name__)


def load_config(server_ini):
    P = ConfigParser.RawConfigParser()

    P.opionxform = str
    P.read(server_ini)

    CFG = {}
    for section in P.sections():
        CFG[section] = dict(P.items(section))

    for (k, v) in CFG['server'].iteritems():
        app.config[k] = v
    return CFG


def run(**kwargs):
    app.run(**kwargs)


@app.route('/keplerphone/<int:kic>/<str:scale>')
def make_music(kic, scale):

    return json.encode(keplerphone.make_music(kic,
                                              app.config['sf2'],
                                              my_scale=scale))

# @app.route('/audio/<int:track_id>')
# def get_track_audio(track_id):
#     return send_file_partial(data_layer.get_track_audio(track_id), cache_timeout=0)

@app.route('/scales')
def get_scales():
    return json.encode(keplerphone.get_scales())


@app.route('/ids')
def get_ids():
    return json.encode(keplerphone.get_ids())


@app.route('/')
def index():
    '''Top-level web page'''
    return flask.render_template('index.html')


# -- partial content streaming

# from flask import request, send_file, Response

@app.after_request
def after_request(response):
    response.headers.add('Accept-Ranges', 'bytes')
    return response


def send_file_partial(path, **kwargs):
    """
        Simple wrapper around send_file which handles HTTP 206 Partial Content
        (byte ranges)
        TODO: handle all send_file args, mirror send_file's error handling
        (if it has any)
    """
    range_header = flask.request.headers.get('Range', None)
    if not range_header:
        return flask.send_file(path, **kwargs)

    size = os.path.getsize(path)
    byte1, byte2 = 0, None

    m = re.search('(\d+)-(\d*)', range_header)
    g = m.groups()

    if g[0]:
        byte1 = int(g[0])

    if g[1]:
        byte2 = int(g[1])

    length = size - byte1
    if byte2 is not None:
        length = byte2 - byte1

    data = None
    with open(path, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)

    rv = flask.Response(data,
                        206,
                        mimetype=mimetypes.guess_type(path)[0],
                        direct_passthrough=True)
    rv.headers.add('Content-Range',
                   'bytes {0}-{1}/{2}'.format(byte1, byte1 + length - 1, size))

    return rv


# Main block
def process_arguments(args):

    parser = argparse.ArgumentParser(description='Keplerphone web server')

    parser.add_argument('-i',
                        '--ini',
                        dest='ini',
                        required=False,
                        type=str,
                        default='server.ini',
                        help='Path to server.ini file')

    parser.add_argument('-p',
                        '--port',
                        dest='port',
                        required=False,
                        type=int,
                        default=5000,
                        help='Port')

    parser.add_argument('--host',
                        dest='host',
                        required=False,
                        type=str,
                        default='0.0.0.0',
                        help='host')

    return vars(parser.parse_args(args))


if __name__ == '__main__':
    parameters = process_arguments(sys.argv[1:])

    CFG = load_config(parameters['ini'])

    port = parameters['port']

    if os.environ.get('ENV') == 'production':
        port = int(os.environ.get('PORT'))

    run(host=parameters['host'], port=port, debug=DEBUG, processes=3)
