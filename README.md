# Cisco Secure Endpoint - Change group by OU
 
Config file must be in same folder as script, named cse_groupByOU.cfg and contain:

    [CSE]
    client_id = a1b2c3d4e5f6g7h8i9j0
    api_key = a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6

    # Cloud selection. Set to eu for European Union, apjc for Asia Pacific, Japan, and Greater China or leave empty for North America.
    # Example:
    # cloud = eu
    cloud = 

    # Email configuration
    recipient = name@somedomain
    sender_email = other.name@somedomain
    smtp_server = your.smtp.server

The file groups_and_OUs.txt need to be created in the same folder as the script and contain base DN and CSE Group guid separated by a colon, for example:
        OU=computers1,DC=corporation,DC=com:a1b2c3d4-1ab2-12a0-1234-1abcdefab123
        OU=computers2,DC=corporation,DC=com:b2c3d4e5-2bc3-23b1-2345-2bcdefabc234
