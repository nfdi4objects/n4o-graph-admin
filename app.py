from flask import Flask, render_template, redirect, request, make_response, url_for
from waitress import serve
import argparse as AP
import requests
import yaml
import hashlib

sparql_url = 'http://172.18.0.4:3030/n4/'

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
    return f'Info: {sparql_url} user= {[k['username'] for k,_ in users]}'


@app.route('/upload', methods=['POST'])
def upload():
    '''Handle file upload and import into the RDF store'''
    err_msg = 'Import failed'
    success_msg = coll = None
    if storage_file := request.files.get('file'):
        if username := request.cookies.get('username', 'www'):
            coll = request.form['collection'] or 'Default'
            if user := find_user(username):
                user['collection'] = coll
            success_msg, err_msg = import_file(storage_file, coll)
    return render_template('index.html', success=success_msg, error=err_msg, collection=coll)


@app.route('/uploadC/<collection>', methods=['POST'])
def uploadC(collection):
    '''Handle file upload and import REST API'''
    success_msg = 'Import failed'
    if storage_file := request.files['file']:
        success_msg, _ = import_file(storage_file, collection)
    return f'message:{success_msg}'


@app.route('/')
def home():
    '''Render the home page'''
    if 'username' in request.cookies:
        username = request.cookies.get('username')
        coll = 'default'
        if user := find_user(username):
            coll = user['collection'] or 'default'
        return render_template('index.html', collection=coll)
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
            return 'Invalid username or password'
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
    with open(fname, 'r') as f:
        config = yaml.safe_load(f)
        return config


if __name__ == '__main__':
    parser = AP.ArgumentParser()
    parser.add_argument('-w', '--wsgi', action=AP.BooleanOptionalAction, help="Use WSGI server")
    parser.add_argument('-p', '--port', type=int, default=5010, help="Server port")
    parser.add_argument('-c', '--config', type=str, default="config.yaml", help="Config file")
    args = parser.parse_args()
    opts = {"port": args.port}

    try:
        config_data = read_yaml(args.config)
        sparql_url = config_data["fuseki-server"]["uri"]
        user_data = read_yaml('users.yaml')
        users = user_data['users']
    except yaml.YAMLError as err:
        quit(str(err))

    if args.wsgi:
        serve(app, host="0.0.0.0", **opts)
    else:
        app.run(host="0.0.0.0", **opts)
