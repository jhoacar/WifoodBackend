import os
import sys
import json
import subprocess
from flask import Flask, send_from_directory, request, jsonify
from functools import wraps
from flask.helpers import make_response
from werkzeug.utils import secure_filename
import pymysql

from server import VIEW_FOLDER

CONFIG = {
    "PORT":80,
    "IP": "192.168.1.1",
    "IFACE":  "br-lan",
    "STATUS_SERVER":"/mnt/status.txt",
    "ROOT_FOLDER":"",
    "VIEW_FOLDER":"/mnt/view_menu",
    "EDIT_FOLDER":"/mnt/edit_menu/",
    "DATA_FOLDER":"/mnt/data",
    "TEMPLATE_FOLDER":"/mnt/templates",
    "IMAGE_FOLDER":"/mnt/data/images/menu",
    "ALLOWED_EXTENSIONS":['png', 'jpg', 'jpeg', 'gif'],
    "STATE_SUCCESS":"Conexion Exitosa",
    "STATE_BAD":"Mala Coneccion",
    "STATE_VERIFY":"Se necesita verificacion",
    "STATE_INACTIVE":"Se encuentra inactivo",
    "STATE_INVALID_USER":"Usuario Invalido",
    "STATE_INVALID_PASS":"Contrasena Invalida",
    "STATE_PERMISSION_DENIED":"Permiso denegado",
    "STATE_NOT_FOUND":"No se encuentra",
    "VALID_IP":sys.argv[1:],
    "DB_HOST":"sql10.freesqldatabase.com",
    "DB_NAME":"sql10442463",
    "DB_USER":"sql10442463",
    "DB_PASS":"kEKm9mMnHJ",
    "DB_PORT":3306,
}

# PostgreSQL
#DB_HOST = "ec2-34-199-209-37.compute-1.amazonaws.com"
#DB_NAME = "d2sfmugthls1b3"
#DB_PORT = 5432
#DB_USER = "kyvtpucbtyfzex"
#DB_PASS = "331f97b32fc4a7891c4cedadbee316fae513b9baa6b71c858017f807824688d3"


""""
CONEXION A LA BASE DE DATOS
    ESTRUCTURA DE LA TABLE:
        CREATE TABLE clients id AUTOINCREMENT PRIMARY KEY, email VARCHAR, password VARCHAR, state BOOLEAN
"""
def connectMySQLDB(username):
    try:
        connectParams = {
            "host"  :   CONFIG["DB_HOST"],
            "db":       CONFIG["DB_NAME"],
            "port":     CONFIG["DB_PORT"],
            "user":     CONFIG["DB_USER"],
            "password": CONFIG["DB_PASS"]
        }
        logInfo("\nConectando a MySQL")
        connection = pymysql.connect(**connectParams)
        cursor = connection.cursor()
        logInfo("\nConexion exitosa")
        cursor.execute("SELECT * FROM clients WHERE email=%s;", (username,))
        data = cursor.fetchone()
        cursor.close()
        connection.close()
        return data

    except Exception as error:
        logInfo("\nPython: "+str(error))
        return CONFIG["STATE_BAD"]

""""
MIDDLEWARE
    ESTRUCTURA DEL MIDDLEWARE:
        Busca en la base de datos si se encuentra disponible el servicio
"""
def auth_required(function):

    def verifyAccess(username,password):
        data = connectMySQLDB(username)

        if data:
            if data[2] != password:
                return CONFIG["STATE_INVALID_PASS"]

            elif not data[3]:
                return CONFIG["STATE_INACTIVE"]

            elif data[2]==password and data[3]:

                return CONFIG["STATE_SUCCESS"]

            else:
                return CONFIG["STATE_BAD"]
        else:
            return CONFIG["STATE_INVALID_USER"]


    @wraps(function)
    def decorated(*args, **kwargs):

        if not request.remote_addr in CONFIG["VALID_IP"] or request.full_path[:-1]=="/logout":
            return function(*args, **kwargs)

        auth = request.authorization
        logInfo("\nCliente a Autorizar: "+str(auth))
        verify = None if not auth else verifyAccess(auth.username, auth.password)
        logInfo("\nVerificacion: "+str(verify))
        if verify == CONFIG["STATE_SUCCESS"]:
            return function(*args, **kwargs)
        elif verify == CONFIG["STATE_BAD"]:
            return send_from_directory(CONFIG["TEMPLATE_FOLDER"],"bad_connection.html"), 500
        elif verify == CONFIG["STATE_INVALID_USER"]:
            return send_from_directory(CONFIG["TEMPLATE_FOLDER"],"invalid_user.html"), 403
        elif verify == CONFIG["STATE_INVALID_PASS"]:
            return send_from_directory(CONFIG["TEMPLATE_FOLDER"],"invalid_pass.html"), 403
        elif verify == CONFIG["STATE_INACTIVE"]:
            return send_from_directory(CONFIG["TEMPLATE_FOLDER"],"inactive.html"), 403
        else:
            return send_from_directory(CONFIG["TEMPLATE_FOLDER"],"verify.html"), 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}
    return decorated

#REDIRIGIR EL TRAFICO HTTPS
#iptables -t nat -A PREROUTING -i IFACE -p tcp --dport 443 -j DNAT --to-destination IP:PORT

FIREWALL = """iptables -A FORWARD -i IFACE -p tcp --dport 53 -j ACCEPT
iptables -A FORWARD -i IFACE -p udp --dport 53 -j ACCEPT
iptables -A FORWARD -i IFACE -p tcp --dport 443 -j ACCEPT
iptables -A FORWARD -i IFACE -p udp --dport 443 -j DROP
iptables -A FORWARD -i IFACE -p tcp --dport PORT -d IP -j ACCEPT
iptables -A FORWARD -i IFACE -j DROP
iptables -t nat -A PREROUTING -i IFACE -p tcp --dport 80 -j DNAT --to-destination IP:PORT"""

def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(str(i),str(j))
    return text

def logInfo(text,first=False):
    mode = "w" if first else "a" #Agrega al final o lo crea de inicio
    file = open(CONFIG["STATUS_SERVER"],mode)
    file.write(str(text))
    file.close()

def executeCommand(command):
    try:
        logInfo("\nEjecutando: "+command)
        process = subprocess.run(command.split(" "),stdin=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        logInfo("\nSalida: "+str(process.stdout))
        logInfo("\nError: "+str(process.stderr))
    except Exception as error:
        logInfo("\nPython: "+str(error))


def redirectTraffic():
    logInfo("\nEjecutado el FIREWALL: ")
    for RULE in FIREWALL.split("\n"):
        executeCommand(replace_all(RULE,CONFIG))

def saveStateFile(status):
    DATA_FILE = CONFIG["DATA_FOLDER"]+"/data.json"
    file = open(DATA_FILE, 'w')
    file.write(json.dumps(status))
    file.close()
    return jsonify({'data': 'Se ha cambiado la informacion del JSON'})


def saveImage(image):
    if image:
        filename = secure_filename(image.filename)
        image.save(CONFIG["IMAGE_FOLDER"]+filename)
        return jsonify({'data': "success"}),200
    return send_from_directory(CONFIG["TEMPLATE_FOLDER"],'404.html'), 404

app = Flask(__name__,static_folder=CONFIG["EDIT_FOLDER"])

"""
    RUTAS
"""
@app.errorhandler(404)
def page_not_found(error):
    if request.host=="www.wifood.net":
        return send_from_directory(CONFIG["TEMPLATE_FOLDER"],'404.html'), 404
    else:
        request.host=="www.wifood.net"
        if request.remote_addr in CONFIG["VALID_IP"]:
            return send_from_directory(CONFIG["EDIT_FOLDER"],'index.html')
        else:
            return send_from_directory(CONFIG["VIEW_FOLDER"],'index.html')
        


@app.errorhandler(500)
def server_error(e):
    logInfo("\nError 500: "+str(request))
    return send_from_directory(CONFIG["TEMPLATE_FOLDER"],'500.html'), 500

@app.route('/logout', methods=['GET'])
def logout():
    logInfo("\nSe desautoriza: "+str(request.authorization))
    return send_from_directory(CONFIG["TEMPLATE_FOLDER"],'verify.html'), 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}


@app.route('/data', methods=["GET","POST"])
@auth_required
def postData():
    if request.method == "POST":
        return saveStateFile(request.get_json())
    elif request.method == "GET":
        return send_from_directory(CONFIG["DATA_FOLDER"],"data.json"),200
    return send_from_directory(CONFIG["TEMPLATE_FOLDER"],'404.html'), 404


@app.route('/images/<string:src>', methods=["GET","POST"])
@auth_required
def serveImage(src):
    if request.method == "POST":
        return saveImage(request.files['image'])
    if request.method == "GET":
        return send_from_directory(CONFIG["IMAGE_FOLDER"],src)
    return send_from_directory(CONFIG["TEMPLATE_FOLDER"],'404.html'), 404

@app.route('/<path:path>')
@auth_required
def send_edit(path):
     if not "/data" in path:
        return send_from_directory(CONFIG["EDIT_FOLDER"],path)


def send_view(folder,fileName):
    if "images" in folder:
        return send_from_directory(CONFIG["IMAGE_FOLDER"],fileName)
    return send_from_directory(CONFIG["VIEW_FOLDER"]+folder,fileName)


@app.route('/', methods=["GET","POST"])
def getIndex():
    if request.remote_addr in CONFIG["VALID_IP"]:
        return send_from_directory(CONFIG["EDIT_FOLDER"],'index.html')
    else:
        return send_from_directory(CONFIG["VIEW_FOLDER"],'index.html')



@app.before_request
@auth_required
def serve():
    ip = request.remote_addr
    path = request.full_path[:-1]
    fileName = path.split("/")[-1:][0]
    folder = "/".join(path.split("/")[:-1])

    if not ip in CONFIG["VALID_IP"]:
        if fileName and fileName!="data":
            return send_view(folder,fileName)
        elif fileName == "data":
            return send_from_directory(CONFIG["DATA_FOLDER"],"data.json")


if __name__ == "__main__":
    #from waitress import serve
    if os.geteuid() != 0:
        logInfo('\n--Debes tener privilegios root para este script--',first=True)
        sys.exit(1)
    else:
        logInfo("\n---Iniciando el SERVIDOR--",first=True)
        logInfo("\nConfigurando el Firewall")
        redirectTraffic()
        app.run(host="0.0.0.0", port=CONFIG["PORT"])


