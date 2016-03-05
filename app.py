import datetime
import getpass
import os
import platform
import re
import sqlite3
import xml.etree.cElementTree as ET
import hashlib
import shutil

### I don't know of any elegant way to get the phone owners name. An input prompt is the only option right now ##

myFname = raw_input('Please enter your firstname and press enter: ')
mySname = raw_input('Please enter your Surname and press enter: ')



### Get the current users name ###
user = getpass.getuser()



### Check users platform to return the correct path to Itunes backup ###
if platform.system() == 'Darwin':
    backupPath = '/Users/'+user+'/Library/Application Support/MobileSync/Backup/'

elif platform.system() == 'Windows':
    if platform.release() =='XP':
        backupPath =''

    elif platform.release() =='Vista': # need to find the correct value for this
        backupPath =''

    elif platform.release() =='7': # need to find the correct value for this
        backupPath ='C:/Users/'+user+'/AppData/Roaming/Apple Computer/MobileSync/Backup'

    elif platform.release() =='8': # need to find the correct value for this
        backupPath =''

    elif platform.release() =='10': # need to find the correct value for this
        backupPath =''
else:
    print 'Sorry this program can only be runned under Osx or Windows'

### We need to keep track of number of dirs to make a user select list ###
count = 0
dictList = {}

### loop through the backupPath to find all backups find the most recent dates and print the result to user ###
print 'Found following backups :'
for dir in os.listdir(backupPath):
    ## Skips hidden files##
    if dir == '.DS_Store': # there might be more hidden files under windows to consider here
        pass
    else:
        count = count + 1 # Add a number to count
        dictList[count] = dir # Add the found backup to a dict with corresponding count number

        print count,':',(datetime.datetime.fromtimestamp(os.stat(backupPath+dir).st_ctime).strftime('%Y-%m-%d %H:%M:%S')), ':', dir # Print selection number, backup dirname and datetime

### User selection and checking that input is correct e.g. no alfabetic, and no numbers outside the dict ###
while True:
     backupChoice = raw_input('Please choose a backup number and press enter: ')
     try:
         backupChoice = int(backupChoice)
         if backupChoice <=0:
             print 'Bad input, please try again'
         elif backupChoice > count:
             print 'Bad input, please try again'
         else:
             break
     except:
         print 'Bad input, please try again'

with sqlite3.connect(backupPath+dictList[backupChoice]+'/3d0d7e5fb2ce288813306e4d4636395e047a3d28') as message_connection:
    mc = message_connection.cursor()

### Connect to the contacts database ###
t = []
with sqlite3.connect(backupPath+dictList[backupChoice]+'/31bb7ba8914766d4ba40d6dfb6113c8b614be442') as contacts_connection:
    cc = contacts_connection.cursor()
for row in cc.execute('''SELECT c0first, c1last, c15Phone FROM ABPersonFullTextSearch_content '''):
        # There is probably a much nicer less retarded way to do this...
        try:
            #first we need to convert tuples into a list (since the sql response comes in tuples and they are immutable)
            lst = list(row)
            # Next we're Using regex to extract just the +46707123456 formatted number from the c15Phone column (lst[2])
            # We use re.finditer because the c15Phone column is filled with all kinds of numbers and they are not seperated values j
            # just a bunch of text, one contact can however have multiple numbers e.g. one main, one work, one landline and we need to
            # get all of them.
            finder = re.finditer('\+([0-9]){11}', lst[2])
            for match in finder:
                # Update the list with just the +46707123456 formatted number.
                lst[2] = match.group(0)

                # Now its time to compare the regexed numbers against the available chats and add them to a new list
                for row in mc.execute('''SELECT ROWID, chat_identifier FROM chat'''):
                    lst2 = list(row)
                    if lst[2] == lst2[1]:
                        t.append(lst + lst2)
        except:
            pass
# Next we're going to clean up the list from duplicates that may appear in the list due to multiple records in the db
# Then user input to choose the chat to archive.
seen = set()
unique = []
for row in t:
        x = row[3],row[0], row[1]
        if x not in seen:
            unique.append(x)
            seen.add(x)
for row in unique:
    print row


chatIdChoice = str (input('Please choose chat number to archive: '))
### We need to fetch the firstname and surname from the list for use in the xml-export.
### Alot of looping going on, might just make some functions instead
for row in t:
    if str(row[3]) == chatIdChoice: # Find the chatIdchoice in the list
        extFname = row[0] #assign the found firstname to a variable
        extSname = row[1] #assign the found surname to a variable

### Create some outputfolders ###
if not os.path.exists(chatIdChoice):
    os.makedirs(chatIdChoice)
if not os.path.exists(chatIdChoice+'/content'):
    os.makedirs(chatIdChoice+'/content')
if not os.path.exists(chatIdChoice+'/content/attachments'):
    os.makedirs(chatIdChoice+'/content/attachments')
if not os.path.exists(chatIdChoice+'/system'):
    os.makedirs(chatIdChoice+'/system')
if not os.path.exists(chatIdChoice+'/metadata'):
    os.makedirs(chatIdChoice+'/metadata')

# It's time to query the messages db and construct the xml-export

xmlConversation = ET.Element('conversation') #Create the root-element <conversation>


for row in mc.execute('''SELECT
    CMJ.chat_id, M.guid, M.text, H.id, M.service, M.date, M.is_from_me, FILE.filename
FROM
    message  AS M
	LEFT JOIN
	message_attachment_join AS MAJ
	ON  M.ROWID = MAJ.message_id
   LEFT JOIN
    handle  AS H
      ON M.handle_id = H.ROWID
    LEFT  JOIN
	attachment as FILE
	ON MAJ.attachment_ID = FILE.ROWID
	LEFT  JOIN  chat_message_join AS CMJ
	on M.ROWID = CMJ.message_id
	WHERE CMJ.chat_id ='''+chatIdChoice+'''
	ORDER BY M.date'''):
    xmlConversation.set('id',str(row[0])) # Set the chatid as an attribute to <conversation>
    xmlMessage = ET.SubElement(xmlConversation,'message') # Create subelement <message>
    xmlDateTime = ET.SubElement(xmlMessage,'datetime') # Create subelement  <datetime>

    xmlFrom = ET.SubElement(xmlMessage,'from')
    xmlTo = ET.SubElement(xmlMessage,'to')
    if row[6] == 1:
        xmlFromFname = ET.SubElement(xmlFrom,'fname')
        xmlFromSname = ET.SubElement(xmlFrom,'sname')
        xmlToFname = ET.SubElement(xmlTo,'fname')
        xmlToSname = ET.SubElement(xmlTo,'sname')
        xmlFromFname.text = myFname
        xmlFromSname.text = mySname
        xmlToFname.text = extFname
        xmlToSname.text = extSname
    else:
        xmlFromFname = ET.SubElement(xmlFrom,'fname')
        xmlFromSname = ET.SubElement(xmlFrom,'sname')
        xmlToFname = ET.SubElement(xmlTo,'fname')
        xmlToSname = ET.SubElement(xmlTo,'sname')
        xmlFromFname.text = extFname
        xmlFromSname.text = extSname
        xmlToFname.text = myFname
        xmlToSname.text = mySname
    xmlMessage.set('id',row[1])
    xmlMessage.set('service',row[4])
    xmlText = ET.SubElement(xmlMessage,'text') # Create subelement  <text>
    xmlText.text = row[2]
    # We need to convert the cocoa timestamp to humanreadable time.
    # We add 978307200 seconds to go from unix epoch (1970-01-01T00:00:00) to cocoa epoch (2001-01-01T00:00:00)
    xmlDateTime.text = (datetime.datetime.fromtimestamp(row[5]+978307200).strftime('%Y-%m-%d %H:%M:%S')) # Add datetime to <datetime>
    ## If there's an attachment in the message we want to make a copy
    if row[7]:
        xmlAttachment = ET.SubElement(xmlMessage,'attachment') # Creates the attachment subelement
        hashSha = hashlib.sha1(row[7].replace('~/','MediaDomain-')) # change the string to the correct name before checksum calculation
        formatName = row[7].split(".",1)[1] # Fetch the right fileextentsion from filepath i database
        xmlAttachment.text = '/attachments/'+hashSha.hexdigest()+'.'+formatName # write the modified path/filename to the xml-export
        shutil.copy2(backupPath+dictList[backupChoice]+'/'+hashSha.hexdigest(),chatIdChoice+'/content/attachments/'+hashSha.hexdigest()+'.'+formatName)#Copy the attachment from backup to the archiving folder and add the correct file extenstion
###Write the XML to a file named after chat_id###
tree = ET.ElementTree(xmlConversation)
tree.write(chatIdChoice+'/content/'+chatIdChoice+'.xml', encoding='utf-8', xml_declaration=True)
#ET.dump(xmlConversation)

