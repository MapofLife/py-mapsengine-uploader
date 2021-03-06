#####################################################
# Uploads all tif files in a folder to maps engine
# Configure in settings.config
# Has some code to move completed files to other folders
# and smart restart capabitlies, but I've commented that functionality out for now
#####################################################

import uploadraster
import sys
import logging
import os
import ConfigParser
import traceback
import datetime
import csv
import shutil

Config = ConfigParser.ConfigParser()
#get run configurations
Config.read('settings.config')
_DIR = Config.get('Settings','RasterDirectory')
_TAGS = Config.get('Settings','Tags').split(",")
_EMAIL = Config.get('Settings','Email')
_DESCRIPTION = Config.get('Settings','Description')
_USER_ACCESS_ID = Config.get('Settings','UserAccessID')
_WAIT = int(Config.get('Settings','APIWait'))
_EEIDS_PATH = Config.get('Settings','EEIDSPath')
_RUN_LOG_PATH = Config.get('Settings','RunLogPath')
_TAG_FILE = ''
if Config.has_option('OptionalSettings', 'TagFile'):
    _TAG_FILE = Config.get('OptionalSettings', 'TagFile')

#Internal constats
_EEIDS_FILE = 'eeids.csv'
_RUN_LOG_FILE = 'runlog.txt'
_CONTAINER_FOLDER = '%s/%s' % (_DIR,'container')
_UPLOADED_FOLDER = '%s/%s' % (_DIR,'uploaded')

######
# Maps Engine Status
# Uploading: means the container has been created, but the upload of the image failed
# Processing: search for status "Is ready to process" and "Is being processed" will return images with this status
# Image was Processed: search for "Was processed" will return images with this status
######

#Codes
NOT_STARTED_CODE = 0
CONTAINER_CODE = 1
UPLOADED_CODE = 2
PERMISSION_CODE = 3

def main(argv):
    print "Starting bulk upload..."
    eeidsfile = '%s/%s' %(_EEIDS_PATH,_EEIDS_FILE)
    runlogfile = '%s/%s' %(_RUN_LOG_PATH,_RUN_LOG_FILE)
    #clear out the current csv file that holds the earthengine id's generated by the upload
    with open(eeidsfile, "w"):
        pass
    
    #if a tag file is supplied, read it in
    tagsf = []
    if _TAG_FILE:
        with open(_TAG_FILE) as f:
            tagfile = csv.DictReader(f)
            for t in tagfile:
                tagsf.append(t)
        
    
    type(tagfile)
    print(tagsf)
    
    logging.basicConfig(filename=runlogfile,level=logging.DEBUG, filemode='w', datefmt='%Y-%m-%d %H:%M:%S')
    service = uploadraster.service()
    #look for files with .tif extension
    files = sorted([ f for f in os.listdir(_DIR) if os.path.isfile(os.path.join(_DIR,f)) and f[-4:]=='.tif'])


    tag1 = 'uploaded:%s:%s' % (_EMAIL,datetime.date.today())
    
    for f in files:
        
        #build up tags. Always include the automatic tag that the web ui creates (uploaded:ben.s.carlson@gmail.com:11/5/14)
        # plus the file name (minus the extension), 
        #plus any tags included in the _TAGS property, 
        #plus any tags supplied in an optional tagfile
        
        filename = f[:-4]
        tags = [tag1,filename] + _TAGS
        for t in tagsf:
            if t['filename'] == f:
                tags = tags + t['tags'].split(',')
        
        uploadsettings = {'name':filename,
                          'description': _DESCRIPTION,
                          'tags':tags,
                          'userAccessID': _USER_ACCESS_ID,
                          'apiWait':_WAIT}
        try:
            logging.info("Starting upload for %s" % f)
            #tags = uploaded:ben.s.carlson@gmail.com:11/5/14, env-annotate, worldclim_tmin_10min_01
            #upload the raster to maps engine
            result = uploadraster.upload(service, '%s/%s' % (_DIR,f), uploadsettings)
            
            if result['code'] == NOT_STARTED_CODE:
                msg = "%s: FAILURE: Not Started" % f
                #outputFile = NOT_STARTED_FILE
   
            elif result['code'] == CONTAINER_CODE:
                msg = "%s: PARTIAL FAILURE: Asset container created but file not uploaded" % f
                #move the file to a different folder so that it is easy to reprocess
                if not os.path.exists(_CONTAINER_FOLDER):
                    os.makedirs(_CONTAINER_FOLDER)
                shutil.move("%s/%s" % (_DIR,f), "%s/%s" % (_CONTAINER_FOLDER,f))
                #outputFile = CONTAINER_FILE
            elif result['code'] == PERMISSION_CODE:
                msg = "%s: PARTIAL FAILURE: File uploaded but permissions not set on asset" % f
                
            elif result['code'] == UPLOADED_CODE:
                msg = "%s: SUCCESS: Uploaded Successfully" % f
                #move the file to the "processed" folder
                if not os.path.exists(_UPLOADED_FOLDER):
                    os.makedirs(_UPLOADED_FOLDER)
                shutil.move("%s/%s" % (_DIR,f), "%s/%s" % (_UPLOADED_FOLDER,f))
                #outputFile = UPLOADED_FILE
            
            with open(eeidsfile, 'a') as csvfile:
                    writer = csv.writer(csvfile, delimiter=',',
                                        quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                    writer.writerow([filename,result['assetid']])
                    
            print(msg)
            logging.info(msg)
            
        except Exception:
            msg = "%s: Critical Error" % f
            print msg
            logging.error(msg)
            logging.error(sys.exc_info()[0])
            logging.error(traceback.format_exc())
    #end for
    
    msg = "Script Completed"
    print msg
    logging.info(msg)
    
if __name__ == '__main__':
    main(sys.argv)