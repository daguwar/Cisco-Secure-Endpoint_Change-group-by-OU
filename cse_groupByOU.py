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
import os
import requests
import smtplib
import sys

def should_move(clientgroup, wantedgroup):
    '''Check if client already member of wanted group
    '''
    if clientgroup == wantedgroup:
        return False
    return True

def process_guid_json(guid_json):
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
    return response_json

def send_report(recipient, sender_email, smtp_server):
    '''Send email with the created log files as attachments
    '''
    subject = 'Delete stale GUIDs report'
    body = 'Log files from script "delete_stale_guids.py"'
    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = subject
    #message["Bcc"] = receiver_email  # Recommended for mass emails

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    files = ['stale_guids.csv', 'deletion-log.txt']

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

def getConnectors(organizationalUnit):
    '''Grab computer names from OU with LDAPs and return tuple
    '''
    server = Server(ldap_server, port=int(ldap_port), use_ssl=ldap_ssl, get_info='ALL')
    connection = Connection(server, user="user1", password="Password123",
               fast_decoder=True, auto_bind=True, auto_referrals=True, check_names=False, read_only=True,
               lazy=False, raise_exceptions=False)

def main():
    '''The main logic of the script
    '''
    # Check arguments
    ## parser = argparse.ArgumentParser()
    ## parser

    # Specify the config file
    config_file = 'cse_groupByOU.cfg'

    # Reading the config file to get settings
    config = configparser.RawConfigParser()
    config.read(config_file)
    client_id = config.get('CSE', 'client_id')
    api_key = config.get('CSE', 'api_key')
    cloud = config.get('CSE', 'cloud')
    recipient = config.get('CSE', 'recipient')
    sender_email = config.get('CSE', 'sender_email')
    smtp_server = config.get('CSE', 'smtp_server')
    ldap_server = config.get('LDAP', 'ldap_server')

    # Instantiate requestions session object
    amp_session = requests.session()
    amp_session.auth = (client_id, api_key)

    # Set to store the computer tuples in
    computers_to_move = set()

    # URL to query AMP
    cloud = config.get('CSE', 'cloud')

    if cloud == '':
        computers_url = 'https://api.amp.cisco.com/v1/computers/'
    else:
        computers_url = 'https://api.' + cloud + '.amp.cisco.com/v1/computers/'

    # Open file with OU and Group guid and call on functions to move computers for each line
    with open('groups_and_OUs.txt', 'r') as f:
        for line in f:
            organizationalUnit, groupGuid = line.split(':')
            connectors = getConnectors(organizationalUnit)
            move_to_group(connectors, groupGuid)

    '''
    # Query the API
    response_json = get(amp_session, computers_url)

    # Process the returned JSON
    initial_batch = process_response_json(response_json, age_threshold)

    # Store the returned stale GUIDs
    computers_to_delete = computers_to_delete.union(initial_batch)

    # Check if there are more pages and repeat
    while 'next' in response_json['metadata']['links']:
        next_url = response_json['metadata']['links']['next']
        response_json = get(amp_session, next_url)
        next_batch = process_response_json(response_json, age_threshold)
        computers_to_delete = computers_to_delete.union(next_batch)

    if computers_to_delete:
        with open('stale_guids.csv', 'w', encoding='utf-8') as file_output:
            file_output.write('Age in days,GUID,Hostname\n')
            for computer in computers_to_delete:
                file_output.write('{},{},{}\n'.format(computer.age,
                                                      computer.guid,
                                                      computer.hostname))
        # Delete GUIDs
        for computer in computers_to_move:
            move_guid(amp_session, computer.guid, computer.hostname, computers_url)
    '''
    send_report(recipient, sender_email, smtp_server) 

    # Cleanup
    os.remove('stale_guids.csv')
    os.remove('deletion-log.txt')

if __name__ == "__main__":
    main()
