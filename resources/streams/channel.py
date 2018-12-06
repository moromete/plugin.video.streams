import sqlite3
import uuid
from datetime import datetime

from settings import SETTINGS
from common import addon, addon_log

class Channel():
  STATUS_ONLINE   = 1
  STATUS_OFFLINE  = -1

  def __init__( self , *args, **kwargs):
    self.id = kwargs.get('id')
    self.id_cat = kwargs.get('id_cat')
    self.name = kwargs.get('name')
    self.address = kwargs.get('address')
    self.protocol = kwargs.get('protocol')
    self.language = kwargs.get('language')
    self.status = kwargs.get('status')
    self.unverified = kwargs.get('unverified')
    self.my = kwargs.get('my')
    self.deleted = kwargs.get('deleted')
    self.last_online = kwargs.get('last_online')
    self.checked = kwargs.get('checked')

    self.db_connection=sqlite3.connect(SETTINGS.CHANNELS_DB)
    self.db_cursor=self.db_connection.cursor()
 
  def findOne(self, id):
    sql = "SELECT id_cat, name, address, protocol, language, status, unverified, my, deleted, last_online, checked \
           FROM channels \
           where id = ?"
    self.db_cursor.execute( sql, (id, ) )
    rec=self.db_cursor.fetchone()
    if rec != None:
      self.id          = id
      self.id_cat      = rec[0]
      self.name        = rec[1]
      self.address     = rec[2]
      self.protocol    = rec[3]
      self.language    = rec[4]
      self.status      = rec[5]
      self.unverified  = rec[6]
      self.my          = rec[7]
      self.deleted     = rec[8]
      self.last_online = rec[9]
      self.checked     = rec[10]
      return True
  
  def save(self):
    if(self.id):
      return self.update()
    else:
      if(self.checkAddrExist() == False):
        self.id  = str(uuid.uuid1())
        return self.insert()
      else:
        return False

  def checkAddrExist(self):
    sql = "SELECT id \
           FROM channels \
           where address = ?"
    self.db_cursor.execute( sql, (self.address, ) )
    rec=self.db_cursor.fetchone()
    if(rec != None):
      self.id = rec[0]
      return True
    else:
      return False
    
  def checkExist(self):
    sql = "SELECT id \
           FROM channels \
           where id = ?"
    self.db_cursor.execute( sql, (self.id, ) ) 
    rec=self.db_cursor.fetchone()
    if(rec != None):
      self.id = rec[0]
      return True
    else:
      return False

  def checkIsMy(self):
    sql = "SELECT my \
           FROM channels \
           where id = ?"
    self.db_cursor.execute( sql, (self.id, ) ) 
    rec=self.db_cursor.fetchone()
    if(rec[0] == 1):
      return True
    else:
      return False
  
  def insert(self):
    sql = "INSERT INTO channels \
           (id, id_cat, name, address, protocol, language, status, unverified, my, last_online, checked) \
           VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    st = self.db_cursor.execute(sql, (self.id,
                                      self.id_cat,
                                      self.name,
                                      self.address,
                                      self.protocol,
                                      self.language,
                                      self.status,
                                      self.unverified,
                                      self.my,
                                      self.last_online,
                                      self.checked
                                     ))
    self.db_connection.commit()
    return st

  def update(self, **kwargs):
    sql = "UPDATE channels SET "
    values = []
    count = 1
    for key, value in kwargs.items():
      values.append(value)
      if(count > 1):
        sql += ", "
      sql += " %s = ? " % key
      count = count + 1
    sql += " WHERE id = ? "
    values.append(self.id)
    #addon_log(sql)
    #addon_log(values)
    st = self.db_cursor.execute(sql, values)
    self.db_connection.commit()
    return st

  def setStatus(self, status):
    self.status = status
    if(self.status == self.STATUS_ONLINE):
      self.last_online = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    sql = "UPDATE channels \
           SET status = ?, \
           last_online = ?, \
           checked = 1 \
           WHERE id = ?"
    st = self.db_cursor.execute(sql, (self.status, self.last_online, self.id, ))
    self.db_connection.commit()
    return st
      
  def delete(self, softDelete=False):
    addon_log(self.my)
    if(self.my):
      sql = "DELETE FROM channels \
            WHERE id = ?"
      st = self.db_cursor.execute(sql, (self.id, ))
      self.db_connection.commit()
      return st
    else:
      sql = "UPDATE channels \
            SET deleted = 1 \
            WHERE id = ?"
      st = self.db_cursor.execute(sql, (self.id, ))
      self.db_connection.commit()
      return st
