iphone-sms-archiver
==========================================
Apple offers no easy way to export your texts and iMessages there are software available to do exports, most of them are however commercial products, and there doesn’t seem to be a free, open source option that’s “good enough”.

Tom Offermanns Iphone-sms-backup python script http://toffer.github.com/iphone-sms-backup/ gets the job done but has some drawbacks:

* Does not try to recover texts with photos. Just skips past them.

* Does not handle group chats

* Only works with IOS 5 to IOS 7 (if you upgraded you're screwed because apple changed the database structure from IOS 8)

The Iarchiver-script is currently under development and is an attempt to make archival representations of the sms/imessages in the iphones messages database. 

The Iarchiver script:

* Does recover text with photos and other attachments 

* ~~Works with IOS 8 and 9~~ 

* ~~Works with IOS 10~~ 

* Works with IOS 11 

* Does NOT handle group chats (yet) 

* Spits out the sms/imessage as an xml-file 

Dependencies
-------------------
You need to install the library bagit from the great folks at LOC before you can run the script  https://github.com/LibraryOfCongress/bagit-python

Running the script
-------------------
You need to connect your iPhone to iTunes and perform a local backup (no encryption), Icloud-backup is not the way to go.

    $ python app.py

Then just follow the instructions. 

