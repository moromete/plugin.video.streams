import xbmc, xbmcgui

import socket
import re
import hashlib
import random
import json
import urllib2
import urllib
import time

import glob
from common import addon_log, addon
from settings import SETTINGS
from resources.streams.channels import Channels

class acestream():
  buffer_size = 1024
  start_time = None
  timeout = 30

  def __init__( self , *args, **kwargs):
    self.player=kwargs.get('player')
    url=kwargs.get('url')
    self.listitem=kwargs.get('listitem')

    self.player_started = None

    self.pid = url.replace('acestream://', '')
    self.pid = self.pid.replace('/', '')

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
    try:
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sock.connect((SETTINGS.ACE_HOST, SETTINGS.ACE_PORT))
    except Exception as inst:
      addon_log(inst)
      try: xbmc.executebuiltin("Dialog.Close(all,true)")
      except: pass
      DEBUG = addon.getSetting('debug')
      if DEBUG == 'true': xbmc.executebuiltin("Notification(%s,%s,%i)" % (str(type(inst)), str(inst), 5))
      return False

    self.send("HELLOBG version=3")
    self.ace_read()

  def auth(self, data):
    p = re.compile('\skey=(\w+)\s')
    m = p.search(data)
    REQUEST_KEY=m.group(1)

    signature = hashlib.sha1(REQUEST_KEY + SETTINGS.PRODUCT_KEY).hexdigest()
    response_key = SETTINGS.PRODUCT_KEY.split ("-") [0] + "-" + signature

    self.send("READY key="+response_key)

  def ch_open(self):
    request_id = random.randint(1, 100)
    cmd = 'LOADASYNC ' + str(request_id) + ' PID ' + self.pid
    self.send(cmd)
    addon_log(cmd)
    return request_id

  def ch_start(self):
    self.send('START PID ' + self.pid + " 0")
    self.start_time = time.time()

  def shutdown(self):
    #addon_log("SHUTDOWN")
    self.send("SHUTDOWN")
    try: xbmc.executebuiltin("Dialog.Close(all,true)")
    except: pass

  def send(self, cmd):
    try:
      self.sock.send(cmd + "\r\n")
    except Exception as inst:
      addon_log(inst)

  def ace_read(self):
    for line in self.read_lines(self.sock):

      if ((self.start_time!=None) and ((time.time() - self.start_time) > self.timeout)):
        self.shutdown()
        xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30057), "", 10000))

      addon_log(line)
      if line.startswith("HELLOTS"):
        self.auth(line)
      elif line.startswith("AUTH"):
        self.request_id = self.ch_open()
      elif line.startswith("LOADRESP"):
        response = line.split()[2:]
        response = ' '.join(response)
        response = json.loads(response)

        if response.get('status') == 100:
          addon_log("LOADASYNC returned error with message: %s" % response.get('message'))
          xbmc.executebuiltin("Notification(%s,%s,%i)" % (response.get('message'), "", 10000))
          return False

        infohash = response.get('infohash')
        #self.sock.send('GETADURL width = 1328 height = 474 infohash = ' + infohash + ' action = load'+"\r\n")
        #self.sock.send('GETADURL width = 1328 height = 474 infohash = ' + infohash + ' action = pause'+"\r\n")

        self.filename = urllib.unquote(response.get('files')[0][0].encode('ascii')).decode('utf-8')
        addon_log(self.filename)
        self.ch_start()

      elif line.startswith("START"):
        self.start_time = None

        try: xbmc.executebuiltin("Dialog.Close(all,true)")
        except: pass

        try:
          player_url = line.split()[1]
          addon_log (player_url)
          self.player.callback = self.shutdown
          self.listitem.setInfo('video', {'Title': self.filename})
          self.player.play(player_url, self.listitem)
          self.player_started = True
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

      elif line.startswith("SHUTDOWN"):
        self.sock.close()

        #offline notif
        #if player was not started
        #addon_log('player_started=');
        #addon_log(self.player_started);
        if(self.player_started != True):
          ch = Channels();
          ch.markStream(chId = self.player.ch_id, status=1) #offline

        break

      #INFO 1;Cannot find active peers
      elif line.startswith("INFO"):
        tmp = line.split(';')
        info_status = tmp[0].split()[1]
        if(info_status == '1'): #INFO 1;Cannot find active peers
          info_msg = tmp[1]
          self.shutdown()
          xbmc.executebuiltin("Notification(%s,%s,%i)" % (info_msg, "", 10000))

      elif line.startswith("EVENT"):
        #print line
        pass
