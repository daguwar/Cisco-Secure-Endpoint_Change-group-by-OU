from collections import namedtuple
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTPException
from ldap3 import Server, Connection, SUBTREE, LEVEL
import argparse
import configparser
import email
import json
import os
import requests
import smtplib
import sys
import time


"""def process_guid_json(guid_json):
    '''Process the individual GUID entry
    '''
    computer = namedtuple('computer', ['hostname', 'guid', 'age'])
    connector_guid = guid_json.get('connector_guid')
    hostname = guid_json.get('hostname')
    last_seen = guid_json.get('last_seen')
    return computer(hostname, connector_guid)

def get(session, url):
    '''HTTP GET the URL and return the decoded JSON
    '''
    response = session.get(url)
    response_json = response.json()
    return response_json"""

def send_report(recipient, sender_email, smtp_server):
    '''Send email with the created log files as attachments. Expects no authentication on smtp server.
    '''
    subject = 'CSE - Move to group by OU'
    body = 'Log files from script "cse_groupByOU.py"'
    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = subject
    #message["Bcc"] = receiver_email  # Recommended for mass emails

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    files = ['move-log.csv']

    for a_file in files:
        attachment = open(a_file, 'rb')
        part = MIMEBase('application','octet-stream')
        part.set_payload(attachment.read())
        part.add_header('Content-Disposition',
                    'attachment',
                    filename=a_file)
        encoders.encode_base64(part)
        message.attach(part)

    #sends email
    try:
        smtpObj = smtplib.SMTP(smtp_server)
        smtpObj.sendmail(sender_email, recipient, message.as_string())

    except SMTPException:
        pass

def get_ldap_connection(ldap_server, ldap_port, ldap_ssl, ldap_user, ldap_password):
    server = Server(ldap_server, port=int(ldap_port), use_ssl=ldap_ssl, get_info='ALL')
    connection = Connection(server, user=ldap_user, password=ldap_password,
               fast_decoder=True, auto_bind=True, auto_referrals=True, check_names=False, read_only=True,
               lazy=False, raise_exceptions=False)
    connection.starttls()

    return connection



def get_connectors_from_ou(conn, organizationalUnit):
    '''Grab computer names from OU with LDAPs and return tuple
    '''
    
def get_connectors_from_cse(connectors_from_ou, groupGuid, computers_url, auth):
    connectors = []
    for connector in connectors_from_ou:
        url = computers_url + f"?hostname={connector}"
        r = requests.get(url, auth=auth)
        j = json.loads(r.content)
        for item in j["data"]:
            hostname = item.get('hostname')
            guid = item.get('connector_guid')
            group = item.get('group_guid')
            if group != groupGuid:
                connectors.append((hostname, guid))
        # Adding a delay to prevent the API from being overwhelmed with requests
        time.sleep(1)
    return connectors

def move_to_group(connectors, groupGuid, computers_url, auth):
    '''Move connectors to group
    '''
    with open('move-log.csv', 'a', encoding='utf-8') as file_output:
        for connector in connectors:
            APICall = requests.session()
            APICall.auth = auth
            url = computers_url + f"{connector[1]}"
            headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/json"}
            payload = f"group_guid={groupGuid}"
            r = APICall.patch(url, data=payload, headers=headers)
            if r.status_code == 202:
                file_output.write('{},{},{},{},Success\n'.format(connector[0],
                                                      connector[1],
                                                      groupGuid,
                                                      r.status_code))
            else:
                file_output.write('{},{},{},{},Failure\n'.format(connector[0],
                                                      connector[1],
                                                      groupGuid,
                                                      r.status_code))
            # Adding a delay to prevent the API from being overwhelmed with requests
            time.sleep(1)



def main():
    '''The main logic of the script
    '''

    # Specify the config file
    config_file = 'cse_groupByOU.cfg'

    # Reading the config file to get settings
    config = configparser.RawConfigParser()
    config.read(config_file)
    client_id = config.get('CSE', 'client_id')
    api_key = config.get('CSE', 'api_key')
    cloud = config.get('CSE', 'cloud')
    recipient = config.get('EMAIL', 'recipient')
    sender_email = config.get('EMAIL', 'sender_email')
    smtp_server = config.get('EMAIL', 'smtp_server')
    ldap_server = config.get('LDAP', 'ldap_server')
    ldap_port = config.get('LDAP', 'ldap_port')
    ldap_ssl = config.get('LDAP', 'ldap_ssl')
    ldap_user = config.get('LDAP', 'ldap_user')
    ldap_password = config.get('LDAP', 'ldap_password')


    # Set auth
    auth = (client_id, api_key)

    # URL to query AMP
    if cloud == '':
        computers_url = 'https://api.amp.cisco.com/v1/computers/'
    else:
        computers_url = 'https://api.' + cloud + '.amp.cisco.com/v1/computers/'

    # Create log file and write headers.
    with open('move-log.csv', 'a', encoding='utf-8') as file_output:
        file_output.write('Hostname,GUID,Group Guid,Status code,Status')
    file_output.close()

    # Open file with OU and Group guid and call on functions to move computers for each line
    with open('groups_and_OUs.txt', 'r') as f:
        for line in f:
            organizationalUnit, groupGuid = line.split(':')
            conn = get_ldap_connection(ldap_server, ldap_port, ldap_ssl, ldap_user, ldap_password)
            connectors_from_ou = get_connectors_from_ou(conn, organizationalUnit)
            connectors = get_connectors_from_cse(connectors_from_ou, groupGuid, computers_url, auth)  
            move_to_group(connectors, groupGuid, computers_url, auth)

    send_report(recipient, sender_email, smtp_server) 

    # Cleanup
    os.remove('move-log.csv')

if __name__ == "__main__":
    main()
