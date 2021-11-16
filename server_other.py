import os
import json
from flask import Flask, send_from_directory, abort, request, jsonify
from functools import wraps
from flask.helpers import make_response
from werkzeug.utils import secure_filename
import psycopg2

ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))
VIEW_FOLDER = ROOT_FOLDER.replace("server","menuView")
EDIT_FOLDER = ROOT_FOLDER.replace("server","menuEdit")
UPLOAD_FOLDER =VIEW_FOLDER +  "/images/"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
DB_HOST = "ec2-34-199-209-37.compute-1.amazonaws.com"
DB_NAME = "d2sfmugthls1b3"
DB_PORT = 5432
DB_USER = "kyvtpucbtyfzex"
DB_PASS = "331f97b32fc4a7891c4cedadbee316fae513b9baa6b71c858017f807824688d3"


SUCCESS = 1
CONNECTION_REFUSED = -1
INVALID_USER = -2

HOST = '0.0.0.0'
PORT = 1111
VALID_IP = ['127.0.0.1','192.168.1.207','192.168.1.163']

app = Flask(__name__,static_folder=EDIT_FOLDER)

def connectPgDB(username, password):
    stateConnection = None
    try:
        print("intentando la conexion a la base de datos")
        connection = psycopg2.connect(host=DB_HOST,dbname=DB_NAME,port=DB_PORT, user=DB_USER, password=DB_PASS, sslmode='require')
        print("Conexion establecida")
        cursor = connection.cursor()
        print("Conexion establecida")
        #cursor.execute("CREATE TABLE clients (id SERIAL PRIMARY KEY, email VARCHAR, password VARCHAR, state BOOLEAN);")
        #cursor.execute("INSERT INTO clients (email,password,state) VALUES(%s,%s,%s)",(username,password,True))
        #cursor.execute("SELECT * FROM CLIENTS")
        #print(cursor.fetchall())
        cursor.execute("SELECT * FROM clients WHERE email=%s;",(username,))
        data = cursor.fetchone()
        if data and data[2] == password and data[3]:
            stateConnection = SUCCESS
        else:
            stateConnection = INVALID_USER
        cursor.execute("SELECT * FROM CLIENTS") 
        print(cursor.fetchall())
        #return stateConnection
    except psycopg2.Error as error: 
        print(error)
        print(error.pgerror)
        print(error.pgcode)
    except psycopg2.Warning as error:
        print(error)
    finally:
        #stateConnection = CONNECTION_REFUSED
        return stateConnection

def verifyAccess(username, password):
    if username=="admin" and password == "Jhoancarrero.11":
        return SUCCESS
    return connectPgDB(username,password)  

def auth_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        auth = request.authorization
        verify = None if not auth else verifyAccess(auth.username,auth.password)
        if verify==SUCCESS:
            return f(*args, **kwargs)
        elif verify==CONNECTION_REFUSED:
            pageNoInternet = "<html><head><title>Sin Conexion</title></head><body><h1>No hay Conexion a Internet</h1><p>Recargue la Página o revise si su router se encuentra conectado a el</p></body></html>"
            return pageNoInternet
        elif verify==INVALID_USER:
            return make_response("")
        else:
            return make_response("Could not verify your login", 401, {'WWW-Authenticate':'Basic realm="Login Required"'})
    return decorated

def saveStateFile(status):
    DATA_FILE = VIEW_FOLDER+"/data.json" 
    file = open(DATA_FILE,'w')
    file.write(json.dumps(status))
    file.close()
    return jsonify({'data': "success"})


def saveImage(image):
    if image:
        filename = secure_filename(image.filename)
        image.save(UPLOAD_FOLDER+filename)
        return jsonify({'data': "success"})
    abort(404)


@app.before_request
def limit_remote_addr():
    if not request.remote_addr in VALID_IP:
        abort(403)  # Forbidden


@app.route('/loadData', methods=["POST"])
def postData():
    if request.method == "POST":
        return saveStateFile(request.get_json())
    abort(404)


@app.route('/loadImage', methods=["POST"])
def postImage():
    if request.method == "POST":
        return saveImage(request.files['image'])
    abort(404)

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
@auth_required
def serve(path):
    #app.static_folder = EDIT_FOLDER
    if "menuView" in path:
        #app.static_folder = VIEW_FOLDER
        #print(app.static_folder.replace("menuEdit","")+'/'+'data.json')
        return send_from_directory(VIEW_FOLDER.replace("menuView",""),path)
    print(app.static_folder+'/'+path)
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    #elif path=="":
    #    return send_from_directory(app.static_folder,'index.html')
    else:   
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    #from waitress import serve
    app.run(host=HOST,port=PORT, debug=True)
