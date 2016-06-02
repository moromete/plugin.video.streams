import os
from urlparse import urlparse
from posixpath import basename, dirname
from glob import addon, is_exe

class SETTINGS(object):

  ADDON_PATH= addon.getAddonInfo('path')

  LANGUAGE = 'en'
  CHAN_LIST_URL = addon.getSetting('chan_list_url')

  parse_object = urlparse(CHAN_LIST_URL)
  f_name = basename(parse_object[2]); #file name of the channel list
  CHAN_LIST = os.path.join(ADDON_PATH, f_name) #full path of the channel list
  CHAN_LIST_EXPIRE =  int(addon.getSetting('chan_list_expire'))*60*60
  CHANNELS_DB = os.path.join(ADDON_PATH,'channels.sqlite')

  #DISABLE_SCHEDULE = addon.getSetting('disable_schedule')
  SHOW_OFFLINE_CH = addon.getSetting('show_offline_ch')
  SHOW_UNVERIFIED = addon.getSetting('show_unverified')

  NOTIFY_OFFLINE = "true"

  DISABLE_SCHEDULE = addon.getSetting('disable_schedule')
  SCHEDULE_PATH = os.path.join(ADDON_PATH,'schedule.sqlite')

  ########################################## sopcast
  SPSC_BINARY = "sp-sc-auth"

  #raspberry pi
  QEMU = "qemu-i386"  #for raspberry pi to issue kill command
  ARM = False
  if(os.uname()[4][:3] == 'arm'):
    ARM = True

  if ARM == False :
    SPSC = os.path.join(ADDON_PATH, 'bin/linux_x86/sopcast', SPSC_BINARY)
    SPSC_LIB = os.path.join(ADDON_PATH, 'bin/linux_x86/sopcast')

    #make executables
    is_exe(SPSC)

  elif ARM == True:
    SOPCAST_ARM_PATH =  addon.getSetting('sopcast_arm_path')
    if(SOPCAST_ARM_PATH == '') :
      SOPCAST_ARM_PATH = os.path.join(ADDON_PATH, 'bin/arm/sopcast')

    #make executables
    is_exe(os.path.join(SOPCAST_ARM_PATH, QEMU))
    is_exe(os.path.join(SOPCAST_ARM_PATH, "lib/ld-linux.so.2"))

    QEMU_SPSC = [os.path.join(SOPCAST_ARM_PATH, QEMU), os.path.join(SOPCAST_ARM_PATH, "lib/ld-linux.so.2"), "--library-path", os.path.join(SOPCAST_ARM_PATH, "lib")]
    SPSC = os.path.join(SOPCAST_ARM_PATH, SPSC_BINARY)
    #/storage/sopcast/qemu-i386 /storage/sopcast/lib/ld-linux.so.2 --library-path /storage/sopcast/lib /storage/sopcast/sp-sc-auth 2>&- $1 $2 $3

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
  USE_PLEXUS_ACE = addon.getSetting('use_plexus_ace')
  ##########################################################
