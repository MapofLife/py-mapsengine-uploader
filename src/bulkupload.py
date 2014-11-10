#####################################################
# Uploads all tif files in a folder to maps engine
# Configure in settings.config
# Has some code to move completed files to other folders
# and smart restart capabitlies, but I've commented that functionality out for now
#####################################################

#TODO: write ee-id's to a file

import uploadraster
import sys
import logging
import os
import ConfigParser
import traceback
import datetime

Config = ConfigParser.ConfigParser()
#get run configurations
Config.read('settings.config')
_DIR = Config.get('Settings','RasterDirectory')
_TAGS = Config.get('Settings','Tags').split(",")
_EMAIL = Config.get('Settings','Email')
_DESCRIPTION = Config.get('Settings','Description')

NOT_STARTED_CODE = 0
CONTAINER_CODE = 1
UPLOADED_CODE = 2

def main(argv):
    
    logging.basicConfig(filename='logs/runlog.txt',level=logging.DEBUG, filemode='w', datefmt='%Y-%m-%d %H:%M:%S')
    service = uploadraster.service()
    #look for files with .tif extension
    files = [ f for f in os.listdir(_DIR) if os.path.isfile(os.path.join(_DIR,f)) and f[-4:]=='.tif']


    tag1 = 'uploaded:%s:%s' % (_EMAIL,datetime.date.today())
    
    for f in files:
        
        #build up tags. Always include the automatic tag that the web ui creates (uploaded:ben.s.carlson@gmail.com:11/5/14)
        # plus the file name (minus the extension), plus any tags included in the _TAGS property
        tags = [tag1,f[:-4]] + _TAGS

        uploadsettings = {'name':f[:-4],
                          'description': _DESCRIPTION,
                          'tags':tags}
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
                #shutil.move("%s/%s" % (TO_UPLOAD_FOLDER,f), "%s/%s" % (CONTAINER_FOLDER,f))
                #outputFile = CONTAINER_FILE
                
            elif result['code'] == UPLOADED_CODE:
                msg = "%s: SUCCESS: Uploaded Successfully" % f
                #move the file to the "processed" folder
                #shutil.move("%s/%s" % (TO_UPLOAD_FOLDER,f), "%s/%s" % (UPLOADED_FOLDER,f))
                #outputFile = UPLOADED_FILE
            
            #with open(outputFile, 'a') as csvfile:
            #        writer = csv.writer(csvfile, delimiter=',',
            #                            quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            #        writer.writerow([f,result['parkid'],result['assetid'],batchID]) 
                    
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