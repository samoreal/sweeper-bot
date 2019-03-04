from bungieapi import BungieApi

import ssl
import os
import json

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

class SweeperBotRequestHandler(BaseHTTPRequestHandler):
    # GET
    def do_GET(self):
        print ("New GET request...")
        parsed = urlparse(self.path)
        print("Path is {}".format(parsed.path))

        if parsed.path == '/authorize':
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.end_headers()

            bapi = BungieApi()
            querydict = parse_qs(parsed.query)
            auth = bapi.authorize(querydict['code'][0])

            try:
                auth['error']
                self.wfile.write(bytes(json.dumps(auth, indent=2), "utf8"))
            except Exception as e:
                bapi.storeAuth(auth)
                memberships = bapi.getMemberships(int(auth['membership_id']))
                bapi.storeMemberships(memberships)
                self.wfile.write(bytes(json.dumps(memberships, indent=2), "utf8"))

        elif parsed.path == '/characters':
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.end_headers()

            bapi = BungieApi()
            querydict = parse_qs(parsed.query)
            chars = bapi.getCharacters(querydict['membership_id'][0],
                                      querydict['platform'][0])
            self.wfile.write(bytes(json.dumps(chars, indent=2), "utf8"))

        elif parsed.path == '/items':
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.end_headers()

            bapi = BungieApi()
            querydict = parse_qs(parsed.query)
            items = bapi.getCharacterItems(querydict['membership_id'][0],
                                        querydict['platform'][0],
                                        querydict['character_id'][0])
            self.wfile.write(bytes(json.dumps(items, indent=2), "utf8"))

        else:
            self.send_response(500)
            self.send_header('Content-Type','text/html')
            self.end_headers()
            self.wfile.write(bytes("Unsupported request", "utf8"))

if __name__ == '__main__':
    print ("Starting server...")
    certfile = os.getenv('LOCALHOST_CERT_FILE')

    httpd = HTTPServer(('localhost', 4443), SweeperBotRequestHandler)
    httpd.socket = ssl.wrap_socket(httpd.socket, server_side=True, certfile=certfile)

    print ("Running server forever...")
    httpd.serve_forever()
