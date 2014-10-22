import xbmc, xbmcgui

import socket
import re
import hashlib
import random
import json
import urllib2

import glob
from glob import addon_log, ADDON_PATH, addon

class acestream():
  buffer_size = 1024

  #PRODUCT_KEY='kjYX790gTytRaXV04IvC-xZH3A18sj5b1Tf3I-J5XVS1xsj-j0797KwxxLpBl26HPvWMm' #free
  PRODUCT_KEY='n51LvQoTlJzNGaFxseRK-uvnvX-sD4Vm5Axwmc4UcoD-jruxmKsuJaH0eVgE' #aceproxy

  def __init__( self , *args, **kwargs):
    self.player=kwargs.get('player')
    url=kwargs.get('url')
    self.listitem=kwargs.get('listitem')

    self.pid = url.replace('acestream://', '')

    self.ace_host = addon.getSetting('ace_host')
    self.ace_port = int(addon.getSetting('ace_port'))

    addon_log('INIT ACESTREAM')

  def read_lines(self, sock, recv_buffer=4096, delim='\n'):
    buffer = ''
    data = True
    while data:
      data = sock.recv(recv_buffer)
      buffer += data

      while buffer.find(delim) != -1:
        line, buffer = buffer.split('\n', 1)
        yield line
    return

  def engine_connect(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addon_log(self.ace_host)
    addon_log(self.ace_port)
    self.sock.connect((self.ace_host, self.ace_port))
    self.sock.send("HELLOBG version=3"+"\r\n")
    self.ace_read()

  def auth(self, data):
    p = re.compile('\skey=(\w+)\s')
    m = p.search(data)
    REQUEST_KEY=m.group(1)

    signature = hashlib.sha1(REQUEST_KEY + self.PRODUCT_KEY).hexdigest()
    response_key = self.PRODUCT_KEY.split ("-") [0] + "-" + signature

    self.sock.send("READY key="+response_key+"\r\n")

  def ch_open(self):
    request_id = random.randint(1, 100)
    self.sock.send('LOADASYNC ' + str(request_id) + ' PID ' + self.pid + "\r\n")
    return request_id

  def ch_start(self):
    self.sock.send('START PID ' + self.pid + " 0" + "\r\n")

  def shutdown(self):
    self.sock.send("SHUTDOWN"+"\r\n")

  def ace_read(self):
    for line in self.read_lines(self.sock):
      addon_log(line)
      if line.startswith("HELLOTS"):
        self.auth(line)
      elif line.startswith("AUTH"):
        self.request_id = self.ch_open()
      elif line.startswith("LOADRESP"):
        response = line.split()[2:]
        response = ' '.join(response)
        response = json.loads(response)

        infohash = response.get('infohash')
        #self.sock.send('GETADURL width = 1328 height = 474 infohash = ' + infohash + ' action = load'+"\r\n")
        #self.sock.send('GETADURL width = 1328 height = 474 infohash = ' + infohash + ' action = pause'+"\r\n")

        if response.get('status') == 100:
          addon_log("LOADASYNC returned error with message: %s" % response.get('message'))
        else:
          filename = urllib2.unquote(response.get('files')[0][0])
          addon_log(filename)
          self.ch_start()

      elif line.startswith("START"):
        try:
          player_url = line.split()[1]
          addon_log (player_url)
          self.player.callback = self.shutdown
          self.player.play(player_url, self.listitem)
        except IndexError as e:
          player_url = None

        #p = re.compile('(http://)[\w\W]+?(\:[0-9]+/)')
        #player_url = url
        #player_url = p.sub(r"\1" + self.ace_host + r"\2", url)
        #addon_log (player_url)
        #self.player.play(player_url, self.listitem)

        #self.sock.send("PAUSE"+"\r\n")
        #self.sock.send("RESUME"+"\r\n")
        #self.sock.send("STOP"+"\r\n")
        #self.sock.send("SHUTDOWN"+"\r\n")

      #elif line.startswith("SHUTDOWN"):
      #  self.sock.close()
      #  break

      elif line.startswith("EVENT"):
        #print line
        pass
