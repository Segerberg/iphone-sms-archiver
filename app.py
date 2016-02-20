import datetime
import getpass
import os
import platform

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
        backupPath =''

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

print dictList[backupChoice]
