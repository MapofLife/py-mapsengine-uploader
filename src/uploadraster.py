# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Command-line skeleton application for Google Maps Engine API.
Usage:
  $ python sample.py

You can also get help on all the command-line flags the program understands
by running:

  $ python sample.py --help

"""

import argparse
import httplib2
import os
import sys
import datetime
import time
import traceback
import logging
import shutil
import csv

from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools
from os import listdir
from os.path import isfile, join

######
# Maps Engine Status
# Uploading: means the container has been created, but the upload of the image failed
# Processing: search for status "Is ready to process" and "Is being processed" will return images with this status
# Image was Processed: search for "Was processed" will return images with this status
######

# Parser for command-line arguments.
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[tools.argparser])

# CLIENT_SECRETS is name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret. You can see the Client ID
# and Client secret on the APIs page in the Cloud Console:
# <https://cloud.google.com/console#/project/206753940765/apiui>
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

# Set up a Flow object to be used for authentication.
# Add one or more of the following scopes. PLEASE ONLY ADD THE SCOPES YOU
# NEED. For more information on using scopes please see
# <https://developers.google.com/+/best-practices>.
FLOW = client.flow_from_clientsecrets(CLIENT_SECRETS,
                                      scope=['https://www.googleapis.com/auth/mapsengine'],
                                      message=tools.message_if_missing(CLIENT_SECRETS))
DATA_FOLDER = "files"
TO_UPLOAD_FOLDER = DATA_FOLDER + "/to_upload"
CONTAINER_FOLDER = DATA_FOLDER + "/container_created"
UPLOADED_FOLDER = DATA_FOLDER + "/uploaded"
OUTPUT = "output"
NOT_STARTED_CODE = 0
CONTAINER_CODE = 1
UPLOADED_CODE = 2
NOT_STARTED_FILE = OUTPUT + "/" + "not_started.csv"
CONTAINER_FILE = OUTPUT + "/" + "container.csv"
UPLOADED_FILE = OUTPUT + "/" + "uploaded.csv"
WAIT = 4 #number of seconds to wait before any api call

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%Hh%Mm')
batchID = "batchID_" + st

def upload(filename, service):
    #file name is always prefixed with: wdpa2014_id and then the park id    
    parkID = os.path.splitext(filename)[0][11:]
    
    ret = {'code': NOT_STARTED_CODE,
           'assetid': None,
           'parkid': parkID}
    
    path = "%s/%s" % (TO_UPLOAD_FOLDER,filename)    

    fileupload = {
        "projectId": "04040405428907908306",
        "name": os.path.splitext(filename)[0],
        "description": "WDPA 2014 Rasterization",
        "files": [{"filename": filename}],
        "draftAccessList": "Map Editors",
        "attribution": "Copyright MAP OF LIFE",
        "tags": ["WDPA_2014_API_Upload",batchID,parkID], #,"testAPI" # add this tag when testing
        "maskType": "autoMask",
        "rasterType": "image"
    }

    #tags: testAPI, testAPI1000
    rasters = service.rasters()        
    request = rasters.upload(body=fileupload)
    
    try:
        time.sleep(WAIT) #need to wait  due to api rate limits
        response = request.execute() #create the skeleton container, which we'll upload the tif file to
        rasterUploadId = str(response['id'])
        
        ret['code'] = CONTAINER_CODE
        ret['assetid'] = rasterUploadId
             
        logging.info("%s: PARTIAL SUCCESS: Finished creating asset container. Asset id is %s" % (filename,rasterUploadId))        

        try:
            freq = rasters.files().insert(id=rasterUploadId,
                                          filename=filename,
                                          media_body=path)
            time.sleep(WAIT) #need to wait  due to api rate limits
            freq.execute()
            logging.info("%s: SUCCESS: Finished uploading" % filename)
            ret['code'] = UPLOADED_CODE
            
        except Exception:
            logging.error("%s: FAILURE: Error uploading" % filename)
            logging.error(sys.exc_info()[0])
            logging.error(traceback.format_exc())
            return ret

    except KeyError:
        logging.error("%s: FAILURE: Error creating asset container files" % filename)
        logging.error(response)
        logging.error(sys.exc_info()[0])
        logging.error(traceback.format_exc())
        return ret
    
    except client.AccessTokenRefreshError:
        logging.error("The credentials have been revoked or expired, please re-run"
          "the application to re-authorize")
        logging.error(sys.exc_info()[0])
        logging.error(traceback.format_exc())
        return ret
           
    return ret
#end upload function

def main(argv):
    # Parse the command-line flags.
    flags = parser.parse_args(argv[1:])
    
    logging.basicConfig(filename='logs/runlog.txt',level=logging.DEBUG, filemode='w', datefmt='%Y-%m-%d %H:%M:%S')
    
    #clear the contents of output files
    #open(NOT_STARTED_FILE, 'w').close()
    #open(CONTAINER_FILE,'w').close()
    #open(UPLOADED_FILE,'w').close()
    
    # If the credentials don't exist or are invalid run through the native client
    # flow. The Storage object will ensure that if successful the good
    # credentials will get written back to the file.
    storage = file.Storage('sample.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(FLOW, storage, flags)
    
    # Create an httplib2.Http object to handle our HTTP requests and authorize it
    # with our good Credentials.
    http = httplib2.Http()
    http = credentials.authorize(http)
    
    # Construct the service object for the interacting with the Google Maps Engine API.
    service = discovery.build('mapsengine', 'v1', http=http)

    #files = ["wdpa2014_id4336.tif"]
    files = [ f for f in listdir(TO_UPLOAD_FOLDER) if isfile(join(TO_UPLOAD_FOLDER,f)) ]
    
    for f in files:
        try:
            logging.info("Starting upload for %s" % f)
            result = upload(f,service)
            
            if result['code'] == NOT_STARTED_CODE:
                msg = "%s: FAILURE: Not Started" % f
                outputFile = NOT_STARTED_FILE
   
            elif result['code'] == CONTAINER_CODE:
                msg = "%s: PARTIAL FAILURE: Asset container created but file not uploaded" % f
                #move the file to a different folder so that it is easy to reprocess
                shutil.move("%s/%s" % (TO_UPLOAD_FOLDER,f), "%s/%s" % (CONTAINER_FOLDER,f))
                outputFile = CONTAINER_FILE
                
            elif result['code'] == UPLOADED_CODE:
                msg = "%s: SUCCESS: Uploaded Successfully" % f
                #move the file to the "processed" folder
                shutil.move("%s/%s" % (TO_UPLOAD_FOLDER,f), "%s/%s" % (UPLOADED_FOLDER,f))
                outputFile = UPLOADED_FILE
            
            with open(outputFile, 'a') as csvfile:
                    writer = csv.writer(csvfile, delimiter=',',
                                        quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                    writer.writerow([f,result['parkid'],result['assetid'],batchID]) 
                    
            print(msg)
            logging.info(msg)
            
        except:
            msg = "%s: Critical Error" % f
            print msg
            logging.error(msg)
            logging.error(sys.exc_info()[0])
            logging.error(traceback.format_exc())
    #end for
    
    msg = "Script Completed"
    print msg
    logging.info(msg)
# end main function

# For more information on the Google Maps Engine API you can visit:
#
#   https://developers.google.com/maps-engine/
#
# For more information on the Google Maps Engine API Python library surface you
# can visit:
#
#   https://developers.google.com/resources/api-libraries/documentation/mapsengine/v1/python/latest/
#
# For information on the Python Client Library visit:
#
#   https://developers.google.com/api-client-library/python/start/get_started
if __name__ == '__main__':
    main(sys.argv)

####### old code ########
        # now let's add the above dataset to a layer
#         print "Adding data source to a layer"
#         try:
#             layercreate = {
#                 "projectId": "04040405428907908306",
#                 "id": "04040405428907908306-04203364926419794261",
#                 "name": "Test API Layer - name",
#                 "description": "Test API Layer - Description",
#                 "datasourceType": "image",
#                 "draftAccessList": "Map Editors",
#                 "datasources": [{
#                     "id": "%s" % rasterUploadId
#                 }]
#             }
#             layers = service.layers()
#             lreq = layers.create(body=layercreate, process=True)
#             lres = lreq.execute()
#             print lres
#         except Exception, ex:
#             print "Error adding data source to a new layer"
#             print ex

        # Is there an additional page of features to load?
        #request = features.list_next(request, response)
        
