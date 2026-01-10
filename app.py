import os
from flask import Flask, render_template, redirect, request, make_response, url_for, jsonify
from waitress import serve
import argparse as AP
import requests
import yaml
import hashlib
import logging
from urllib.parse import urlparse

os.makedirs('logs',exist_ok=True)
logfile = 'logs/app.log'

if os.path.exists(logfile): os.remove(logfile)
logging.basicConfig(filename=logfile, level=logging.INFO)
logger = logging.getLogger(__name__)


sparql_url = 'http://fuseki:3030/n4o'
def importer_url(coll): 
    return f'http://importer:5020/collection/{coll}'


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


def is_RDF_suffix(suffix: str):
    '''Check if the file suffix is a valid RDF format'''
    return suffix.lower() in ['.ttl', '.nt', '.nq', '.jsonld', '.json', '.rdf', '.xml']


def import_file(storage_file, collection='default'):
    '''Import a file into the RDF store'''
    if collection:
        files = {'file': (storage_file.filename, storage_file, 'text/plain')}
        response = requests.post(sparql_url, files=files, params={'graph': f'n4o:{collection}'})
        return (f'Importing {storage_file.filename} into {collection} - Ok\nanswer={response.text}', None)


@app.route('/info')
def info():
    '''Display information about the RDF store and users'''
    return f'Info: SPARQL = {sparql_url}'

@app.route('/')
def home():
    '''Render the home page'''
    if 'username' in request.cookies:
        return render_template('index.html', conn=jsonify('http://localhost:3030/n4o').json)
    else:
        return redirect(url_for('login'))


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

    if config_data := read_yaml(args.config):
        sparql_url = config_data["fuseki-server"]["uri"]

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
