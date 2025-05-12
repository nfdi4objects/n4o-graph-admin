from flask import Flask, render_template, request
from waitress import serve
import argparse as AP
from pathlib import Path
import requests, yaml

sparql_url = 'http://172.18.0.4:3030/n4/'

app = Flask(__name__,template_folder='templates', static_folder='static', static_url_path='/assets')

def is_RDF_suffix(suffix:str):
    return suffix.lower() in ['.ttl', '.nt', '.nq', '.jsonld', '.json', '.rdf', '.xml']

def import_file(fs, collection='default'):
    files = {'file': (fs.filename, fs, 'text/plain')}
    response = requests.post(sparql_url, files=files, params={'graph': f'n4o:{collection}'})
    msg = f'answer={response.text}'
    
    return (f'Importing {fs.filename} into {collection} - Ok\n{msg}',None)

@app.route('/')
def index():
    return render_template('index.html',collection=collection_name)

collection_name ='default'

@app.route('/upload', methods=['POST'])
def upload():
    err_msg = 'Import failed'
    global collection_name
    if storage_file:=request.files['file']:
        collection_name = request.form['collection'] or 'Default'
        success_msg,err_msg = import_file(storage_file,collection_name)
    # Handle file upload here
    return render_template('index.html',success=success_msg,error=err_msg, collection=collection_name)

@app.route('/uploadC/<collection>', methods=['POST'])
def uploadC(collection):
    success_msg = 'Import failed'
    if storage_file:=request.files['file']:
        src_file = Path(storage_file.filename)
        if is_RDF_suffix(src_file.suffix):
            work_file = f'./upload{src_file.suffix}'
            storage_file.save(work_file)
            success_msg,_ = import_file(src_file,work_file,collection)
    # Handle file upload here
    return f'message:{success_msg}'

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
