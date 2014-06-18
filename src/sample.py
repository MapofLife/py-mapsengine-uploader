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

from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools

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


def main(argv):
    # Parse the command-line flags.
    flags = parser.parse_args(argv[1:])
    
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

    raster_files = [
        "wdpa_test_raster1.tif",
        "wdpa_test_raster2.tif",
        "wdpa_test_raster3.tif"
    ]

    filenames = []
    for name in raster_files:
        filenames.append({
            "filename": "%s" % name
        })
    
    fileupload = {
        "projectId": "04040405428907908306",
        "name": "Test API Upload - Name",
        "description": "Test API Upload - Description",
        "files": filenames,
#         "acquisitionTime": {
#                             "start": "%s" % datetime.datetime.utcnow(),
#                             "end": "%s" % datetime.datetime.utcnow(),
#                             "precision": "second"
#                             },
        "draftAccessList": "Map Editors",
        "attribution": "Copyright MAP OF LIFE",
        "tags": ["testAPIUpload"],
        "maskType": "autoMask",
        "rasterType": "image"
    }
    print fileupload
    try:
        print "Success! Now add code here."
        #features = service.tables().features()
        rasters = service.rasters()
#         request = rasters.get(id='04040405428907908306-08561054050764735577')
#         while request is not None:
#             response = request.execute()
#             print response
            #for raster in response['features']:
            #    print raster
        request = rasters.upload(body=fileupload)
        response = request.execute()
        print response
        try:
            rasterUploadId = str(response['id'])

            print "Upload raster id %s" % rasterUploadId

            for name in raster_files:
                print "Waiting for 2 seconds"
                time.sleep(2)

                try:
                    print "Setting up insert request"
                    freq = rasters.files().insert(id=rasterUploadId,
                                                  filename=name,
                                                  media_body=name)
                    print "Calling insert request"
                    freq.execute()
                    print "Finished uploading %s" % name
                except Exception:
                    print "Unable to insert '%s'" % name

        except KeyError:
            print "Error uploading raster files"
            print response


        # now let's add the above dataset to a layer
        print "Adding data source to a layer"
        try:
            layercreate = {
                "projectId": "04040405428907908306",
                "id": "04040405428907908306-04203364926419794261",
                "name": "Test API Layer - name",
                "description": "Test API Layer - Description",
                "datasourceType": "image",
                "draftAccessList": "Map Editors",
                "datasources": [{
                    "id": "%s" % rasterUploadId
                }]
            }
            layers = service.layers()
            lreq = layers.create(body=layercreate, process=True)
            lres = lreq.execute()
            print lres
        except Exception, ex:
            print "Error adding data source to a new layer"
            print ex

        # Is there an additional page of features to load?
        #request = features.list_next(request, response)
    
    except client.AccessTokenRefreshError:
        print ("The credentials have been revoked or expired, please re-run"
          "the application to re-authorize")


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