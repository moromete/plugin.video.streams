import xbmc
import os, sys
from urlparse import urlparse
from posixpath import basename, dirname
from common import addon, addon_log, is_exe

class SETTINGS(object):

  ADDON_PATH = addon.getAddonInfo('path')
  PROFILE = xbmc.translatePath(addon.getAddonInfo('profile'))
  
  LANGUAGE = 'en'
  #CHAN_LIST_URL = addon.getSetting('chan_list_url')
  CHAN_LIST_URL = 'https://moromete.github.io/repository.moromete.addons/plugin.video.streams/streams.json'
  EXPORT_EMAIL = 'streams201811@gmail.com'

  parse_object = urlparse(CHAN_LIST_URL)
  f_name = basename(parse_object[2]); #file name of the channel list
  # CHAN_LIST = os.path.join(ADDON_PATH, f_name) #full path of the channel list
  CHAN_LIST = os.path.join(PROFILE, f_name) #full path of the channel list
  CHAN_LIST_EXPIRE =  int(addon.getSetting('chan_list_expire'))*60*60
  # CHANNELS_DB = os.path.join(ADDON_PATH,'channels.sqlite')
  CHANNELS_DB = os.path.join(PROFILE,'channels.sqlite')
  EXPORT_CHAN_LIST = os.path.join(PROFILE, 'export.json') 

  #DISABLE_SCHEDULE = addon.getSetting('disable_schedule')
  SHOW_OFFLINE_CH = addon.getSetting('show_offline_ch')
  SHOW_UNVERIFIED = addon.getSetting('show_unverified')

  # DISABLE_SCHEDULE = addon.getSetting('disable_schedule')
  # SCHEDULE_PATH = os.path.join(ADDON_PATH,'schedule.sqlite')
  EPG_URL = addon.getSetting('epg_url')

  ########################################## sopcast
  SPSC_BINARY = "sp-sc-auth"
  
  #raspberry pi
  QEMU = "qemu-i386"  #for raspberry pi to issue kill command
  QEMU64 = "qemuaarch-i386"
  ARM = False
  ARM64 = False
  
  if sys.platform.startswith('linux'):
    if(os.uname()[4][:3] == 'arm'): #not supported by windows
      ARM = True
    elif(os.uname()[4][:3] == 'aar'):
      ARM = True
      ARM64 = True if sys.maxsize > 2**32 else False
  
  if ARM == False :
    SPSC = os.path.join(ADDON_PATH, 'bin/linux_x86/sopcast', SPSC_BINARY)
    SPSC_LIB = os.path.join(ADDON_PATH, 'bin/linux_x86/sopcast/lib')
    
    LOADER = os.path.join(ADDON_PATH, 'bin/linux_x86/sopcast', 'ld-linux.so.2')

    #make executables
    is_exe(SPSC)
    is_exe(LOADER)

    SPSC = [LOADER, '--library-path', os.path.join(ADDON_PATH, 'bin/linux_x86/sopcast', 'lib'), SPSC]

  elif ARM == True:
      SOPCAST_ARM_PATH =  addon.getSetting('sopcast_arm_path')
      if(SOPCAST_ARM_PATH == '') :
        SOPCAST_ARM_PATH = os.path.join(ADDON_PATH, 'bin/arm/sopcast')
      is_exe(os.path.join(SOPCAST_ARM_PATH, "lib/ld-linux.so.2"))

      if ARM64 == False:
        is_exe(os.path.join(SOPCAST_ARM_PATH, QEMU))
        QEMU_SPSC = [os.path.join(SOPCAST_ARM_PATH, QEMU), os.path.join(SOPCAST_ARM_PATH, "lib/ld-linux.so.2"), "--library-path", os.path.join(SOPCAST_ARM_PATH, "lib")]
      else:
        is_exe(os.path.join(SOPCAST_ARM_PATH, QEMU64))
        QEMU_SPSC = [os.path.join(SOPCAST_ARM_PATH, QEMU64), os.path.join(SOPCAST_ARM_PATH, "lib/ld-linux.so.2"), "--library-path", os.path.join(SOPCAST_ARM_PATH, "lib")]

      # SPSC = os.path.join(SOPCAST_ARM_PATH, SPSC_BINARY)
      SPSC = QEMU_SPSC + [os.path.join(SOPCAST_ARM_PATH, SPSC_BINARY)]

  LOCAL_PORT =  addon.getSetting('local_port')
  VIDEO_PORT =  addon.getSetting('video_port')
  BUFER_SIZE = int(addon.getSetting('buffer_size'))
  USE_PLEXUS_SOP = addon.getSetting('use_plexus_sop')

  LOCAL_URL = "http://localhost:"+str(VIDEO_PORT)+"/?"

  TEST_URL = "http://www.google.com"
  ##########################################################

  ########################################################## acestream
  #PRODUCT_KEY='kjYX790gTytRaXV04IvC-xZH3A18sj5b1Tf3I-J5XVS1xsj-j0797KwxxLpBl26HPvWMm' #free
  PRODUCT_KEY='n51LvQoTlJzNGaFxseRK-uvnvX-sD4Vm5Axwmc4UcoD-jruxmKsuJaH0eVgE' #aceproxy
  ACE_HOST = addon.getSetting('ace_host')
  ACE_PORT = int(addon.getSetting('ace_port'))
  ACE_ENGINE_TYPE = int(addon.getSetting('ace_engine_type'))
##########################################################