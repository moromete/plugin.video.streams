import sqlite3

from settings import SETTINGS

class Category():
  def __init__( self , *args, **kwargs):
    self.id = kwargs.get('id')
    self.name = kwargs.get('name')
    
    self.db_connection=sqlite3.connect(SETTINGS.CHANNELS_DB)
    self.db_cursor=self.db_connection.cursor()
 
  def findOne(self, id):
    sql = "SELECT name \
           FROM categories \
           where id = ?"
    self.db_cursor.execute( sql, (id) )
    rec=self.db_cursor.fetchone()
    if rec != None:
      self.id         = id
      self.name       = rec[1]
      return True
  
  def save(self):
    if(self.id):
      return self.update()
    else:
      return self.insert()
  
  def insert(self):
    sql = "INSERT INTO categories \
           (id, name) \
           VALUES(?, ?)"
    st = self.db_cursor.execute(sql, (self.id,
                                      self.name,))
    self.db_connection.commit()
    return st

  def update(self):
    sql = "UPDATE categories \
           SET name = ? \
           where id = ?"
    st = self.db_cursor.execute(sql, (self.name,
                                      self.id,))
    self.db_connection.commit()
    return st
