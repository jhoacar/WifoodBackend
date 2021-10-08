# 192.168.1.202 - - [07/Oct/2021 16:22:25] "GET /generate_204 HTTP/1.1" 404 -
# 192.168.1.202 - - [07/Oct/2021 16:22:26] "GET /generate_204 HTTP/1.1" 404 -
# 192.168.1.202 - - [07/Oct/2021 16:22:26] "GET /gen_204 HTTP/1.1" 404 -
# 192.168.1.202 - - [07/Oct/2021 16:22:35] "GET /generate_204 HTTP/1.1" 404 -
# 192.168.1.202 - - [07/Oct/2021 16:22:35] "GET /generate_204 HTTP/1.1" 404 -
# 192.168.1.202 - - [07/Oct/2021 16:22:51] "GET /generate_204 HTTP/1.1" 404 -
# 192.168.1.202 - - [07/Oct/2021 16:22:51] "GET /gen_204 HTTP/1.1" 404 -
# 192.168.1.202 - - [07/Oct/2021 16:23:23] "GET /generate_204 HTTP/1.1" 404 -
# 192.168.1.202 - - [07/Oct/2021 16:23:23] "GET /generate_204 HTTP/1.1" 404 -
# 192.168.1.202 - - [07/Oct/2021 16:24:27] "GET /generate_204 HTTP/1.1" 404 -
# 192.168.1.202 - - [07/Oct/2021 16:24:27] "GET /gen_204 HTTP/1.1" 404 -

#import subprocess
from flask import Flask 
from flask.helpers import make_response

# These variables are used as settings
PORT       = 80         # the port in which the captive portal web server listens 
IFACE      = "br-lan"      # the interface that captive portal protects
IP_ADDRESS = "192.168.1.1" # the ip address of the captive portal (it can be the IP of IFACE) 

'''
This it the http server used by the the captive portal
'''
#the login page
html_login = """
<html>
<body>
    <b>Login Form</b>
    <form method="POST" action="do_login">
    Username: <input type="text" name="username"><br>
    Password: <input type="password" name="password"><br>
    <input type="submit" value="Submit">
    </form>
</body>
</html>
"""

'''
if the user requests the login page show it, else
use the redirect page
'''
'''
this is called when the user submits the login form
'''

# print "*********************************************"
# print "* Note, if there are already iptables rules *"
# print "* this script may not work. Flush iptables  *"
# print "* at your own risk using iptables -F        *"
# print "*********************************************"
#print("...Erasing All IPTABLES")
#subprocess.run("iptables -F".split(" "))
#subprocess.run("iptables -t nat -F".split(" "))
#print("Updating iptables")
#print("... Connect any device to Internet and it will send request by DHCP to a specific URL to have a Network Connectivity Status Indicator")
#print("... Accepting URL and resolving with 8.8.8.8 (google) DNS")
#subprocess.run("iptables -t nat -A PREROUTING -d 8.8.8.8/32 -j ACCEPT".split(" "))
#print (".. Allow TCP DNS")
#subprocess.run(["iptables", "-A", "FORWARD", "-i", IFACE, "-p", "tcp", "--dport", "53", "-j" ,"ACCEPT"])
#print (".. Allow UDP DNS")
#subprocess.run(["iptables", "-A", "FORWARD", "-i", IFACE, "-p", "udp", "--dport", "53", "-j" ,"ACCEPT"])
#print (".. Allow traffic to captive portal")
#subprocess.run(["iptables", "-A", "FORWARD", "-i", IFACE, "-p", "tcp", "--dport", str(PORT),"-d", IP_ADDRESS, "-j" ,"ACCEPT"])
#print (".. Block all other traffic")
#subprocess.run(["iptables", "-A", "FORWARD", "-i", IFACE, "-j" ,"DROP"])

#print("...Rdirect All Trafic of Internet")
#subprocess.run("iptables -t nat -A PREROUTING -p tcp -m tcp -s 192.168.1.0/24 --dport 80 -j DNAT --to-destination 192.168.1.1:80".split(" "))
#subprocess.run("iptables -t nat -A PREROUTING -p tcp -m tcp -s 192.168.1.0/24 --dport 443 -j DNAT --to-destination 192.168.1.1:80".split(" "))

print ("Starting web server")
app = Flask(__name__)

# 192.168.1.202 - - [07/Oct/2021 16:22:26] "GET /generate_204 HTTP/1.1" 404 -
# 192.168.1.202 - - [07/Oct/2021 16:22:26] "GET /gen_204 HTTP/1.1" 404 -
#192.168.1.207 - - [07/Oct/2021 16:23:37] "GET /canonical.html HTTP/1.1" 404 -
#192.168.1.207 - - [07/Oct/2021 16:24:08] "GET /connecttest.txt HTTP/1.1" 404 -
#Le mandamos un codigo distinto de 204 para que detecte que es un portal cautivo

"""
        Este enfoque se basa en una URL específica, 
        mWalledGardenUrl = "http://clients3.google.com/generate_204" 
        siempre devolviendo un código de 204 respuestas. 
        Esto funcionará incluso si se ha interferido con el DNS,
        ya que en ese caso se devolverá un código 200 lugar del esperado 204 .
        He visto algunos portales cautivos que spoofing peticiones a esta URL específica
        para prevenir el Internet no accesible mensaje en los dispositivos androides.
        
        Este enfoque no funcionará en áreas con acceso restringido a Internet,
        como China, donde todo el país es un jardín amurallado , 
        y donde la mayoría de los servicios de Google / Apple están bloqueados o filtrados.
        Algunos de estos pueden no estar bloqueados: 
        http://www.google.cn/generate_204 , 
        http://g.cn/generate_204 , 
        http://gstatic.com/generate_204 o 
        http://connectivitycheck.gstatic.com/generate_204 – 
        sin embargo, todos estos pertenecen a google por lo que no garantiza el trabajo. 

        Google tiene una variación de este tema: la búsqueda http://www.google.com/blank.html devolverá un código 200 con un cuerpo de respuesta de longitud cero. Así que si usted consigue un cuerpo no vacío esto sería otra manera de averiguar que usted está detrás de un jardín amurallado. 
        Apple tiene su propia URL para detectar portales cautivos: 
        cuando la red está conectada, los dispositivos IOS y MacOS se conectan a una URL como
        http://www.apple.com/library/test/success.html , 
        http://attwifi.apple.com/library/test/success.html , 
        http://captive.apple.com/hotspot-detect.html 
        que debe devolver un código de estado HTTP de 200 y un cuerpo que contiene Success . 
"""

# @app.route('/library/test/success.html') #APPLE
# @app.route('/library/test/success.html') #APPLE
# @app.route('/hotspot-detect.html')       #APPLE
# @app.route('/canonical.html')           #WINDOWS
# @app.route('/connecttest.txt')          #WINDOWS
# @app.route('/ncc.txt')                  #WINDOWS
# @app.route('/crl/hydrantidcao1.crl')    #WINDOWS
# @app.route('/generate_204')             #ANDROID
# @app.route('/gen_204')                  #ANDROID
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve():
    return make_response(html_login, 200)

#print ("Redirecting HTTP traffic to captive portal")
#subprocess.run(["iptables", "-t", "nat", "-A", "PREROUTING", "-i", IFACE, "-p", "tcp", "--dport", "80", "-j" ,"DNAT", "--to-destination", IP_ADDRESS+":"+str(PORT)])

#print ("Redirecting HTTPS traffic to captive portal")
#subprocess.run(["iptables", "-t", "nat", "-A", "PREROUTING", "-i", IFACE, "-p", "tcp", "--dport", "443", "-j" ,"DNAT", "--to-destination", IP_ADDRESS+":"+str(PORT)])


app.run(host="0.0.0.0", port=PORT, debug=True)
