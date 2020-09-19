# GoogleDriveSync

A python script to track changes in the google drive using gooel drive api V3.
This script creates the same folder structure in the local machine as it is in google drive.
Script runs in loop and check for the changes and update the local structure according to the changes made in the drive.
Point to note that this script does not fetch the whole file from the drive but instead creates the text file, 
just to represent the folder structure.

## Usages

Please add the credentials.json content to the script which stores the client secreat key and id.
To get the credentials.json file follow the instructions for <a target='__blank' href='https://developers.google.com/drive/api/v3/quickstart/python'>Google Drive Api Quickstart</a>

To fetch all the changes locally and delete the older folder structure call the script with forced flag.
```
python script.py forced
```
To run the script
```
python script.py
```
