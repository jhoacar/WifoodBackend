import os
import sys
import json
import subprocess
from flask import Flask, send_from_directory, request, jsonify
from functools import wraps
from flask.helpers import make_response
from werkzeug.utils import secure_filename
import pymysql

CONFIG = {
    "PORT":80,
    "IP": "192.168.1.1",
    "IFACE":  "br-lan",
    "STATUS_SERVER":"./status.txt",
    "ROOT_FOLDER":"",
    "VIEW_FOLDER":"C:/Users/jhoan/OneDrive/Escritorio/Proyecto_Wifi/frontend/build",
    "EDIT_FOLDER":"C:/Users/jhoan/OneDrive/Escritorio/Proyecto_Wifi/frontend/build",
    "UPLOAD_FOLDER":"",
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

HTML = {
    CONFIG["STATE_BAD"]:
        """
    <html>
        <head>
            <title>Sin Conexion</title>
        </head>
        <body>
            <h1>No hay Conexion a Internet</h1>
            <p>Recargue la Página o revise si su router se encuentra conectado a el</p>
        </body>
    </html>
    """,
    CONFIG["STATE_VERIFY"]:
        """
    <html>
        <head>
            <title>Iniciar Sesion</title>
        </head>
        <body>
            <h1>No ha iniciado sesion</h1>
            <p>Verifique su usuario y contraseña (Recargue la pagina)</p>
        </body>
    </html>
    """,
    CONFIG["STATE_INVALID_USER"]:
        """
    <html>
        <head>
            <title>Usuario Invalido</title>
        </head>
        <body>
            <h1>No hay registro del usuario $user</h1>
            <p>Ingrese sus credenciales otra vez</p>
            <script>
                const redirect = ()=>{
                    const request = new XMLHttpRequest();                                        
                    request.open("GET", "/logout", false, "false", "false");                                                                                                                               
                    request.send();
                    window.location="/";
                }
                setTimeout(redirect,3000) 
            </script>
        </body>
    </html>
    """,
    CONFIG["STATE_INVALID_PASS"]: """
    <html>
        <head>
            <title>Contraseña Incorrecta</title>
        </head>
        <body>
            <h1>No coincide la contraseña para $user</h1>
            <p>Ingrese sus credenciales otra vez</p>
            <script>
                const redirect = ()=>{
                    const request = new XMLHttpRequest();                                        
                    request.open("GET", "/logout", false, "false", "false");                                                                                                                               
                    request.send();
                    window.location="/";
                }
                setTimeout(redirect,3000) 
            </script>
        </body>
    </html>
    """,
    CONFIG["STATE_INACTIVE"]:
        """
    <html>
        <head>
            <title>Usuario Inactivo</title>
        </head>
        <body>
            <h1>No hay servicio para el usuario $user</h1>
            <p>Verifique con su proveedor sobre su inactividad en el servicio</p>
        </body>
    </html>
    """,
    CONFIG["STATE_NOT_FOUND"]:
        """
    <html>
        <head>
            <title>Pagina No Encontrada</title>
        </head>
        <body>
            <h1>No se encuentra lo que solicito</h1>
            <p>Verifique la ruta que desea acceder</p>
        </body>
    </html>
        """,
    CONFIG["STATE_PERMISSION_DENIED"]:
        """
    <html>
        <head>
            <title>Pagina No Disponible</title>
        </head>
        <body>
            <h1>No tiene permisos</h1>
            <p>Verifique que su IP ( $ip ) tenga acceso al servidor</p>
        </body>
    </html>
        """

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
def connectMySQLDB(username, password):
    stateConnection = None
    try:
        connectParams = {
            "host"  :   CONFIG["DB_HOST"],
            "db":       CONFIG["DB_NAME"],
            "port":     CONFIG["DB_PORT"],
            "user":     CONFIG["DB_USER"],
            "password": CONFIG["DB_PASS"]
        }
        saveAtFile("\nConectando a MySQL")
        connection = pymysql.connect(**connectParams)
        cursor = connection.cursor()
        saveAtFile("\nConexion exitosa")
        cursor.execute("SELECT * FROM clients WHERE email=%s;", (username,))
        data = cursor.fetchone()
        if data:
            if data[2] != password:
                stateConnection = CONFIG["STATE_INVALID_PASS"]
            elif not data[3]:
                stateConnection = CONFIG["STATE_INACTIVE"]
            else:
                stateConnection = CONFIG["STATE_SUCCESS"]
        else:
            stateConnection = CONFIG["STATE_INVALID_USER"]
        cursor.close()
        connection.close()
        return stateConnection
    
    except Exception as error:
        saveAtFile("\nPython: "+str(error))
        return CONFIG["STATE_BAD"]

""""
MIDDLEWARE
    ESTRUCTURA DEL MIDDLEWARE:
        Busca en la base de datos si se encuentra disponible el servicio
"""
def auth_required(function):

    def verifyAccess(username,password):
        return connectMySQLDB(username,password)
        
    @wraps(function)
    def decorated(*args, **kwargs):
        
        if not request.remote_addr in CONFIG["VALID_IP"]:
            return function(*args, **kwargs)
            
        auth = request.authorization
        saveAtFile("\nCliente a Autorizar: "+str(auth))
        verify = None if not auth else verifyAccess(auth.username, auth.password)
        saveAtFile("\nVerificacion: "+str(verify))
        if verify == CONFIG["STATE_SUCCESS"]:
            return function(*args, **kwargs)
        elif verify == CONFIG["STATE_BAD"]:
            pass
            return make_response(HTML[CONFIG["STATE_BAD"]], 500)
        elif verify == CONFIG["STATE_INVALID_USER"]:
            return make_response(HTML[CONFIG["STATE_INVALID_USER"]].replace("$user", auth.username), 401)
        elif verify == CONFIG["STATE_INVALID_PASS"]:
            return make_response(HTML[CONFIG["STATE_INVALID_PASS"]].replace("$user", auth.username), 401)
        elif verify == CONFIG["STATE_INACTIVE"]:
            return make_response(HTML[CONFIG["STATE_INACTIVE"]].replace("$user", auth.username), 403)
        else:
            return make_response(HTML[CONFIG["STATE_INACTIVE"]], 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
    return decorated


FIREWALL = """iptables -A FORWARD -i IFACE -j DROP
iptables -A FORWARD -i IFACE -p tcp --dport 53 -j ACCEPT
iptables -A FORWARD -i IFACE -p udp --dport 53 -j ACCEPT
iptables -A FORWARD -i IFACE -p tcp --dport PORT -d IP -j ACCEPT
iptables -t nat -A PREROUTING -i IFACE -p tcp --dport 443 -j DNAT --to-destination IP:PORT
iptables -t nat -A PREROUTING -i IFACE -p tcp --dport PORT -j DNAT --to-destination IP:PORT"""

def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(str(i),str(j))
    return text

def saveAtFile(text,first=False):
    mode = "w" if first else "a" #Agrega al final o lo crea de inicio
    file = open(CONFIG["STATUS_SERVER"],mode)
    file.write(str(text))
    file.close()

def executeCommand(command):
    try:
        saveAtFile("\nEjecutando: "+command)
        process = subprocess.run(command.split(" "),stdin=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        saveAtFile("Salida: "+str(process.stdout))
        saveAtFile("Error: "+str(process.stderr))
    except Exception as error:
        saveAtFile("\nPython: "+str(error))  


def redirectTraffic():
    saveAtFile("\nEjecutado el FIREWALL: ")
    for RULE in FIREWALL.split("\n"):
        executeCommand(replace_all(RULE,CONFIG))

def saveStateFile(status):
    DATA_FILE = CONFIG["ROOT_FOLDER"]+"/data.json"
    file = open(DATA_FILE, 'w')
    file.write(json.dumps(status))
    file.close()
    return jsonify({'data': 'Se ha cambiado la informacion del JSON'})


def saveImage(image):
    if image:
        filename = secure_filename(image.filename)
        image.save(CONFIG["UPLOAD_FOLDER"]+filename)
        return jsonify({'data': "success"})
    return False


app = Flask(__name__)

"""
    RUTAS
"""
#@app.before_request
#def limit_remote_addr():
#    print(request)    
#    if request.remote_addr in CONFIG["VALID_IP"]:
#        #return jsonify({'ip': request.remote_addr}), 200
#        return send_from_directory(CONFIG["VIEW_FOLDER"],"index.html")
#    else:
#        return jsonify({'ip': request.remote_addr}), 401
#return send_from_directory(CONFIG["EDIT_FOLDER"]+"/index.html")

@app.route('/logout', methods=['GET'])
def logout():
    saveAtFile("\nSe desautoriza: "+str(request.authorization))
    return make_response(HTML[CONFIG["STATE_VERIFY"]], 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


@app.route('/data', methods=["POST"])
def postData():
    if request.method == "POST":
        return saveStateFile(request.get_json())
    return make_response(HTML[CONFIG["STATE_NOT_FOUND"]], 404)


@app.route('/images', methods=["POST"])
def postImage():
    if request.method == "POST":
        return saveImage(request.files['image'])
    return make_response(HTML[CONFIG["STATE_NOT_FOUND"]], 404)


def send_edit(path):
    saveAtFile("\n-----------------EDITANDO--------------\n")
    
    fileName = path.split("/")[-1:][0]
    folder = "/".join(path.split("/")[:-1])
    
    
    if path != "" and os.path.exists(CONFIG["EDIT_FOLDER"] + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(CONFIG["VIEW_FOLDER"],'index.html')
    
def send_view(path):
    
    fileName = path.split("/")[-1:][0]
    folder = "/".join(path.split("/")[:-1])
    
    if path != "" and path!="/" and os.path.exists(CONFIG["VIEW_FOLDER"] + '/' + path):
        return send_from_directory(CONFIG["VIEW_FOLDER"]+folder,fileName)
    else:
        return send_from_directory(CONFIG["VIEW_FOLDER"],'index.html')
    #else:
    #    return HTML[CONFIG["STATE_NOT_FOUND"]], 404
        
@app.before_request
@auth_required
def serve():
    
    path = request.full_path[:-1]
    
    if request.remote_addr in CONFIG["VALID_IP"]:
    
        return send_edit(path)
    
    else:
        
        return send_view(path)

if __name__ == "__main__":
    #from waitress import serve
    #if os.geteuid() != 0:
    #    saveAtFile('\n--Debes tener privilegios root para este script.--',first=True)
    #    sys.exit(1)
    #else:
        saveAtFile("\n---Iniciando el SERVIDOR--",first=True)
    #    redirectTraffic()
        app.run(host="0.0.0.0", port=CONFIG["PORT"], debug=True)




