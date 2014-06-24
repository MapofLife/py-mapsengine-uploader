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
PROCESSED = "processed"
OUTPUT = "output"

def upload(filename, service):
    time.sleep(1)
    path = "%s/%s" % (DATA_FOLDER,filename)
    #file name is always prefixed with: wdpa2014_id and then the park id
    parkID = os.path.splitext(filename)[0][11:]

    fileupload = {
        "projectId": "04040405428907908306",
        "name": os.path.splitext(filename)[0],
        "description": "WDPA 2014 Rasterization",
        "files": [{"filename": filename}],
        "draftAccessList": "Map Editors",
        "attribution": "Copyright MAP OF LIFE",
        "tags": ["WDPA_2014_API_Upload","batch_2132-20000",parkID],
        "maskType": "autoMask",
        "rasterType": "image"
    }

    #tags: testAPI, testAPI1000
    
    try:

        rasters = service.rasters()
        #create the skeleton container, which we'll upload the tif file to
        request = rasters.upload(body=fileupload)
        response = request.execute()

        try:
            rasterUploadId = str(response['id'])
            
            logging.info("Upload raster id %s" % rasterUploadId)

            time.sleep(1)

            try:
                freq = rasters.files().insert(id=rasterUploadId,
                                              filename=filename,
                                              media_body=path)
                freq.execute()
                logging.info("Finished uploading %s" % filename)
            except Exception:
                logging.error("Unable to insert '%s'" % filename)
                logging.error(sys.exc_info()[0])
                logging.error(traceback.format_exc())
                return False

        except KeyError:
            logging.error("Error uploading raster files")
            logging.error(response)
            return False
    
    except client.AccessTokenRefreshError:
        logging.error("The credentials have been revoked or expired, please re-run"
          "the application to re-authorize")
        return False
    
    #write out this rasterID to a file, this should be the EE id.  also include the park id
    with open('%s/uploaded.csv' % OUTPUT, 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow([filename,parkID,rasterUploadId])
        
    return True
#end upload function

def main(argv):
    # Parse the command-line flags.
    flags = parser.parse_args(argv[1:])
    
    logging.basicConfig(filename='logs/runlog.txt',level=logging.DEBUG, filemode='w', datefmt='%Y-%m-%d %H:%M:%S')
    
    #clear the contents of output files
    open('%s/retry.txt' % OUTPUT, 'w').close()
    open('%s/uploaded.csv' % OUTPUT,'w').close()
    
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
    files = [ f for f in listdir(DATA_FOLDER) if isfile(join(DATA_FOLDER,f)) ]
    
    for f in files:
        try:
            logging.info("Starting upload for %s" % f)
            success = upload(f,service)
            if success:
                msg = "SUCCESS: %s" % f
                print(msg)
                logging.info(msg)
                #move the file to the "processed" folder
                shutil.move("%s/%s" % (DATA_FOLDER,f), "%s/%s/%s" % (DATA_FOLDER,PROCESSED,f))
            else:
                msg = "FAILURE: %s" % f
                print(msg)
                logging.error(msg)
                with open("%s/retry.txt" % OUTPUT, "a") as myfile:
                    myfile.write(f)
        except:
            logging.error("Critical Error %s" % f)

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
        