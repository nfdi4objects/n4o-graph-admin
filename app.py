import os
from flask import Flask, render_template, redirect, request, make_response, url_for, jsonify, Response
from waitress import serve
import argparse as AP
import requests
import yaml
import hashlib
import logging
from pathlib import Path
from urllib.parse import urlparse

LOG_FILE = 'app.log'
IMPORTER_URL  ='http://importer:5020'
FUSEKI_URL  ='http://fuseki:3030'


logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/assets')
app.secret_key = 'your_secret_key'  # Replace with a strong secret key
users = []


def find_user(name):
    '''Find a user by username in the users list'''
    for user in users:
        if user['username'] == name:
            return user
    return None


def pw_hash(pw_str):
    '''Hash the password using MD5'''
    return hashlib.md5(pw_str.encode()).hexdigest()


def get_page(page, title=""):
    '''Render the home page'''
    if 'username' in request.cookies:
        return render_template(page, title=title)
    else:
        return redirect(url_for('login'))


@app.route('/')
@app.route('/collections')
def home():
    return get_page('collections.html', "N4O-KG: Collections")


@app.route('/terminologies')
def terminologies():
    return get_page('terminologies.html', "N4O-KG: Terminologies")


@app.route('/mappings')
def mappings():
    return get_page('mappings.html', 'N4O-KG: Mappings')


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''Handle user login'''
    if request.method == 'POST':
        username = request.form['username']
        user = find_user(username)
        if user and user['password'] == pw_hash(request.form['password']):
            response = make_response(redirect(url_for('home')))
            response.set_cookie('username', username)
            return response
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/logout')
def logout():
    '''Handle user logout'''
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('username')
    return response


@app.route('/fuseki', methods=['post'])
def fuseki():
    if data := request.json.get('data'):
        res = requests.post(f'{FUSEKI_URL}/n4o?query={data}')
        return jsonify(res.text), res.status_code


@app.route('/importer/<path:subpath>', methods=["GET", "POST", "PUT", "DELETE"])
def importer(subpath):
    '''Forwards requests to the importer service'''
    res = requests.request(
        method=request.method,
        url=f'{IMPORTER_URL}/{subpath}',  # Forward to importer service
        headers={k: v for k, v in request.headers if k.lower() != 'host'},  # Exclude 'host' header
        data=request.get_data(),
        cookies=request.cookies,
        json=request.get_json(silent=True),
        allow_redirects=False,
    )

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(k, v) for k, v in res.raw.headers.items() if k.lower() not in excluded_headers]

    response = Response(res.content, res.status_code, headers)
    return response


@app.route('/postCollectionData', methods=['POST'])
def postCollectionData():
    '''Posts new collection data. Recent data will be deleted.'''
    if uri := request.json.get('uri'):
        index = urlparse(uri).path.strip('/').split('/')[-1]
        if data := request.json['data']:
            # Copy data to file, then call importer services receive and add
            suffix = request.json.get("suffix", "ttl")
            import_file = f'import_{index}.{suffix}'
            Path(f'./data').mkdir(exist_ok=True)
            Path(f'./data/{import_file}').write_text(data)
            service = f'{IMPORTER_URL}/collection/{index}'
            res = requests.post(f'{service}/receive?from={import_file}')
            res = requests.post(f'{service}/load')
            #res = requests.post(f'{service}/add')
            return res.text, res.status_code
    return jsonify(message='No data or collection index provided')


def read_yaml(fname):
    '''Read a YAML file and return the data'''
    if os.path.exists(fname):
        with open(fname, 'r') as f:
            return yaml.safe_load(f)


if __name__ == '__main__':
    parser = AP.ArgumentParser()
    parser.add_argument('-w', '--wsgi', action='store_true', help="Use WSGI server")
    parser.add_argument('-p', '--port', type=int, default=5010, help="Server port")
    parser.add_argument('-c', '--config', type=str, default="config.yaml", help="Config file")
    args = parser.parse_args()
    opts = {"port": args.port}

    user_data = read_yaml('users.yaml')
    if not user_data:
        user_data = read_yaml('admin.yaml')

    if user_data:
        users = user_data['users']
    else:
        quit(stderr='No users found in users.yaml')

    if args.wsgi:
        opts['url_scheme'] = 'https'
        serve(app, host="0.0.0.0", **opts)
    else:
        app.run(host="0.0.0.0", **opts)
