import os
import sys
import json
import subprocess
from flask import Flask, send_from_directory, request, jsonify
from functools import wraps
from flask.helpers import make_response
from werkzeug.utils import secure_filename
import pymysql
#import psycopg2

ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))
VIEW_FOLDER = ROOT_FOLDER.replace("server", "menuView")
EDIT_FOLDER = ROOT_FOLDER.replace("server", "menuEdit")
UPLOAD_FOLDER = VIEW_FOLDER + "/images/"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
# MySQL
DB_HOST = "sql10.freesqldatabase.com"
DB_NAME = "sql10442463"
DB_USER = "sql10442463"
DB_PASS = "kEKm9mMnHJ"
DB_PORT = 3306
# PostgreSQL
#DB_HOST = "ec2-34-199-209-37.compute-1.amazonaws.com"
#DB_NAME = "d2sfmugthls1b3"
#DB_PORT = 5432
#DB_USER = "kyvtpucbtyfzex"
#DB_PASS = "331f97b32fc4a7891c4cedadbee316fae513b9baa6b71c858017f807824688d3"


SUCCESS = "Success"
BAD_CONNECTION = "Connection Refused"
VERIFY_LOGIN = "Verify Login"
INACTIVE_USER = "Inactive User"
INVALID_USER = "Invalid User"
INVALID_PASSWORD = "Invalid Password"
NOT_FOUND = "Not Found"
PERMISION_DENIED = "Not Permitted"

VALID_IP = sys.argv[1:]
PORT = 1111

HTML = {
    BAD_CONNECTION:
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
    VERIFY_LOGIN:
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
    INVALID_USER:
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
    INVALID_PASSWORD: """
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
    INACTIVE_USER:
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
    NOT_FOUND:
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
    PERMISION_DENIED:
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

app = Flask(__name__, static_folder=EDIT_FOLDER)


def connectMySQLDB(username, password):
    stateConnection = None
    try:
        connection = pymysql.connect(
            host=DB_HOST, db=DB_NAME, port=DB_PORT, user=DB_USER, password=DB_PASS)
        cursor = connection.cursor()
        #cursor.execute("CREATE TABLE clients (id SERIAL PRIMARY KEY, email VARCHAR, password VARCHAR, state BOOLEAN);")
        #cursor.execute("INSERT INTO clients (email,password,state) VALUES(%s,%s,%s)",(username,password,True))
        cursor.execute("SELECT * FROM clients WHERE email=%s;", (username,))
        data = cursor.fetchone()
        if data:
            if data[2] != password:
                stateConnection = INVALID_PASSWORD
            elif not data[3]:
                stateConnection = INACTIVE_USER
            else:
                stateConnection = SUCCESS
        else:
            stateConnection = INVALID_USER
        cursor.close()
        connection.close()
        return stateConnection
    except pymysql.Error as error:
        print(error)
        return BAD_CONNECTION
    except Exception as error:
        print(error)
        return BAD_CONNECTION


def verifyAccess(username, password):
    # if username == "admin" and password == "Jhoancarrero.11":
    #    return SUCCESS
    return connectMySQLDB(username, password)


def auth_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        verify = None if not auth else verifyAccess(
            auth.username, auth.password)
        print("Auth: ", auth)
        print("Verify: ", verify)
        if verify == SUCCESS:
            return f(*args, **kwargs)
        elif verify == BAD_CONNECTION:
            return make_response(HTML[BAD_CONNECTION], 500)
        elif verify == INVALID_USER:
            return make_response(HTML[INVALID_USER].replace("$user", auth.username), 401)
        elif verify == INVALID_PASSWORD:
            return make_response(HTML[INVALID_PASSWORD].replace("$user", auth.username), 401)
        elif verify == INACTIVE_USER:
            return make_response(HTML[INACTIVE_USER].replace("$user", auth.username), 403)
        else:
            return make_response(HTML[VERIFY_LOGIN], 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
    return decorated


def saveStateFile(status):
    DATA_FILE = VIEW_FOLDER+"/data.json"
    file = open(DATA_FILE, 'w')
    file.write(json.dumps(status))
    file.close()
    return jsonify({'data': "success"})


def saveImage(image):
    if image:
        filename = secure_filename(image.filename)
        image.save(UPLOAD_FOLDER+filename)
        return jsonify({'data': "success"})
    return make_response(HTML[NOT_FOUND], 404)


@app.before_request
def limit_remote_addr():
    # Las ip validas son pasadas por parametro al arrancar el servidor
    if not request.remote_addr in VALID_IP:
        return make_response(HTML[PERMISION_DENIED].replace("$ip", request.remote_addr), 403)


@app.route('/logout', methods=['GET'])
def logout():
    print("Logout: ", request.authorization)
    return make_response(HTML[VERIFY_LOGIN], 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


@app.route('/loadData', methods=["POST"])
def postData():
    if request.method == "POST":
        return saveStateFile(request.get_json())
    return make_response(HTML[NOT_FOUND], 404)


@app.route('/loadImage', methods=["POST"])
def postImage():
    if request.method == "POST":
        return saveImage(request.files['image'])
    return make_response(HTML[NOT_FOUND], 404)

# Serve React App


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
@auth_required
def serve(path):
    if "menuView" in path:
        return send_from_directory(VIEW_FOLDER.replace("menuView", ""), path)
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    elif path == "" and os.path.exists(app.static_folder+'/'+'index.html'):
        return send_from_directory(app.static_folder, 'index.html')
    else:
        return make_response(HTML[NOT_FOUND], 404)


def blockPort():
    #Para bloquear todas las solicitudes de servicio en el puerto establecido:
    try:
        RULE_SET = "iptables -A INPUT -p tcp --dport "+str(PORT)+" -j DROP"
        #RULE_SET_WLAN_0 = "iptables -A INPUT -i wlan0 -p tcp --dport "+str(PORT)+" -j DROP" 
        #RULE_SET_WLAN_1 = "iptables -A INPUT -i wlan1 -p tcp --dport "+str(PORT)+" -j DROP" 
        first_rule  =   subprocess.run(RULE_SET.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #second_rule =   subprocess.run(RULE_SET_WLAN_0.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #third_rule  =   subprocess.run(RULE_SET_WLAN_1.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)        
        if first_rule.stdout:
            print(first_rule.stdout)
            return True
        elif first_rule.stderr:
            print(first_rule.stderr)
            return False
    except Exception as error:
        print(error)
        return False


def allowIpToPort(IP):
    #Para permitir solo las solicitudes del servicio a la ip permitida:
    try:
        RULE_SET = "iptables -A INPUT -s "+IP+" -p tcp --dport "+str(PORT)+" -j ACCEPT"
        #RULE_SET_WLAN_0 = "iptables -A INPUT -i wlan0 -p tcp --dport "+str(PORT)+" -j DROP" 
        #RULE_SET_WLAN_1 = "iptables -A INPUT -i wlan1 -p tcp --dport "+str(PORT)+" -j DROP" 
        first_rule  =   subprocess.run(RULE_SET.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #second_rule =   subprocess.run(RULE_SET_WLAN_0.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #third_rule  =   subprocess.run(RULE_SET_WLAN_1.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)        
        if first_rule.stdout:
            print(first_rule.stdout)
            return True
        elif first_rule.stderr:
            print(first_rule.stderr)
            return False
    except Exception as error:
        print(error)
        return False


if __name__ == '__main__':
    #from waitress import serve
    #if os.geteuid() != 0:
    #    print('Debes tener privilegios root para este script.')
    #    sys.exit(1)
    #else:
        if blockPort():
            error = False
            
            for IP in VALID_IP:
                if not error:
                    error = allowIpToPort(IP)
            
            if not error:
                app.run(host="0.0.0.0", port=PORT, debug=True)
