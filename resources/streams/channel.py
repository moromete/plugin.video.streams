import sqlite3
import uuid

from settings import SETTINGS
from common import addon, addon_log

class Channel():
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

    self.db_connection=sqlite3.connect(SETTINGS.CHANNELS_DB)
    self.db_cursor=self.db_connection.cursor()
 
  def findOne(self, id):
    sql = "SELECT id_cat, name, address, protocol, language, status, unverified, my, deleted \
           FROM channels \
           where id = ?"
    self.db_cursor.execute( sql, (id, ) )
    rec=self.db_cursor.fetchone()
    if rec != None:
      self.id         = id
      self.id_cat     = rec[0]
      self.name       = rec[1]
      self.address    = rec[2]
      self.protocol   = rec[3]
      self.language   = rec[4]
      self.status     = rec[5]
      self.unverified = rec[6]
      self.my         = rec[7]
      self.deleted    = rec[8]
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
  
  def insert(self):
    sql = "INSERT INTO channels \
           (id, id_cat, name, address, protocol, language, status, unverified, my) \
           VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"
    st = self.db_cursor.execute(sql, (self.id,
                                      self.id_cat,
                                      self.name,
                                      self.address,
                                      self.protocol,
                                      self.language,
                                      self.status,
                                      self.unverified,
                                      self.my,
                                     ))
    self.db_connection.commit()
    return st

  def update(self):
    sql = "UPDATE channels \
           SET id_cat =?,  \
               name = ?, \
               address = ?, \
               protocol = ?, \
               language = ?, \
               status = ?, \
               unverified = ?, \
               my = ?, \
               deleted = ?) \
           where id = ?"
    st = self.db_cursor.execute(sql, (self.id_cat,
                                      self.name,
                                      self.address,
                                      self.protocol,
                                      self.language,
                                      self.status,
                                      self.unverified,
                                      self.my,
                                      self.deleted,
                                      self.id))
    self.db_connection.commit()
    return st

  def setStatus(self, status):
    self.status = status
    sql = "UPDATE channels \
          SET status = ? \
          WHERE id = ?"
    st = self.db_cursor.execute(sql, (self.status, self.id, ))
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
