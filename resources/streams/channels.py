import xbmc, xbmcgui

import sys
import re
import sqlite3
import json
import os.path

from settings import SETTINGS
from common import addon, addon_log
from channel import Channel
from category import Category

class Channels():
  def __init__( self , **kwargs):
    self.catId = kwargs.get('catId')

  # def createDb(self):
  #   db_connection=sqlite3.connect(SETTINGS.CHANNELS_DB)
  #   db_cursor=db_connection.cursor()

  #   sql = "CREATE TABLE IF NOT EXISTS categories (id INTEGER, name TEXT)"
  #   addon_log(sql)
  #   db_cursor.execute(sql);
    
  #   sql="DELETE FROM categories"
  #   db_cursor.execute(sql)

  #   #video_resolution TEXT, video_aspect REAL, audio_codec TEXT, video_codec TEXT, thumbnail TEXT, schedule_id INTEGER,\
  #   sql = "CREATE TABLE IF NOT EXISTS channels \
  #         (id TEXT, id_cat INTEGER, name TEXT, language TEXT, status INTEGER, \
  #          address TEXT, protocol TEXT, \
  #          unverified INTEGER, my integer, deleted integer)"
  #   db_cursor.execute(sql)
    
  #   # sql="DELETE FROM channels"
  #   # db_cursor.execute(sql)
    
  #   db_connection.commit()
  #   db_connection.close()

  def migrateDb(self):
    addon_log("""Run database migrations.""")

    def get_script_version(path):
        return int(path.split('_')[0])

    db = sqlite3.connect(SETTINGS.CHANNELS_DB)
    current_version = db.cursor().execute('pragma user_version').fetchone()[0]

    addon_log(current_version)

    migrations_path = os.path.join(SETTINGS.ADDON_PATH, 'resources/streams/migrations/')
    migration_files = list(os.listdir(migrations_path))
    for migration in sorted(migration_files):
        scriptFile = "{0}".format(migration)
        migration_version = get_script_version(scriptFile)
        scriptPath = os.path.join(SETTINGS.ADDON_PATH, 'resources/streams/migrations/', scriptFile)

        if migration_version > current_version:
            addon_log("applying migration {0}".format(migration_version))
            with open(scriptPath, mode='r') as f:
                 db.cursor().executescript(f.read())
                 addon_log("database now at version {0}".format(migration_version))
        else:
            addon_log("migration {0} already applied".format(migration_version))

  def addChannel(self):
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
          name = name.decode('utf8')
          if name == '' : sys.exit(0)
          else:
            #save
            ch = Channel(id_cat = self.catId, address = url, name=name, protocol=protocol, status=Channel.STATUS_ONLINE, my=1)
            if(ch.save() == False):
              xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30408), "", 1))
              xbmc.executebuiltin("Container.Refresh")
            xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30405), "", 1))
            xbmc.executebuiltin("Container.Refresh")
        else:
          xbmc.executebuiltin("Container.Refresh")
    else:
      xbmc.executebuiltin("Container.Refresh")
  
  def deleteStream(self, chId):
    ch = Channel()
    ch.findOne(chId)
    ch.delete()
    xbmc.executebuiltin("Container.Refresh")

  def cleanCategories(self):
    db = sqlite3.connect(SETTINGS.CHANNELS_DB)
    db_cursor=db.cursor()

    sql="DELETE FROM categories"
    db_cursor.execute(sql)

    db.commit()
    db.close()
  
  def importChannels(self):
    # self.createDb()
    # self.migrateDb()
    
    with open(SETTINGS.CHAN_LIST) as json_file:
      data = json.loads(json_file.read())
      json_file.close()

      self.cleanCategories()

      parsedIds = []

      for group in data['groups']:
        addon_log(str(group['id']) + " " + group['name'])
        cat = Category(id = group['id'], name=group['name'])
        cat.insert()
        
        for channel in group['channels']:
          #addon_log(str(channel['id'])+" "+unicode(channel['name'])+" "+ str(channel['language'])+" "+str(channel['status']))
          if ((not channel['unverified']) or (SETTINGS.SHOW_UNVERIFIED=='true')):

            #addon_log(channel['name'].encode('utf8'))

            # schedule_id = 0
            # thumbnail = ""
            # video_resolution = ""
            # video_aspect = 0
            # audio_codec = ""
            # video_codec = ""

            # stream_type = channel['stream_type']
            # if 'schedule' in channel:
            #   schedule = channel['schedule']
            #   schedule_id = schedule['ch_id']
            # if 'thumbnail' in channel:
            #   thumbnail = channel['thumbnail']
            # if 'video_resolution' in stream_type:
            #   video_resolution = stream_type['video_resolution']
            # if 'video_aspect' in stream_type:
            #   video_aspect = stream_type['video_aspect']
            # if 'audio_codec' in stream_type:
            #   audio_codec = stream_type['audio_codec']
            # if 'video_codec' in stream_type:
            #   video_codec = stream_type['video_codec']
            if(channel['status'] == 2): 
              status = Channel.STATUS_ONLINE 
            else: 
              status = Channel.STATUS_OFFLINE

            ch = Channel(id = str(channel['id']),
                         id_cat = group['id'],
                         name = channel['name'],
                         address = channel['address'], 
                         protocol = channel['protocol'],
                         language = channel['language'],
                         status = status,
                         unverified = channel['unverified']
                        )
            if((ch.checkExist() == False) and (ch.checkAddrExist() == False)):
              ch.insert()
            else:
              if(ch.checkIsMy() == False):
                ch.update(id_cat = group['id'],
                          name = channel['name'],
                          address = channel['address'], 
                          protocol = channel['protocol'],
                          language = channel['language'],
                          status = status,
                          unverified = channel['unverified'])
            
            if(ch.checkIsMy() == False):
              parsedIds.append(ch.id)
      
      addon_log('parsed %d channels' % len(parsedIds))
      self.cleanChannels(parsedIds)
  
  #delete channels that are not comming from import and are not my channels
  def cleanChannels(self, parsedIds):
    if(len(parsedIds) > 0):
      db = sqlite3.connect(SETTINGS.CHANNELS_DB)
      db_cursor=db.cursor()
      # addon_log(parsedIds)

      #do not delete my channels 
      sql="DELETE FROM channels WHERE id NOT IN ( %s ) AND my IS NULL" % ", ".join(parsedIds)
      # addon_log(sql)
      db_cursor.execute(sql)

      db.commit()
      db.close()

  def loadChannels(self, loadUnverified = False):
    db_connection=sqlite3.connect(SETTINGS.CHANNELS_DB)
    db_cursor=db_connection.cursor()

    sql = 'SELECT id, name, language, status, \
           address, protocol, \
           unverified, my \
           FROM channels \
           WHERE id_cat = ? and deleted is NULL'
    if(loadUnverified):
      sql += ' and unverified = 1'
    else:
      sql += ' and unverified IS NULL'
    sql += ' ORDER BY name'
    
    db_cursor.execute( sql, (self.catId, ) )
    rec=db_cursor.fetchall()
    
    arrChannels = []
    if len(rec)>0:
      for id, name, language, status, \
          address, protocol, \
          unverified, my in rec:
        ch = Channel(id=id, 
                     id_cat=self.catId,
                     name=name,
                     language=language,
                     status=status,
                     address=address,
                     protocol=protocol,
                     unverified=unverified,
                     my=my)
        arrChannels.append(ch)
    db_connection.close()
    return arrChannels

  def loadCategories(self):
    db_connection=sqlite3.connect(SETTINGS.CHANNELS_DB)
    db_cursor=db_connection.cursor()
      
    sql = "SELECT id, name \
           FROM categories"
    db_cursor.execute(sql)
    rec=db_cursor.fetchall()
    
    arrCategories = []
    if len(rec)>0:
      for id, name in rec:
        cat = Category(id=id, 
                       name=name)
        arrCategories.append(cat)
    db_connection.close()
    return arrCategories
  
  def markStream(self, chId, status):
    ch = Channel()
    ch.findOne(chId)
    ch.setStatus(status)
    # xbmc.executebuiltin("Container.Refresh")


    