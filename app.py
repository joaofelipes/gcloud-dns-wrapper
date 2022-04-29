from google.oauth2 import service_account
from googleapiclient import discovery
from operator import ne
from flask import Flask
from flask import request
from flask import jsonify
from pathlib import Path
import socket
import json

app = Flask(__name__)

@app.route('/')
def index():
  # Check secret
  secret = request.headers.getlist('Authorization') 
  authkey = 'nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQCLO0riZjt9vtYx'
  if len(secret) > 0 :
    if secret[0] == authkey:
      job = doit()
    else:
      return {'Message': 'Authoriazation failed'}   
  else:
    return {'Message': 'Authoriazation required'} 
  
  return job

def doit():
    # Set variables
    project_id="reliable-cairn-685"
    zone_name="joaofelipe"
    cred_file_path='C:\\MyGarbage\\WebProjects\\update-gcloud-dns\\sandbox\\gcloud.json' 

    # Get remote IP address
    if request.headers.getlist("X-Forwarded-For"):
       remoteip = request.headers.getlist("X-Forwarded-For")[0]
    else:
       remoteip = request.remote_addr
   
    # Set Credentials
    gcp_dns_credentials_txt = Path(cred_file_path).read_text()
    gcp_dns_credentials = json.loads(gcp_dns_credentials_txt) 
    credentials = service_account.Credentials.from_service_account_info(gcp_dns_credentials)
    service = discovery.build('dns', 'v1', credentials=credentials)

    # Get the current IP of the register
    # currentip = socket.gethostbyname('hass.joaofelipe.net') # does not work
    querydns = service.resourceRecordSets().list(project=project_id, managedZone=zone_name)
    dnsresponse = querydns.execute()
    for record in dnsresponse['rrsets']:   
      if record['name'] == 'hass.joaofelipe.net.':
        currentip = record['rrdatas'][0]

    # Set body to change
    change_body = {
        "deletions": [
            {
              "name": "hass.joaofelipe.net.",
              "type": "A",
              "ttl": 120,
              "rrdata": [currentip],
              "reason" : "update"
            }
        ],
        "additions": [
            {
        "name": "hass.joaofelipe.net.",
        "type": "A",
        "ttl": 120,
        "rrdata": [remoteip]
        }
    ]
    }

    # Execute request with the change and return response
    if remoteip != currentip :
      rrequest = service.changes().create(project=project_id, managedZone=zone_name, body=change_body)
      rresponse = rrequest.execute()
      return change_body
    else :
      return {"message": "Nothint to do. Records are the same."}

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)