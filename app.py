from flask import Flask, render_template, request
from waitress import serve
import argparse as AP
from pathlib import Path

app = Flask(__name__,template_folder='templates', static_folder='static', static_url_path='/assets')

def import_file(src_file:str, work_file:str, collection='unspecified'):
    # Simulate file import
    return (f'Importing {src_file} into {collection} - Ok',None)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    err_msg = 'Import failed'
    if storage_file:=request.files['file']:
        src_file = storage_file.filename
        work_file = f'./upload{Path(src_file).suffix}'
        storage_file.save(work_file)
        success_msg,err_msg = import_file(src_file,work_file)
    # Handle file upload here
    return render_template('index.html',success=success_msg,error=err_msg)

@app.route('/uploadC/<collection>', methods=['POST'])
def uploadC(collection):
    success_msg = 'Import failed'
    if storage_file:=request.files['file']:
        src_file = storage_file.filename
        work_file = f'./upload{Path(src_file).suffix}'
        storage_file.save(work_file)
        success_msg,_ = import_file(src_file,work_file,collection)
    # Handle file upload here
    return f'message:{success_msg}'

if __name__ == '__main__':
    parser = AP.ArgumentParser()
    parser.add_argument('-w', '--wsgi', action=AP.BooleanOptionalAction, help="Use WSGI server")
    parser.add_argument('-p', '--port', type=int, default=5010, help="Server port")
    args = parser.parse_args()
    opts = {"port": args.port}

    if args.wsgi:
        serve(app, host="0.0.0.0", **opts)
    else:
        app.run(host="0.0.0.0", **opts)
