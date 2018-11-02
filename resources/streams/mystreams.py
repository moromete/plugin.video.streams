import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs
import os
import hashlib
import sys
import re

import sqlite3

from settings import SETTINGS
from common import addon, addon_log

def add_stream(catId):
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
        if name == '' : sys.exit(0)
        else:
          #save
          save(catId, url, name, protocol)
          xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30405), "", 1))
          xbmc.executebuiltin("Container.Refresh")
      else:
        xbmc.executebuiltin("Container.Refresh")
  else:
    xbmc.executebuiltin("Container.Refresh")

def save(catId, url, name, protocol):
  db_connection=sqlite3.connect(SETTINGS.CHANNELS_DB)
  db_cursor=db_connection.cursor()
  sql = "INSERT INTO channels \
         (id_cat, name, address, protocol, status, unverified) \
         VALUES(?,?,?,?,?,?)"
  st = db_cursor.execute(sql, (catId, name, url, protocol, 2, 1))
  db_connection.commit()