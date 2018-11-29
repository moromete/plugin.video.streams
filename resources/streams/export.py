import sqlite3
import json
import os
import time
from datetime import datetime
import smtplib
#from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase

from settings import SETTINGS
from common import addon, addon_log

import xbmc, xbmcgui

class export():
  def __init__( self ):
    db_connection=sqlite3.connect(SETTINGS.CHANNELS_DB)
    self.db_cursor=db_connection.cursor()
    self.exportFile = os.path.join(addon.getAddonInfo('path'), 'export.json') 

  def createExportFile( self ):
    sql = "SELECT id, name, status, address, unverified, my \
           FROM channels \
           order by id_cat, name"
    self.db_cursor.execute( sql )
    rec=self.db_cursor.fetchall()

    if len(rec)>0:
      jsonData = []
      for id, name, status, \
          address, unverified, my in rec:
        channel = {'id': id,
                   'name': name,
                   'address': address,
                   'status': status,
                   'unverified': unverified,
                   'my': my}
        jsonData.append(channel)
      jsonStr = json.dumps(jsonData)

      f=open(self.exportFile,"w+")
      f.write(jsonStr)
      f.close() 

  def checkDoExport( self ):
    if not os.path.isfile(self.exportFile):
      return True

    nowTime = time.mktime(datetime.now().timetuple())
    timeCreated = os.stat(self.exportFile)[8]  # get local play list modified date
    if nowTime - timeCreated > 12*60*60: #12 hours
      return True
  
  def export(self):
    if(self.checkSmtp()):
      if(self.checkDoExport()):
        self.createExportFile()
        self.send()
      self.smtp.quit()
      return True;
  
  def send(self):
    emailTo = 'streams201811@gmail.com'

    msg = MIMEMultipart()
    #msg = EmailMessage()
    #msg['Subject'] = 'Export %s' % datetime.now().isoformat()
    msg['Subject'] = 'Export plugin.video.streams'
    msg['From'] = 'streams201811@gmail.com'
    msg['To'] = emailTo
    #msg.set_content(fp.read())
        
    fp=open(self.exportFile,"rb")
    attach = MIMEBase('application', 'json')
    attach.set_payload(fp.read())
    fp.close()
    # Encode the payload using Base64
    #encoders.encode_base64(msg)
    attach.add_header('Content-Disposition', 'attachment', filename='streams.json')
    msg.attach(attach)
    #msg.add_attachment(f.read(),
    #                   maintype='application',
    #                   subtype='json',
    #                   filename='export.json')
    
    try:  
      self.smtp.sendmail('streams201811@gmail.com', emailTo, msg.as_string())
      #s.send_message(msg)
    except Exception as inst:
      addon_log(inst)
      xbmcgui.Dialog().ok(addon.getLocalizedString(30300), addon.getLocalizedString(30409), str(inst))

  def checkSmtp(self):
    try:  
      self.smtp = smtplib.SMTP(addon.getSetting('smtp'))
      self.smtp.starttls()
      self.smtp.login(addon.getSetting('smtpUsername'), addon.getSetting('smtpPasswd'))
      self.smtp.ehlo()
      return True
    except Exception as inst:
      addon_log(inst)
      #xbmc.executebuiltin("Notification(%s,%s,%d)" % (addon.getLocalizedString(30409), "", 30000))
      xbmcgui.Dialog().ok(addon.getLocalizedString(30300), addon.getLocalizedString(30409), str(inst))