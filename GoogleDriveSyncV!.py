from __future__ import print_function
import pickle
import json
import os,sys,time,shutil
import os.path
import urllib.parse
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient import errors
from pathlib import Path

class GoogleDriveSync:
    def __init__(self):
        self.data={}
        self.config = {
            'baseUrlToWriteInFile':'www.google.com/',  # url which gets written in the text file
            # 'folderToStoreFiles':'D:\\gdriveLog\\',        # local folder path from root
            'folderToStoreFiles':'/home/pg/gdrivelog/', 
            'myDriveFolderName':'mydrive',             # my drive folder in drive will map to this folder name
            'sharedFolderName':'shared' ,              # shared files/folders will map in this folder name
            'checkDelay':10,
            'platform':''
        }
        self.client_config = {
        "installed": {
            # replace this with content of credentials.json file
        }
        }

    # function authenticate the user and returns the service to be used as api
    def authenticate(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(client_config,SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        service = build('drive', 'v3', credentials=creds)
        self.service = service
    
    def cleanLocalFileStructure(self):
        if os.path.exists(os.path.normcase(self.config['folderToStoreFiles'])):
            print('[WARNING] cleaning the directory')
            try:
                shutil.rmtree(os.path.normcase(self.config['folderToStoreFiles']))
            except:
                print('[ERROR] unnable to delete folder,Please delete '+str(self.config['folderToStoreFiles']) +' manually')
  
    def listDrives(self):
        driveList = self.service.drives().list().execute()
        self.drives = driveList.get('drives')         
        for drive in self.drives:
            self.data[drive['id']] = drive

    def createLocalStructureFromFile(self):
        print('[info] creating files')
        for i in self.data.keys():
            name, id , parentNames = self.getFormatedData(i)
            drivePath=''
            while len(parentNames)>0:
                drivePath = drivePath + parentNames.pop() +'/'
            path = self.config.get('folderToStoreFiles') + drivePath
            if len(name.split('.')) > 1:
                if not os.path.exists(os.path.normcase(path)):
                    os.makedirs(os.path.normcase(path))
                with open(os.path.normcase(path + name +'.txt'), 'w', encoding="utf-8") as filehandle:
                    print(os.path.normcase(path + name +'.txt'))
                    # drivePath= self.replaceDriveNameToNo(drivePath,self.data[i])
                    filehandle.write(urllib.parse.quote(self.config.get('baseUrlToWriteInFile') + drivePath + name))

    def getGoogleDriveData(self,forced):
        files=[]
        page_token = None
        print('[info] getting all data from drive')
        if os.path.exists('output.txt') and not forced:
            try:
                with open('output.txt', 'rb') as filehandle:
                    self.data = pickle.load(filehandle)
                print('[info] found output.txt, reading the file')
            except:
                print('[ERROR] output.txt badfile cleaning')
                os.remove('output.txt')
                self.getGoogleDriveData()
        else:
            while True:
                try:
                    param = {}
                    param['supportsAllDrives']=True
                    param['includeItemsFromAllDrives']=True
                    param['q']="trashed = false"
                    param['fields']="nextPageToken, files(id,name,parents,modifiedTime)"
                    if page_token:
                        param['pageToken'] = page_token
                    results = self.service.files().list(**param).execute()
                    files = files + results.get('files', [])
                    page_token = results.get('nextPageToken')
                    if not page_token:
                        break
                except:
                    print('[ERROR] An error occurred:')
                    self.main()
                with open('output.txt', 'wb') as filehandle:
                    print(len(files))
                    for i in files:
                        self.data[i['id']]=i
                    pickle.dump(self.data, filehandle)
                
                #self.createLocalStructureFromFile()
                print('[info] getting next page data')
        

    def getParents(self,id):
        data=self.data
        parentName=[]
        parentIds=[]
        while True:
            if id in data.keys():
                parentName.append(data[id]['name'].strip())
                parentIds.append(id)
                if 'parents' in data[id].keys():
                    id = data[id]['parents'][0]
                else:
                    parentName.append(self.config.get('sharedFolderName'))
                    break
            else:
                parentName.append(self.config.get('myDriveFolderName'))
                break
        return [parentName,parentIds]

    def getFormatedData(self,i):
        data=self.data
        name='' 
        id=''
        parents=''
        parentNames=[]
        parentIds=[]
        if 'name' in data[i].keys():
            name= data[i]['name']
        if 'id' in data[i].keys():
            id=data[i]['id']
        if 'parents' in data[i].keys():
            parents = data[i]['parents']
            parentNames,parentIds = self.getParents(parents[0])
        if 'parents' not in data[i].keys():
            parentNames = [self.config.get('sharedFolderName')]
        return [ name.strip() , id , parentNames, parentIds]
    
    def replaceDriveNameToNo(self,path,parentIds):
        containsDrive = False
        drivePath = path
        for drive in self.drives:
            if drive.get('id') in parentIds:
                containsDrive=True
        if self.config.get('myDriveFolderName') in path.split('/'):
            path = '/'.join([name.replace(self.config.get('myDriveFolderName'),str(0)+':') for name in path.split('/')])
        if containsDrive:
            driveArr = path.split('/')
            driveArr = driveArr[1:]
            drivePath= '/'.join(driveArr)
            for idx, i in enumerate(self.drives):
                if i['id'] in parentIds:
                    temp= [ name.replace(i['name'],str(idx+1)+':') for name in driveArr]
                    path = '/'.join(temp)
        return [drivePath , path]

    def removeFile(self,i):
        name, id ,parentNames,parentIds = self.getFormatedData(i)
        self.data[i]['path'] = parentNames
        drivePath=''
        while len(parentNames) > 0:
            drivePath = drivePath + parentNames.pop() +'/'   
        path = self.config.get('folderToStoreFiles') + drivePath
        normPath = os.path.normcase(path)
        filePath = path + name +'.txt'
        normFilePath = os.path.normcase(filePath)
        if os.path.exists(normFilePath):
            os.remove(normFilePath)

    def createFile(self,i):
        name, id ,parentNames,parentIds = self.getFormatedData(i)
        self.data[i]['path'] = parentNames
        drivePath=''
        while len(parentNames) > 0:
            drivePath = drivePath + parentNames.pop() +'/'   

        if len(name.split('.')) > 1:
            drivePath , contentPath = self.replaceDriveNameToNo(drivePath,parentIds)
            path = self.config.get('folderToStoreFiles') + drivePath
            normPath = os.path.normcase(path)
            filePath = path + name +'.txt'
            normFilePath = os.path.normcase(filePath)
            # print(path,name)
            if not os.path.exists(normPath):
                os.makedirs(normPath)
            with open(normFilePath, 'w', encoding="utf-8") as filehandle:
                # contentPath = self.replaceDriveNameToNo(drivePath,parentIds)
                # fileContent = urllib.parse.quote(self.config.get('baseUrlToWriteInFile') + contentPath + name)
                fileContent = self.config.get('baseUrlToWriteInFile') + contentPath + name
                filehandle.write(fileContent)

    def createFilesAndFolders(self):
        print('[info] creating files')
        data = self.data
        for i in data.keys():
            self.createFile(i)

        # for key in data.keys():
        #     print(data.get(key).get('name'),data.get(key).get('parents'),data.get(key).get('path'))
    
    def updateOutputFile(self,changes):
        print(changes)
        files=[]
        for change in changes:
            fileId = change.get('fileId')
            if change.get('file'):
                name = change.get('file').get('name')
            removed = change.get('removed')
            if removed:
                self.removeFile(fileId)
                itemRemoved = self.data.pop(fileId,'already removed')
                print('[info] removed item '+str(itemRemoved))
            else:
                page_token=None
                while True:
                    # try:
                    param = {}
                    param['supportsAllDrives']=True
                    param['includeItemsFromAllDrives']=True
                    param['q']="trashed = false and name='"+name+"'"
                    param['fields']="nextPageToken, files(id,name,parents,modifiedTime)"
                    if page_token:
                        param['pageToken'] = page_token
                    results = self.service.files().list(**param).execute()
                    print(results)
                    files = files + results.get('files', [])
                    page_token = results.get('nextPageToken')
                    if not page_token:
                        break
                if len(files) == 0:
                    self.removeFile(fileId)
                    itemRemoved = self.data.pop(fileId,'already removed')
                    print('[info] trash item  '+str(itemRemoved))
                
        with open('output.txt', 'wb') as filehandle:
            if len(files) > 0:
                for i in files:
                    self.data[i['id']]=i
            pickle.dump(self.data, filehandle)
        for i in files:
            self.createFile(i['id'])
                
                    # except:
                    #     print('[ERROR] An error occurred:')
            #     pass

            # page_token=None
            # while True:
            #     if page_token:
            #         param['pageToken'] = page_token
            #     results = self.service.files().get(fileId=fileId).execute()
            #     print(results.get('files', []))
            #     page_token = results.get('nextPageToken')
            #     if not page_token:
            #         break                
            # self.data[fileId] = 

    def isDriveChanged(self,saved_start_page_token):
        page_token = saved_start_page_token
        print('[info] fetching latest changes')
        param = {}
        param['supportsAllDrives']=True
        param['includeItemsFromAllDrives']=True
        param['spaces']='drive'
        # param['q']="trashed = false"
        # param['fields']="nextPageToken, files(id,name,parents,modifiedTime)"
        while page_token is not None:
            param['pageToken'] = page_token
            response = self.service.changes().list(**param).execute()
            # for change in response.get('changes'):
            #     # Process change
            #     isChanged=True
            #     # print('Change found for file: %s' % change.get('fileId'))
            if 'newStartPageToken' in response:
                # Last page, save this token for the next polling interval
                saved_start_page_token = response.get('newStartPageToken')
            page_token = response.get('nextPageToken')
        return response.get('changes')
    
    def main(self):
        self.authenticate()
        self.listDrives()
        self.cleanLocalFileStructure()
        forced=None
        if len(sys.argv) > 1:
            if 'forced' in sys.argv:
                forced=True
        response = self.service.changes().getStartPageToken().execute()
        firstPageToken = response.get('startPageToken')
        self.getGoogleDriveData(forced)
        self.createFilesAndFolders()
        while True:
            changes = self.isDriveChanged(firstPageToken)
            if len(changes) > 0:
                print('[info] drive changes detected')
                self.updateOutputFile(changes)
                # self.cleanLocalFileStructure()
                # self.createFilesAndFolders()
                response = self.service.changes().getStartPageToken().execute()
                firstPageToken = response.get('startPageToken')

            print('waiting for delay of '+str(self.config.get('checkDelay')))
            for i in range(self.config.get('checkDelay'),0,-1):
                sys.stdout.write(str(i)+' ')
                sys.stdout.flush()
                time.sleep(1)
            print('')

driveObj = GoogleDriveSync()
if __name__ == '__main__':
    driveObj.main()