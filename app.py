# -*- coding: UTF-8 -*-
import bagit
import datetime
import getpass
import os
import platform
import re
import sqlite3
import tarfile
import xml.etree.cElementTree as ET
import hashlib
import shutil
import uuid
import sys
conversationUUID = str(uuid.uuid4()) # create a UUID; used as id for conversation
xmlUUID = str(uuid.uuid4()) # create a UUID; used for naming xml-file and PREMIS objectIdentifierValue (xml-file)
xsdUUID = str(uuid.uuid4()) # create a UUID; used for PREMIS objectIdentifierValue (xsd-file)
xslUUID = str(uuid.uuid4()) # create a UUID; used for PREMIS objectIdentifierValue (xsl-file)
eventUUID = str(uuid.uuid4()) # create a UUID; used for giving Event a uuid


### I don't know of any elegant way to get the phone owners name. An input prompt is the only option right now ##
myFname = raw_input('Please enter phone owners firstname and press enter: ')
mySname = raw_input('Please enter phone owners surname and press enter: ')
myFname = myFname.decode('utf-8')
mySname = mySname.decode('utf-8')

yes = set(['yes','y', 'ye', ''])
no = set(['no','n'])

while True:
    try:
        choice = raw_input('Is phone owner and operator the same person? ("y" or "n"): ')
        if choice in yes:
             operatorAgentFName = myFname
             operatorAgentSName = mySname
             break
        elif choice in no:
            operatorAgentFName = raw_input('Please enter operators firstname and press enter: ')
            operatorAgentSName = raw_input('Please enter operators Surname and press enter: ')
            break
        else:
            sys.stdout.write('Please respond with "yes" or "no")\n')
    except:
        pass

timeStamp = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%H:%M:%S') # Get the current datetimestamp for use as PREMIS-metadata


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

    elif platform.release() =='7':
        backupPath ='C:/Users/'+user+'/AppData/Roaming/Apple Computer/MobileSync/Backup' # Need to confirm this is the correct path

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
###Give user option to create an alias if a contact-name is not formatted right###
print 'Do you want to use "'+extFname+' '+extSname+'" as naming for contact '

while True:
    try:
        choice = raw_input('("y" or "n"): ')
        if choice in yes:
             extFname = extFname
             extSname = extSname
             break
        elif choice in no:
            extSname = raw_input('Please enter contact firstname and press enter: ')
            extSname = raw_input('Please enter contact Surname and press enter: ')
            break
        else:
            sys.stdout.write('Please respond with "yes" or "no")\n')
    except:
        pass

### Create some outputfolders ###
rootPath = extSname+'_'+extFname+'_'+chatIdChoice+'_UUID_'+conversationUUID
if not os.path.exists(rootPath):
    os.makedirs(rootPath)
if not os.path.exists(rootPath+'/content'):
    os.makedirs(rootPath+'/content')
if not os.path.exists(rootPath+'/content/attachments'):
    os.makedirs(rootPath+'/content/attachments')
if not os.path.exists(rootPath+'/system'):
    os.makedirs(rootPath+'/system')
if not os.path.exists(rootPath+'/metadata'):
    os.makedirs(rootPath+'/metadata')

xmlConversation = ET.Element('conversation') #Create the root element <conversation>

###Create the PREMIS intellectualEntity e.g. this application###
premis = ET.Element('premis') #Create the root element premis
premis.set('xmlns:xlink','http://www.w3.org/1999/xlink')
premis.set('xmlns:xsi','http://www.w3.org/2001/XMLSchema-instance')
premis.set('xmlns','http://www.loc.gov/premis/v3')
premis.set('xsi:schemaLocation','info:lc/xmlns/premis-v3 http://www.loc.gov/standards/premis/premis.xsd')
premis.set('version','3.0')
premisObject = ET.SubElement(premis,'object')
premisObject.set('xsi:type','intellectualEntity')
premisObjectIdentfier = ET.SubElement(premisObject,'objectIdentifier')
premisObjectIdentfierType = ET.SubElement(premisObjectIdentfier,'objectIdentifierType')
premisObjectIdentfierType.text = 'local'
premisObjectIdentfierValue = ET.SubElement(premisObjectIdentfier,'objectIdentifierValue')
premisObjectIdentfierValue.text = '1'
premisObjectEnvironmentFunction = ET.SubElement(premisObject,'environmentFunction')
premisObjectEnvironmentFunctionEnvironmentFunctionType = ET.SubElement(premisObjectEnvironmentFunction,'environmentFunctionType')
premisObjectEnvironmentFunctionEnvironmentFunctionType.text = 'software application'
premisObjectEnvironmentFunctionEnvironmentFunctionLevel = ET.SubElement(premisObjectEnvironmentFunction,'environmentFunctionLevel')
premisObjectEnvironmentFunctionEnvironmentFunctionLevel.text = '2'
premisObjectEnvironmentDesignation = ET.SubElement(premisObject,'environmentDesignation')
premisObjectEnvironmentDesignationEnvironmentName = ET.SubElement(premisObjectEnvironmentDesignation,'environmentName')
premisObjectEnvironmentDesignationEnvironmentName.text = 'iphone-sms-archiver'
premisObjectEnvironmentDesignationEnvironmentVersion = ET.SubElement(premisObjectEnvironmentDesignation,'environmentVersion')
premisObjectEnvironmentDesignationEnvironmentVersion.text ='1.0'
premisObjectEnvironmentDesignationEnvironmentOrigin = ET.SubElement(premisObjectEnvironmentDesignation,'environmentOrigin')
premisObjectEnvironmentDesignationEnvironmentOrigin.text = 'Andreas Segerberg'
premisObjectRelationship = ET.SubElement(premisObject,'relationship')
premisObjectRelationshipRelationshipType = ET.SubElement(premisObjectRelationship,'relationshipType')
premisObjectRelationshipRelationshipType.text = 'reference'
premisObjectRelationshipRelationshipSubType = ET.SubElement(premisObjectRelationship,'relationshipSubType')
premisObjectRelationshipRelationshipSubType.text = 'is documented in'
premisObjectRelationshipRelatedObjectIdentifier = ET.SubElement(premisObjectRelationship,'relatedObjectIdentifier')
premisObjectRelationshipRelatedObjectIdentifierRelatedObjectIdentifierType = ET.SubElement(premisObjectRelationshipRelatedObjectIdentifier,'relatedObjectIdentifierType')
premisObjectRelationshipRelatedObjectIdentifierRelatedObjectIdentifierType.text = 'URL'
premisObjectRelationshipRelatedObjectIdentifierRelatedObjectIdentifierValue = ET.SubElement(premisObjectRelationshipRelatedObjectIdentifier,'relatedObjectIdentifierValue')
premisObjectRelationshipRelatedObjectIdentifierRelatedObjectIdentifierValue.text = 'https://github.com/Segerberg/iphone-sms-archiver'

first = True
last = None
# It's time to query the messages db and construct the xml-export
for row in mc.execute('''SELECT
    CMJ.chat_id, M.guid, M.text, H.id, M.service, M.date, M.is_from_me, FILE.filename, FILE.mime_type
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
    xmlConversation.set('id', conversationUUID) # Give the conversation  a UUID
    xmlConversation.set('chatId',str(row[0])) # Set the chatid as an attribute to <conversation>
    xmlConversation.set('xmlns:xsi','http://www.w3.org/2001/XMLSchema-instance')
    xmlConversation.set('xsi:noNamespaceSchemaLocation','../system/schema.xsd')

    xmlMessage = ET.SubElement(xmlConversation,'message') # Create subelement <message>
    xmlDateTime = ET.SubElement(xmlMessage,'datetime') # Create subelement  <datetime>

    xmlFrom = ET.SubElement(xmlMessage,'from')
    xmlTo = ET.SubElement(xmlMessage,'to')

    ###Handles the direction the message is sent###
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
    xmlMessage.set('isFromMe',str(row[6]))
    xmlText = ET.SubElement(xmlMessage,'text') # Create subelement  <text>
    xmlText.text = row[2]
    # We need to convert the cocoa timestamp to humanreadable time.
    # We add 978307200 seconds to go from unix epoch (1970-01-01T00:00:00) to cocoa epoch (2001-01-01T00:00:00)
    xmlDateTime.text = (datetime.datetime.fromtimestamp(row[5]+978307200).strftime('%Y-%m-%d %H:%M:%S')) # Add datetime to <datetime>
    ### We also want fetch the first message date (and the last later###
    if first:
        firstDate = datetime.datetime.fromtimestamp(row[5]+978307200).strftime('%Y-%m-%d')
        first = False
    if last is not None:
        pass
    lastDate = datetime.datetime.fromtimestamp(row[5]+978307200).strftime('%Y-%m-%d')

    ## If there's an attachment in the message we want to make a copy
    if row[7]:
        xmlAttachment = ET.SubElement(xmlMessage,'attachment') # Creates the attachment subelement
        hashSha = hashlib.sha1(row[7].replace('~/','MediaDomain-')) # change the string to the correct name before checksum calculation
        formatName = row[7].split(".",1)[1] # Fetch the right fileextentsion from filepath i database
        xmlAttachment.set ('file',hashSha.hexdigest()+'.'+formatName) # write the modified path/filename to the xml-export
        shutil.copy2(backupPath+dictList[backupChoice]+'/'+hashSha.hexdigest(),rootPath+'/content/attachments/'+hashSha.hexdigest()+'.'+formatName)#Copy the attachment from backup to the archiving folder and add the correct file extenstion

        ###Create a PREMIS file object for every attachment###
        premisObject = ET.SubElement(premis,'object')
        premisObject.set('xsi:type','file')
        premisObjectIdentfier = ET.SubElement(premisObject,'objectIdentifier')
        premisObjectIdentfierType = ET.SubElement(premisObjectIdentfier,'objectIdentifierType')
        premisObjectIdentfierType.text = 'sha-1'
        premisObjectIdentfierValue = ET.SubElement(premisObjectIdentfier,'objectIdentifierValue')
        premisObjectIdentfierValue.text = hashSha.hexdigest()
        premisObjectObjectCharacteristics = ET.SubElement(premisObject,'objectCharacteristics')
        premisObjectObjectCharacteristicsCompositionLevel = ET.SubElement(premisObjectObjectCharacteristics,'compositionLevel')
        premisObjectObjectCharacteristicsCompositionLevel.text = '0'
        premisObjectObjectCharacteristicsFixity = ET.SubElement(premisObjectObjectCharacteristics,'fixity')
        premisObjectObjectCharacteristicsFixityMessageDigestAlgorithm = ET.SubElement(premisObjectObjectCharacteristicsFixity,'messageDigestAlgorithm')
        premisObjectObjectCharacteristicsFixityMessageDigestAlgorithm.text = 'md5'
        premisObjectObjectCharacteristicsFixityMessageDigest = ET.SubElement(premisObjectObjectCharacteristicsFixity,'messageDigest')
        premisObjectObjectCharacteristicsFixityMessageDigest.text = hashlib.md5(open(rootPath+'/content/attachments/'+hashSha.hexdigest()+'.'+formatName,'rb').read()).hexdigest()
        premisObjectObjectCharacteristicsSize = ET.SubElement(premisObjectObjectCharacteristics,'size')
        premisObjectObjectCharacteristicsSize.text = str(os.path.getsize(rootPath+'/content/attachments/'+hashSha.hexdigest()+'.'+formatName))
        premisObjectObjectCharacteristicsFormat = ET.SubElement(premisObjectObjectCharacteristics,'format')
        premisObjectObjectCharacteristicsFormatFormatDesignation= ET.SubElement(premisObjectObjectCharacteristicsFormat,'formatDesignation')
        premisObjectObjectCharacteristicsFormatFormatDesignationFormatName = ET.SubElement(premisObjectObjectCharacteristicsFormatFormatDesignation,'formatName')
        premisObjectObjectCharacteristicsFormatFormatDesignationFormatName.text = row[8]
        premisObjectObjectCharacteristicsCreatingApplication = ET.SubElement(premisObjectObjectCharacteristics,'creatingApplication')
        premisObjectObjectCharacteristicsCreatingApplicationDate = ET.SubElement(premisObjectObjectCharacteristicsCreatingApplication,'dateCreatedByApplication')
        premisObjectObjectCharacteristicsCreatingApplicationDate.text = 'unknowed'
        premisLinkingEventIdentifier = ET.SubElement(premisObject,'linkingEventIdentifier')
        premisLinkingEventIdentifierLinkingEventIdentifierType = ET.SubElement(premisLinkingEventIdentifier,'linkingEventIdentifierType')
        premisLinkingEventIdentifierLinkingEventIdentifierType.text = 'uuid'
        premisLinkingEventIdentifierLinkingEventIdentifierValue = ET.SubElement(premisLinkingEventIdentifier,'linkingEventIdentifierValue')
        premisLinkingEventIdentifierLinkingEventIdentifierValue.text = eventUUID

###Write the XML to a file named after chat_id###
tree = ET.ElementTree(xmlConversation)
tree.write(rootPath+'/content/'+xmlUUID+'.xml', encoding='utf-8', xml_declaration=False)

###We need to insert reference to the xslt###
with open(rootPath+'/content/'+xmlUUID+'.xml', "r+") as f:
     firstXml = f.read() # read everything in the xml-file
     f.seek(0) # Find the first line
     f.write('''<?xml version='1.0' encoding='utf-8'?>\n<?xml-stylesheet type="text/xsl" href="../system/style.xsl"?>\n'''+ firstXml) # insert the xml-declaration, xslt path and then the rest of the data

#####Make a copy of the xslt and xsd to the SIP ###
shutil.copy2('style.xsl',rootPath+'/system/style.xsl')
shutil.copy2('schema.xsd',rootPath+'/system/schema.xsd')

### Create a PREMIS file object for the XSD-file ###
premisObject = ET.SubElement(premis,'object')
premisObject.set('xsi:type','file')
premisObjectIdentfier = ET.SubElement(premisObject,'objectIdentifier')
premisObjectIdentfierType = ET.SubElement(premisObjectIdentfier,'objectIdentifierType')
premisObjectIdentfierType.text = 'uuid'
premisObjectIdentfierValue = ET.SubElement(premisObjectIdentfier,'objectIdentifierValue')
premisObjectIdentfierValue.text = xsdUUID
premisObjectObjectCharacteristics = ET.SubElement(premisObject,'objectCharacteristics')
premisObjectObjectCharacteristicsCompositionLevel = ET.SubElement(premisObjectObjectCharacteristics,'compositionLevel')
premisObjectObjectCharacteristicsCompositionLevel.text = '0'
premisObjectObjectCharacteristicsFixity = ET.SubElement(premisObjectObjectCharacteristics,'fixity')
premisObjectObjectCharacteristicsFixityMessageDigestAlgorithm = ET.SubElement(premisObjectObjectCharacteristicsFixity,'messageDigestAlgorithm')
premisObjectObjectCharacteristicsFixityMessageDigestAlgorithm.text = 'md5'
premisObjectObjectCharacteristicsFixityMessageDigest = ET.SubElement(premisObjectObjectCharacteristicsFixity,'messageDigest')
premisObjectObjectCharacteristicsFixityMessageDigest.text = hashlib.md5(open(rootPath+'/system/schema.xsd','rb').read()).hexdigest()
premisObjectObjectCharacteristicsSize = ET.SubElement(premisObjectObjectCharacteristics,'size')
premisObjectObjectCharacteristicsSize.text = str(os.path.getsize(rootPath+'/system/schema.xsd'))
premisObjectObjectCharacteristicsFormat = ET.SubElement(premisObjectObjectCharacteristics,'format')
premisObjectObjectCharacteristicsFormatFormatDesignation= ET.SubElement(premisObjectObjectCharacteristicsFormat,'formatDesignation')
premisObjectObjectCharacteristicsFormatFormatDesignationFormatName = ET.SubElement(premisObjectObjectCharacteristicsFormatFormatDesignation,'formatName')
premisObjectObjectCharacteristicsFormatFormatDesignationFormatName.text = 'text/xml'
premisLinkingEventIdentifier = ET.SubElement(premisObject,'linkingEventIdentifier')
premisLinkingEventIdentifierLinkingEventIdentifierType = ET.SubElement(premisLinkingEventIdentifier,'linkingEventIdentifierType')
premisLinkingEventIdentifierLinkingEventIdentifierType.text = 'uuid'
premisLinkingEventIdentifierLinkingEventIdentifierValue = ET.SubElement(premisLinkingEventIdentifier,'linkingEventIdentifierValue')
premisLinkingEventIdentifierLinkingEventIdentifierValue.text = eventUUID

### Create a PREMIS file object for the XSL-file ###
premisObject = ET.SubElement(premis,'object')
premisObject.set('xsi:type','file')
premisObjectIdentfier = ET.SubElement(premisObject,'objectIdentifier')
premisObjectIdentfierType = ET.SubElement(premisObjectIdentfier,'objectIdentifierType')
premisObjectIdentfierType.text = 'uuid'
premisObjectIdentfierValue = ET.SubElement(premisObjectIdentfier,'objectIdentifierValue')
premisObjectIdentfierValue.text = xslUUID
premisObjectObjectCharacteristics = ET.SubElement(premisObject,'objectCharacteristics')
premisObjectObjectCharacteristicsCompositionLevel = ET.SubElement(premisObjectObjectCharacteristics,'compositionLevel')
premisObjectObjectCharacteristicsCompositionLevel.text = '0'
premisObjectObjectCharacteristicsFixity = ET.SubElement(premisObjectObjectCharacteristics,'fixity')
premisObjectObjectCharacteristicsFixityMessageDigestAlgorithm = ET.SubElement(premisObjectObjectCharacteristicsFixity,'messageDigestAlgorithm')
premisObjectObjectCharacteristicsFixityMessageDigestAlgorithm.text = 'md5'
premisObjectObjectCharacteristicsFixityMessageDigest = ET.SubElement(premisObjectObjectCharacteristicsFixity,'messageDigest')
premisObjectObjectCharacteristicsFixityMessageDigest.text = hashlib.md5(open(rootPath+'/system/style.xsl','rb').read()).hexdigest()
premisObjectObjectCharacteristicsSize = ET.SubElement(premisObjectObjectCharacteristics,'size')
premisObjectObjectCharacteristicsSize.text = str(os.path.getsize(rootPath+'/system/style.xsl'))
premisObjectObjectCharacteristicsFormat = ET.SubElement(premisObjectObjectCharacteristics,'format')
premisObjectObjectCharacteristicsFormatFormatDesignation= ET.SubElement(premisObjectObjectCharacteristicsFormat,'formatDesignation')
premisObjectObjectCharacteristicsFormatFormatDesignationFormatName = ET.SubElement(premisObjectObjectCharacteristicsFormatFormatDesignation,'formatName')
premisObjectObjectCharacteristicsFormatFormatDesignationFormatName.text = 'text/xml'
premisLinkingEventIdentifier = ET.SubElement(premisObject,'linkingEventIdentifier')
premisLinkingEventIdentifierLinkingEventIdentifierType = ET.SubElement(premisLinkingEventIdentifier,'linkingEventIdentifierType')
premisLinkingEventIdentifierLinkingEventIdentifierType.text = 'uuid'
premisLinkingEventIdentifierLinkingEventIdentifierValue = ET.SubElement(premisLinkingEventIdentifier,'linkingEventIdentifierValue')
premisLinkingEventIdentifierLinkingEventIdentifierValue.text = eventUUID

### Create a PREMIS file object for the generated xml-file ###
premisObject = ET.SubElement(premis,'object')
premisObject.set('xsi:type','file')
premisObjectIdentfier = ET.SubElement(premisObject,'objectIdentifier')
premisObjectIdentfierType = ET.SubElement(premisObjectIdentfier,'objectIdentifierType')
premisObjectIdentfierType.text = 'uuid'
premisObjectIdentfierValue = ET.SubElement(premisObjectIdentfier,'objectIdentifierValue')
premisObjectIdentfierValue.text = xmlUUID
premisObjectObjectCharacteristics = ET.SubElement(premisObject,'objectCharacteristics')
premisObjectObjectCharacteristicsCompositionLevel = ET.SubElement(premisObjectObjectCharacteristics,'compositionLevel')
premisObjectObjectCharacteristicsCompositionLevel.text = '0'
premisObjectObjectCharacteristicsFixity = ET.SubElement(premisObjectObjectCharacteristics,'fixity')
premisObjectObjectCharacteristicsFixityMessageDigestAlgorithm = ET.SubElement(premisObjectObjectCharacteristicsFixity,'messageDigestAlgorithm')
premisObjectObjectCharacteristicsFixityMessageDigestAlgorithm.text = 'md5'
premisObjectObjectCharacteristicsFixityMessageDigest = ET.SubElement(premisObjectObjectCharacteristicsFixity,'messageDigest')
premisObjectObjectCharacteristicsFixityMessageDigest.text = hashlib.md5(open(rootPath+'/content/'+xmlUUID+'.xml','rb').read()).hexdigest()
premisObjectObjectCharacteristicsSize = ET.SubElement(premisObjectObjectCharacteristics,'size')
premisObjectObjectCharacteristicsSize.text = str(os.path.getsize(rootPath+'/content/'+xmlUUID+'.xml'))
premisObjectObjectCharacteristicsFormat = ET.SubElement(premisObjectObjectCharacteristics,'format')
premisObjectObjectCharacteristicsFormatFormatDesignation= ET.SubElement(premisObjectObjectCharacteristicsFormat,'formatDesignation')
premisObjectObjectCharacteristicsFormatFormatDesignationFormatName = ET.SubElement(premisObjectObjectCharacteristicsFormatFormatDesignation,'formatName')
premisObjectObjectCharacteristicsFormatFormatDesignationFormatName.text = 'text/xml'
premisObjectObjectCharacteristicsCreatingApplication = ET.SubElement(premisObjectObjectCharacteristics,'creatingApplication')
premisObjectObjectCharacteristicsCreatingApplicationName = ET.SubElement(premisObjectObjectCharacteristicsCreatingApplication,'creatingApplicationName')
premisObjectObjectCharacteristicsCreatingApplicationName.text = 'iphone-sms-archiver'
premisObjectObjectCharacteristicsCreatingApplicationVersion = ET.SubElement(premisObjectObjectCharacteristicsCreatingApplication,'creatingApplicationVersion')
premisObjectObjectCharacteristicsCreatingApplicationVersion.text = '1.0' #Change to easy modified variable
premisObjectObjectCharacteristicsCreatingApplicationDate = ET.SubElement(premisObjectObjectCharacteristicsCreatingApplication,'dateCreatedByApplication')
premisObjectObjectCharacteristicsCreatingApplicationDate.text = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%H:%M:%S')
premisObjectRelationship = ET.SubElement(premisObject,'relationship')
premisObjectRelationshipRelationshipType = ET.SubElement(premisObjectRelationship,'relationshipType')
premisObjectRelationshipRelationshipType.text = 'dependency'
premisObjectRelationshipRelationshipSubType = ET.SubElement(premisObjectRelationship,'relationshipSubType')
premisObjectRelationshipRelationshipSubType.text = 'requires'
premisObjectRelationshipRelatedObjectIdentifier = ET.SubElement(premisObjectRelationship,'relatedObjectIdentifier')
premisObjectRelationshipRelatedObjectIdentifierRelatedObjectIdentifierType = ET.SubElement(premisObjectRelationshipRelatedObjectIdentifier,'relatedObjectIdentifierType')
premisObjectRelationshipRelatedObjectIdentifierRelatedObjectIdentifierType.text = 'uuid'
premisObjectRelationshipRelatedObjectIdentifierRelatedObjectIdentifierValue = ET.SubElement(premisObjectRelationshipRelatedObjectIdentifier,'relatedObjectIdentifierValue')
premisObjectRelationshipRelatedObjectIdentifierRelatedObjectIdentifierValue.text = xsdUUID
premisObjectRelationshipRelatedEnvironmentPurpose = ET.SubElement(premisObjectRelationship,'relatedEnvironmentPurpose')
premisObjectRelationshipRelatedEnvironmentPurpose.text ='validate'
premisObjectRelationshipRelatedEnvironmentCharacteristic = ET.SubElement(premisObjectRelationship,'relatedEnvironmentCharacteristic')
premisObjectRelationshipRelatedEnvironmentCharacteristic.text = 'known to work'
premisObjectRelationship = ET.SubElement(premisObject,'relationship')
premisObjectRelationshipRelationshipType = ET.SubElement(premisObjectRelationship,'relationshipType')
premisObjectRelationshipRelationshipType.text = 'dependency'
premisObjectRelationshipRelationshipSubType = ET.SubElement(premisObjectRelationship,'relationshipSubType')
premisObjectRelationshipRelationshipSubType.text = 'requires'
premisObjectRelationshipRelatedObjectIdentifier = ET.SubElement(premisObjectRelationship,'relatedObjectIdentifier')
premisObjectRelationshipRelatedObjectIdentifierRelatedObjectIdentifierType = ET.SubElement(premisObjectRelationshipRelatedObjectIdentifier,'relatedObjectIdentifierType')
premisObjectRelationshipRelatedObjectIdentifierRelatedObjectIdentifierType.text = 'uuid'
premisObjectRelationshipRelatedObjectIdentifierRelatedObjectIdentifierValue = ET.SubElement(premisObjectRelationshipRelatedObjectIdentifier,'relatedObjectIdentifierValue')
premisObjectRelationshipRelatedObjectIdentifierRelatedObjectIdentifierValue.text = xslUUID
premisObjectRelationshipRelatedEnvironmentPurpose = ET.SubElement(premisObjectRelationship,'relatedEnvironmentPurpose')
premisObjectRelationshipRelatedEnvironmentPurpose.text ='rendering'
premisObjectRelationshipRelatedEnvironmentCharacteristic = ET.SubElement(premisObjectRelationship,'relatedEnvironmentCharacteristic')
premisObjectRelationshipRelatedEnvironmentCharacteristic.text = 'known to work'
premisLinkingEventIdentifier = ET.SubElement(premisObject,'linkingEventIdentifier')
premisLinkingEventIdentifierLinkingEventIdentifierType = ET.SubElement(premisLinkingEventIdentifier,'linkingEventIdentifierType')
premisLinkingEventIdentifierLinkingEventIdentifierType.text = 'uuid'
premisLinkingEventIdentifierLinkingEventIdentifierValue = ET.SubElement(premisLinkingEventIdentifier,'linkingEventIdentifierValue')
premisLinkingEventIdentifierLinkingEventIdentifierValue.text = eventUUID

###Create the PREMIS EVENT###
premisEvent = ET.SubElement(premis,'event')
premisEventEventIdentifier = ET.SubElement(premisEvent,'eventIdentifier')
premisEventEventIdentifierEventIdentifierType = ET.SubElement(premisEventEventIdentifier,'eventIdentifierType')
premisEventEventIdentifierEventIdentifierType.text = 'uuid'
premisEventEventIdentifierEventIdentifierValue = ET.SubElement(premisEventEventIdentifier,'eventIdentifierValue')
premisEventEventIdentifierEventIdentifierValue.text = eventUUID
premisEventEventType = ET.SubElement(premisEvent,'eventType')
premisEventEventType.text = 'CAPTURE'
premisEventEventDateTime = ET.SubElement(premisEvent,'eventDateTime')
premisEventEventDateTime.text = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%H:%M:%S')# MOVE THIS TO SCRIPT START
premisEventEventDetailInformation = ET.SubElement(premisEvent,'eventDetailInformation')
premisEventEventDetailInformationEventDetail = ET.SubElement(premisEventEventDetailInformation,'eventDetail')
premisEventEventDetailInformationEventDetail.text = 'Extract all attachments and make an xml-representation of selected conversation from iphone sqlite database '
premisEventLinkingAgentIdentifier = ET.SubElement(premisEvent,'linkingAgentIdentifier')
premisEventLinkingAgentIdentifierLinkingAgentIdentifierType = ET.SubElement(premisEventLinkingAgentIdentifier,'linkingAgentIdentifierType')
premisEventLinkingAgentIdentifierLinkingAgentIdentifierType.text = 'localAgentId'
premisEventLinkingAgentIdentifierLinkingAgentIdentifierValue = ET.SubElement(premisEventLinkingAgentIdentifier,'linkingAgentIdentifierValue')
premisEventLinkingAgentIdentifierLinkingAgentIdentifierValue.text = '1'
premisEventLinkingAgentIdentifierLinkingAgentRole = ET.SubElement(premisEventLinkingAgentIdentifier,'linkingAgentRole')
premisEventLinkingAgentIdentifierLinkingAgentRole.text = 'executing program'

premisEventLinkingAgentIdentifier = ET.SubElement(premisEvent,'linkingAgentIdentifier')
premisEventLinkingAgentIdentifierLinkingAgentIdentifierType = ET.SubElement(premisEventLinkingAgentIdentifier,'linkingAgentIdentifierType')
premisEventLinkingAgentIdentifierLinkingAgentIdentifierType.text = 'localAgentId'
premisEventLinkingAgentIdentifierLinkingAgentIdentifierValue = ET.SubElement(premisEventLinkingAgentIdentifier,'linkingAgentIdentifierValue')
premisEventLinkingAgentIdentifierLinkingAgentIdentifierValue.text = operatorAgentSName +',' + operatorAgentFName
premisEventLinkingAgentIdentifierLinkingAgentRole = ET.SubElement(premisEventLinkingAgentIdentifier,'linkingAgentRole')
premisEventLinkingAgentIdentifierLinkingAgentRole.text = 'archivist'

###Create a softwareAgent for this script###
premisAgent = ET.SubElement(premis,'agent')
premisAgentAgentIdentifier = ET.SubElement(premisAgent ,'agentIdentifier')
premisAgentAgentIdentifierAgentIdentifierType = ET.SubElement(premisAgentAgentIdentifier ,'agentIdentifierType')
premisAgentAgentIdentifierAgentIdentifierType.text = 'localAgentId'
premisAgentAgentIdentifierAgentIdentifierValue = ET.SubElement(premisAgentAgentIdentifier ,'agentIdentifierValue')
premisAgentAgentIdentifierAgentIdentifierValue.text = '1'
premisAgentAgentName = ET.SubElement(premisAgent ,'agentName')
premisAgentAgentName.text = 'iphone-sms-archiver'
premisAgentAgentType = ET.SubElement(premisAgent ,'agentType')
premisAgentAgentType.text = 'software application'
premisAgentAgentVersion = ET.SubElement(premisAgent ,'agentVersion')
premisAgentAgentVersion.text = '1.0' #Change to easy modified variable
premisAgentAgentLinkingEnvironmentIdentifier = ET.SubElement(premisAgent ,'linkingEnvironmentIdentifier')
premisAgentAgentLinkingEnvironmentIdentifierLinkingEnvironmentIdentifierType = ET.SubElement(premisAgentAgentLinkingEnvironmentIdentifier ,'linkingEnvironmentIdentifierType')
premisAgentAgentLinkingEnvironmentIdentifierLinkingEnvironmentIdentifierType.text = 'localObjectId'
premisAgentAgentLinkingEnvironmentIdentifierLinkingEnvironmentIdentifierValue = ET.SubElement(premisAgentAgentLinkingEnvironmentIdentifier ,'linkingEnvironmentIdentifierValue')
premisAgentAgentLinkingEnvironmentIdentifierLinkingEnvironmentIdentifierValue.text = '1'

premisAgent = ET.SubElement(premis,'agent')
premisAgentAgentIdentifier = ET.SubElement(premisAgent ,'agentIdentifier')
premisAgentAgentIdentifierAgentIdentifierType = ET.SubElement(premisAgentAgentIdentifier ,'agentIdentifierType')
premisAgentAgentIdentifierAgentIdentifierType.text = 'localAgentId'
premisAgentAgentIdentifierAgentIdentifierValue = ET.SubElement(premisAgentAgentIdentifier ,'agentIdentifierValue')
premisAgentAgentIdentifierAgentIdentifierValue.text = operatorAgentSName +',' + operatorAgentFName
premisAgentAgentName = ET.SubElement(premisAgent ,'agentName')
premisAgentAgentName.text = operatorAgentFName+' '+operatorAgentSName
premisAgentAgentType = ET.SubElement(premisAgent ,'agentType')
premisAgentAgentType.text = 'person'
premisTree = ET.ElementTree(premis)
premisTree.write(rootPath+'/metadata/premis.xml', encoding='utf-8', xml_declaration=True)


### Next step is to create a Bagit bag with som Dublin Core metadata in bag.info###
bagitDict = {}
contactNameKey = 'Contact-Name'
contactNameValue = myFname+' '+mySname
bagitDict[contactNameKey]=contactNameValue.encode('utf-8')
dcTitleKey = 'dc:title'
dcTitleValue = 'sms conversation'
bagitDict[dcTitleKey] = dcTitleValue
dcDescriptionKey = 'dc:description'
dcDescriptionValue = 'conversation between '+myFname+' '+mySname+' and '+extFname+' '+extSname
bagitDict[dcDescriptionKey] = dcDescriptionValue.encode('utf-8')
dcCoverageKey = 'dc:coverage'
dcCoverageValue = firstDate+' - '+lastDate
bagitDict[dcCoverageKey] = dcCoverageValue
dcCreatorKey = 'dc:creator'
dcCreatorValue = myFname+' '+mySname
bagitDict[dcCreatorKey] = dcCreatorValue.encode('utf-8')
bag = bagit.make_bag(str(rootPath.encode('utf-8')), bagitDict)

###Final step is to make a TAR-file###
tar = tarfile.open(extFname+'_'+extSname+'_'+conversationUUID+".tar", "w")
tar.add(rootPath)
tar.close()



