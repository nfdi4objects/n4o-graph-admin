from flask import Flask, render_template, redirect, request, make_response, url_for
from waitress import serve
import argparse as AP
from pathlib import Path
import requests, yaml

sparql_url = 'http://172.18.0.4:3030/n4/'

app = Flask(__name__,template_folder='templates', static_folder='static', static_url_path='/assets')
app.secret_key = 'your_secret_key'  # Replace with a strong secret key
user_collection_name ={'admin':'default','user1':'default_1','guest':'default_2'}
users = {'admin': 'admin123', 'user1': 'user1', 'guest': 'guest1'}


def is_RDF_suffix(suffix:str):
    return suffix.lower() in ['.ttl', '.nt', '.nq', '.jsonld', '.json', '.rdf', '.xml']

def import_file(storage_file, collection='default'):
    if collection:
        files = {'file': (storage_file.filename, storage_file, 'text/plain')}
        response = requests.post(sparql_url, files=files, params={'graph': f'n4o:{collection}'})
        return (f'Importing {storage_file.filename} into {collection} - Ok\nanswer={response.text}',None)

@app.route('/info')
def info():
    return f'Info: {sparql_url} names = {user_collection_name} user= {[k for k,_ in user_collection_name.items()]}' 

@app.route('/upload', methods=['POST'])
def upload():
    global user_collection_name
    err_msg = 'Import failed'
    success_msg = coll = None
    if storage_file:=request.files.get('file'):
        if username := request.cookies.get('username','www'):
            coll = request.form['collection'] or 'Default'
            user_collection_name[username] = coll
            success_msg,err_msg = import_file(storage_file,coll)
    return render_template('index.html',success=success_msg,error=err_msg, collection=coll)

@app.route('/uploadC/<collection>', methods=['POST'])
def uploadC(collection):
    success_msg = 'Import failed'
    if storage_file:=request.files['file']:
        success_msg,_ = import_file(storage_file,collection)
    return f'message:{success_msg}'

@app.route('/')
def home():
    global user_collection_name
    if 'username' in request.cookies:
        username = request.cookies.get('username')
        if username not in user_collection_name:
            user_collection_name[username]='default'   
        return render_template('index.html',collection=user_collection_name.get(username))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            response = make_response(redirect(url_for('home')))
            response.set_cookie('username', username)
            return response
        else:
            return 'Invalid username or password'
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('username')
    return response

if __name__ == '__main__':
    parser = AP.ArgumentParser()
    parser.add_argument('-w', '--wsgi', action=AP.BooleanOptionalAction, help="Use WSGI server")
    parser.add_argument('-p', '--port', type=int, default=5010, help="Server port")
    parser.add_argument('-c', '--config', type=str, default="config.yaml", help="Config file")
    args = parser.parse_args()
    opts = {"port": args.port}

    try:
        with open(args.config) as stream:
            data = yaml.safe_load(stream)
            sparql_url = data["fuseki-server"]["uri"]
    except yaml.YAMLError as err:
        quit(str(err))


    if args.wsgi:
        serve(app, host="0.0.0.0", **opts)
    else:
        app.run(host="0.0.0.0", **opts)
