from flask import Flask, render_template, request
from waitress import serve
import argparse as AP
from pathlib import Path

app = Flask(__name__)

def import_file(filename:Flask):
    # Simulate file import
    print(f"Importing {filename}")
    return (f'Import ok',None)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    err_msg = 'Import failed'
    if storage_file:=request.files['file']:
        workFile = f'./upload{Path(storage_file.filename).suffix}'
        storage_file.save(workFile)
        success_msg,err_msg = import_file(workFile)
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
