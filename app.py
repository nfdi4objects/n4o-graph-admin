from flask import Flask, render_template, request
from waitress import serve
import argparse as AP
from pathlib import Path

app = Flask(__name__,template_folder='templates', static_folder='static', static_url_path='/assets')

def import_file(src_file:str, work_file:str):
    # Simulate file import
    print(f"Importing {src_file}")
    return (f'Importing {src_file} ok',None)

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
