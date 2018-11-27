import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs
import os
import hashlib
import sys
import re
import uuid

import sqlite3

from settings import SETTINGS
from common import addon, addon_log

def addChannel(catId):
  kb = xbmc.Keyboard('', addon.getLocalizedString(30403))

  #url
  kb.doModal()
  if (kb.isConfirmed()):
    url = kb.getText()
    if url == '' : sys.exit(0)
    else:
      #protocol
      m = re.search('^(\w+)://', url)
      if(m):
        protocol = m.group(1)
      else:
        xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30406), "", 1))
        sys.exit(0)

      #name
      kb = xbmc.Keyboard('', addon.getLocalizedString(30404))
      kb.doModal()
      if (kb.isConfirmed()):
        name = kb.getText()
        name = name.title()
        if name == '' : sys.exit(0)
        else:
          #save
          if(insertStream(catId, url, name, protocol) == False):
            xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30408), "", 1))
            xbmc.executebuiltin("Container.Refresh")
          xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30405), "", 1))
          xbmc.executebuiltin("Container.Refresh")
      else:
        xbmc.executebuiltin("Container.Refresh")
  else:
    xbmc.executebuiltin("Container.Refresh")

def insertStream(catId, url, name, protocol):
  db_connection=sqlite3.connect(SETTINGS.CHANNELS_DB)
  db_cursor=db_connection.cursor()
  sql = "INSERT INTO channels \
         (id, id_cat, name, address, protocol, status, my) \
         VALUES(?, ?, ?, ?, ?, ?, ?)"
  st = db_cursor.execute(sql, (str(uuid.uuid1()), catId, name, url, protocol, 2, 1))
  addon_log(str(uuid.uuid1()))
  db_connection.commit()
  return st

def deleteStream(chId):
  db_connection=sqlite3.connect(SETTINGS.CHANNELS_DB)
  db_cursor=db_connection.cursor()
  sql = "DELETE FROM channels \
         WHERE id = ?"
  db_cursor.execute(sql, (chId, ))
  db_connection.commit()
  xbmc.executebuiltin("Container.Refresh")

def setStatus(chId, status):
  db_connection=sqlite3.connect(SETTINGS.CHANNELS_DB)
  db_cursor=db_connection.cursor()
  sql = "UPDATE channels \
         SET status = ? \
         WHERE id = ?"
  db_cursor.execute(sql, (status, chId))
  db_connection.commit()
  xbmc.executebuiltin("Container.Refresh")

