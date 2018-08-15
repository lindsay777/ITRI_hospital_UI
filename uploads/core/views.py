from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from uploads.core.models import Document
from uploads.core.forms import DocumentForm

from os import listdir
from os.path import isfile, join

import matplotlib.pyplot as plt
import pydicom
import zipfile
import cv2
import os
import shutil
from pydicom.data import get_testdata_files

def home(request):
    documents = Document.objects.all()
    return render(request, 'core/home.html', { 'documents': documents })

def simple_upload(request):
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        zipFileName = fs.save(myfile.name, myfile)

        # read zip file
        zip_file = zipfile.ZipFile(os.path.join(os.getcwd(), 'media/', zipFileName))

        # create a folder with a uniqe name same as the zip file
        folderNameList = list(zipFileName)[:-4] #remove '.zip'
        folderName = ''.join(folderNameList)
        folderPath = 'media/' + folderName

        # extract zip file to the folder created
        for file in zip_file.namelist():
            zip_file.extract(file, os.path.join(os.getcwd(), folderPath))

        # get .dcm files from the zip folder
        zip_list = zip_file.namelist()
        lstFilesDCM = []
        for file_name in zip_list:
            if ".dcm" in file_name.lower():
                lstFilesDCM.append(os.path.join(os.getcwd(), folderPath, file_name))
        print(lstFilesDCM[0] + '\n')

        # read IMG00000
        dataset = pydicom.dcmread(lstFilesDCM[0]) 

        # get patient's ID
        pid = dataset.PatientID

        # get sex
        sex = dataset.PatientSex

        # get age (ex. 063Y->63)
        age_list = list(dataset.PatientAge)
        del age_list[-1]
        if age_list[0]=='0':
            del age_list[0]
        age = ''.join(age_list)

        # get MP
        name = str(dataset.PatientName)
        if "(PM" in name:
            name = name.split('(')[1].split(')')[0]
            name_list = list(name)
            del name_list[0:2]
            mp = ''.join(name_list)

        #----- get image report from file IMG00000 -----  
        # get image and save to report
        # pydicom example: https://goo.gl/SMyny4
        report = ''
        if cv2.imwrite(folderPath + '/IMG00000_report.jpg', dataset.pixel_array):
            report = '/' + folderPath + '/IMG00000_report.jpg'

        #----- get zscore, tscore from file STR00000 -----
        # read STR00000
        dataset = pydicom.dcmread(lstFilesDCM[5])  

        zscore=[]
        tscore=[]
        imageComments = dataset.ImageComments.split('><')

        # get zscore
        match_zscore = [s for s in imageComments if "BMD_ZSCORE" in s]
        for substring in match_zscore:
            substring = substring.split('</')[0].split('>')[1]
            zscore.append(substring)

        # get tscore
        match_tscore = [s for s in imageComments if "BMD_TSCORE" in s]
        for substring in match_tscore:
            substring = substring.split('</')[0].split('>')[1]
            tscore.append(substring)

        uploaded_file_url = fs.url(zipFileName)
        return render(request, 'core/simple_upload.html', {
            'uploaded_file_url': uploaded_file_url,
            'pid': pid,
            'sex': sex,
            'age': age,
            'mp': mp,
            'zscore': zscore,
            'tscore': tscore,
            'report': report,
        })

    return render(request, 'core/simple_upload.html')


def upload_dcm(request):
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        fileName = fs.save(myfile.name, myfile)
        print('filename:' + fileName)
        print(os.getcwd())

        # move file form media/ to media/dcm/ folder
        shutil.move('media/'+fileName, 'media/DCM/'+fileName)
        dcmFilePath = 'media/DCM/' + fileName

        # read file
        dataset = pydicom.dcmread(dcmFilePath) 

        # get patient's ID
        pid = dataset.PatientID

        # get sex
        sex = dataset.PatientSex

        # get age (ex. 063Y->63)
        age_list = list(dataset.PatientAge)
        del age_list[-1]
        if age_list[0]=='0':
            del age_list[0]
        age = ''.join(age_list)

        # get MP
        name = str(dataset.PatientName)
        if "(PM" in name:
            name = name.split('(')[1].split(')')[0]
            name_list = list(name)
            del name_list[0:2]
            mp = ''.join(name_list)

        # response={
        #     'pid': pid,
        #     'sex': sex,
        #     'age': age,
        #     'mp': mp,
        # }

        #----- get image report from file IMG00000 -----  
        # get image and save to report
        # pydicom example: https://goo.gl/SMyny4
        report = ''
        zscore=[]
        tscore=[]
        if fileName.startswith('IMG00000'):
            if cv2.imwrite('media/DCM/IMG00000_report.jpg', dataset.pixel_array):
                report = '/media/DCM/IMG00000_report.jpg'
                #response['report'] = '/media/DCM/IMG00000_report.jpg'

        #----- get zscore, tscore from file STR00000 -----
        # read STR00000
        elif fileName.startswith('STR00000'):       
            imageComments = dataset.ImageComments.split('><')

            # get zscore
            match_zscore = [s for s in imageComments if "BMD_ZSCORE" in s]
            for substring in match_zscore:
                substring = substring.split('</')[0].split('>')[1]
                zscore.append(substring)

            # get tscore
            match_tscore = [s for s in imageComments if "BMD_TSCORE" in s]
            for substring in match_tscore:
                substring = substring.split('</')[0].split('>')[1]
                tscore.append(substring)

            # response['zscore'] = zscore
            # response['tscore'] = tscore
        
        # print(response)
        # print(response[zscore])
        uploaded_file_url = fs.url(fileName)
        # response={'uploaded_file_url': uploaded_file_url}
        # return render(request, 'core/upload_dcm.html', response)
        return render(request, 'core/upload_dcm.html', {
            'uploaded_file_url': uploaded_file_url,
            'pid': pid,
            'sex': sex,
            'age': age,
            'mp': mp,
            'zscore': zscore,
            'tscore': tscore,
            'report': report,
        })
    else:
        return render(request, 'core/upload_dcm.html')
        

def upload_zip(request):
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        zipFileName = fs.save(myfile.name, myfile)

        print('zipFilename:' + zipFileName)
        print(os.getcwd())

        # move file form media/ to media/dcm/ folder
        shutil.move('media/'+zipFileName, 'media/ZIP/'+zipFileName)

        # read zip file
        zip_file = zipfile.ZipFile(os.path.join(os.getcwd(), 'media/ZIP/', zipFileName))

        # extract zip file
        for file in zip_file.namelist():
            zip_file.extract(file, os.path.join(os.getcwd(), 'media/ZIP/'))
        
        # get folder name of the extracted zip file
        fileName = list(zipFileName)[:-4] #remove '.zip'
        fileName = ''.join(fileName)
        zipFilePath = 'media/ZIP/' + fileName

        # response={
        #     'zipFileName': zipFileName,
        #     'zipFilePath': zipFilePath,
        # }

        # print directory tree
        # traverse root directory, and list directories as dirs and files as files
        dir_tree = []
        for root, dirs, files in os.walk(zipFilePath):
            path = root.split(os.sep)
            line = ((len(path) - 1) * '---', os.path.basename(root))
            line = ''.join(line)
            dir_tree.append(line)
            for file in files:
                line = (len(path) * '---', file)
                line = ''.join(line)
                dir_tree.append(line)
        # response['dir_tree'] = dir_tree

        # get .dcm files from the zip folder
        zip_list = zip_file.namelist()
        lstFilesDCM = []
        for file_name in zip_list:
            if ".dcm" in file_name.lower():
                lstFilesDCM.append(os.path.join(os.getcwd(), zipFilePath, file_name))
        print(lstFilesDCM[0] + '\n')

        # response['uploaded_file_url'] = fs.url(zipFileName)
        uploaded_file_url = fs.url(zipFileName)
        # return render(request, 'core/upload_zip.html', response)
        return render(request, 'core/upload_zip.html', {
            'uploaded_file_url': uploaded_file_url,
            'zipFileName': zipFileName,
            'zipFilePath': zipFilePath,
            'dir_tree': dir_tree,
        })
    else: 
        return render(request, 'core/upload_zip.html')

# 在view裡面可以使用form
# 定義一個view 透過request把資料POST到request.POST當中
# 再把request.POST當作constructor傳入form裡面
def model_form_upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid(): # 檢查輸入資料是否合法
            form.save()
            return redirect('home')
    else:
        form = DocumentForm()
    return render(request, 'core/model_form_upload.html', {
        'form': form
    })

def manage_dcm(request):

    folderPath = 'media/DCM/'

    # list files in the folder
    onlyfiles = [f for f in listdir(folderPath) if isfile(join(folderPath, f))]

    return render(request, 'core/manage_dcm.html', {
        'onlyfiles': onlyfiles,
    })

def show_dcm(request):
    print(os.getcwd())

    # get the fileName user clicked from template
    fileName = request.GET.get('file', None)

    # fileName / filePath preprocess
    filePath = 'media/DCM/' + fileName
    fileName = list(fileName)[:-4] #remove '.dcm'
    fileName = ''.join(fileName)
    print('fileName: ' + fileName)
    print('filePath: ' + filePath)

    # read file
    dataset = pydicom.dcmread(filePath) 

    # get patient's ID
    pid = dataset.PatientID

    # get sex
    sex = dataset.PatientSex

    # get age (ex. 063Y->63)
    age_list = list(dataset.PatientAge)
    del age_list[-1]
    if age_list[0]=='0':
        del age_list[0]
    age = ''.join(age_list)

    # get MP
    name = str(dataset.PatientName)
    if "(PM" in name:
        name = name.split('(')[1].split(')')[0]
        name_list = list(name)
        del name_list[0:2]
        mp = ''.join(name_list)

    # ----- Judge from filename, get value or image -----
    zscore=[]
    tscore=[]
    report=''
    response={
        'pid': pid,
        'sex': sex,
        'age': age,
        'mp': mp,
        }
    # get zscore, tscore from file STR00000
    if fileName.startswith('STR00000'):
        imageComments = dataset.ImageComments.split('><')

        # get zscore
        match_zscore = [s for s in imageComments if "BMD_ZSCORE" in s]
        for substring in match_zscore:
            substring = substring.split('</')[0].split('>')[1]
            zscore.append(substring)

        # get tscore
        match_tscore = [s for s in imageComments if "BMD_TSCORE" in s]
        for substring in match_tscore:
            substring = substring.split('</')[0].split('>')[1]
            tscore.append(substring)

        response={
            'zscore': zscore,
            'tscore': tscore,
        }
    
    # get image and save to report from file IMG
    # pydicom example: https://goo.gl/SMyny4
    elif fileName.startswith('IMG'):      
        if cv2.imwrite('media/DCM/' + fileName + '_report.jpg', dataset.pixel_array):
            response['report'] = '/media/DCM/' + fileName + '_report.jpg'
    print(response)
    return render(request, 'core/show_dcm.html', response)

def manage_zip(request):

    folderPath = 'media/ZIP/'

    # list files in the folder
    onlyfiles = [f for f in listdir(folderPath) if isfile(join(folderPath, f))]

    return render(request, 'core/manage_zip.html', {
        'onlyfiles': onlyfiles,
    })


# TODO: 
# 1. rename/download/delete in manage files
# 2. warnings for same filenames
# 3. upload zip file: click to show??