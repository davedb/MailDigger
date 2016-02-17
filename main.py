from __future__ import print_function
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import base64
import re
from bs4 import BeautifulSoup
import json

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'MailDigger'


def get_credentials():
    '''Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    '''
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    #results = service.users().labels().list(userId='me').execute()
    results = service.users().messages().list(userId='me', q='bikemi').execute()
    messages = results.get('messages', [])
    #print(messages)

    if not messages:
        print('No messages found.')
    else:
        #print('messages:')
        dataToWriteKeys = (('pickUpDate', 'pickUpTime'),('pickUpStationId', 'pickUpStation'),('dropDate','dropTime'), ('dropStationId', 'dropStation'),'bikeType','usageTime','price','penalty','co2Saved','burnedCalories')
        dataToWrite = []
        for message in messages:
            messageId = message['id']
            print(messageId)#, service.users().messages().get(userId='me', id=messageId).execute())
            #if messageId == '152c0033f0e6ac3a':
            cMessage = service.users().messages().get(userId='me', id=messageId, format='full').execute()
            
            try:
                cMessageDataDecoded = base64.urlsafe_b64decode(cMessage['payload']['body']['data'])
            except KeyError:
                continue

            soup = BeautifulSoup(cMessageDataDecoded, 'html.parser')
            
            try:
                valuableData = soup.body.find_all(string=re.compile(': (\S+) ?-? ?(.+)?'))
            except AttributeError:
                continue

            print('handling..')
            prog = re.compile(': (\S+) ?-? ?(.+)?')
            i = 0
            singleTrip = {}
            for value in valuableData:
                #print(value, i)
                try:
                    #print(type(dataToWriteKeys[i]))
                    if(isinstance(dataToWriteKeys[i], tuple)):
                        singleTrip[dataToWriteKeys[i][0]] = prog.search(value).group(1);
                        singleTrip[dataToWriteKeys[i][1]] = prog.search(value).group(2);
                    else:
                        singleTrip[dataToWriteKeys[i]] = prog.search(value).group(1) + ' ' + prog.search(value).group(2);
                    i+= 1
                    #print('{0:<10} | {1:>10}'.format(prog.search(value).group(1),prog.search(value).group(2)))
                except TypeError:
                    singleTrip[dataToWriteKeys[i]] = prog.search(value).group(1)
                    i+= 1
                    #print('     ' + prog.search(value).group(1))
            dataToWrite.append(singleTrip)
            #return
        print(dataToWrite)
        f = open('outuput.json', 'w')
        json_data = json.dumps(dataToWrite)
        f.write(json_data)
        f.close()

    


if __name__ == '__main__':
    main()
