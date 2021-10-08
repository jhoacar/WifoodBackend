#!/bin/bash
#Firewall que redirige todo el trafico hacia el servidor
#iptables -F
#iptables -t nat -F
iptables -A FORWARD -i br-lan -j DROP
iptables -A FORWARD -i br-lan -p tcp --dport 53 -j ACCEPT
iptables -A FORWARD -i br-lan -p udp --dport 53 -j ACCEPT
iptables -A FORWARD -i br-lan -p tcp --dport 80 -d 192.168.1.1 -j ACCEPT
iptables -t nat -A PREROUTING -i br-lan -p tcp --dport 443 -j DNAT --to-destination 192.168.1.1:80
iptables -t nat -A PREROUTING -i br-lan -p tcp --dport 80 -j DNAT --to-destination 192.168.1.1:80
