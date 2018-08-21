from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse

from uploads.core.models import Document
from uploads.core.forms import DocumentForm
from uploads.core.forms import nameForm

from os import listdir
from os.path import isfile, join

import matplotlib.pyplot as plt
import pydicom
import zipfile
import cv2
import os
import shutil
import re
from pydicom.data import get_testdata_files

# TODO: 
# 1. delete in manage files page
# 2. warnings for same filenames

# variable naming principle:
# myfile: .dcm
# myZipFile: .zip
# zipFolder: folder
# fileName: no .dcm

# session:
# upload_zip: myZipFile
# show_dcm: myfile

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
        myfile = fs.save(myfile.name, myfile)

        # move file form media/ to media/dcm/ folder
        shutil.move('media/'+myfile, 'media/DCM/'+myfile)
        dcmFilePath = 'media/DCM/' + myfile

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

        response={
            'pid': pid,
            'sex': sex,
            'age': age,
            'mp': mp,
        } 

        #----- get image report from file IMG00000 -----  
        # get image and save to report
        # pydicom example: https://goo.gl/SMyny4
        zscore=[]
        tscore=[]
        if myfile.startswith('IMG00000'):
            if cv2.imwrite('media/DCM/JPG/IMG00000_report.jpg', dataset.pixel_array):
                # must add a '/' ahead
                response['report'] = '/media/DCM/JPG/IMG00000_report.jpg'

        #----- get zscore, tscore from file STR00000 -----
        # read STR00000
        elif myfile.startswith('STR00000'):       
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

            response['zscore'] = zscore
            response['tscore'] = tscore

        uploaded_file_url = fs.url(myfile)
        response['uploaded_file_url'] = uploaded_file_url

        return render(request, 'core/upload_dcm.html', response)
    else:
        return render(request, 'core/upload_dcm.html')
        
def upload_zip(request):
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        myZipFile = fs.save(myfile.name, myfile)
        request.session['myZipFile']=myZipFile
        print('myZipFile:' + myZipFile)

        print(os.getcwd())

        # move file form media/ to media/dcm/ folder
        shutil.move('media/'+myZipFile, 'media/ZIP/'+myZipFile)
        # read zip file
        zip_file = zipfile.ZipFile(os.path.join(os.getcwd(), 'media/ZIP/', myZipFile))
        # extract zip file
        for file in zip_file.namelist():
            zip_file.extract(file, os.path.join(os.getcwd(), 'media/ZIP/'))
        
        # get folder name of the extracted zip file
        zipFolder = list(myZipFile)[:-4] #remove '.zip'
        zipFolder = ''.join(zipFolder)
        print('zipFolder: '+zipFolder)
        zipFilePath = 'media/ZIP/' + zipFolder

        response={
            'myZipFile': myZipFile,
            'zipFilePath': zipFilePath,
        }

        # directory tree
        dir_tree = []
        # contain '.dcm' files 
        file_tree = []
        # traverse root directory, and list directories as dirs and files as files
        for root, dirs, files in os.walk(zipFilePath):
            path = root.split(os.sep)
            line = ((len(path) - 1) * '---', os.path.basename(root))
            line = ''.join(line)
            dir_tree.append(line)
            file_tree.append('')
            for file in files:
                line = (len(path) * '---', file)
                line = ''.join(line)
                dir_tree.append(line)
                file_tree.append(file)
        response['dir_tree'] = dir_tree
        response['file_tree'] = file_tree
        # zip so that templates can show
        file_dir_list = zip(dir_tree, file_tree)
        response['file_dir_list'] = file_dir_list

        #TODO: fix url
        response['uploaded_file_url'] = fs.url(myZipFile)
        
        return render(request, 'core/upload_zip.html', response)
    else: 
        return render(request, 'core/upload_zip.html')

def show_zip(request):
    print('----show zip----')
    print(os.getcwd())
    zipFolder = request.session['myZipFile']
    zipFolder = list(zipFolder)[:-4] # remove '.zip'
    zipFolder = ''.join(zipFolder)
    print('zipFolder: '+zipFolder)

    # get the file name user clicked from template
    myfile = request.GET.get('file', None)
    print('myfile: '+myfile)

    if myfile.startswith('STR'):
        filePath = 'media/ZIP/' + zipFolder + '/SDY00000/' + myfile
        print('STRfilePath: '+ filePath)
    elif myfile.startswith('IMG'):
        filePath = 'media/ZIP/' + zipFolder + '/SDY00000/SRS00000/' + myfile
        print('IMGfilePath: '+ filePath)

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

    response={
        'pid': pid,
        'sex': sex,
        'age': age,
        'mp': mp,
    }

    # ----- Judge from myfile, get value or image -----
    zscore=[]
    tscore=[]
    report=''
    fileName = list(myfile)[:-4] #remove '.dcm'
    fileName = ''.join(fileName)
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

        response['zscore'] = zscore
        response['tscore'] = tscore
    
    
    # get image and save to report from file IMG
    # pydicom example: https://goo.gl/SMyny4
    elif fileName.startswith('IMG'):      
        # TODO: imshow instead of imwrite? two views?
        if cv2.imwrite('media/ZIP/JPG/' + fileName + '_report.jpg', dataset.pixel_array):
            response['report'] = '/media/ZIP/JPG/' + fileName + '_report.jpg'

    print(response)
    return render(request, 'core/show_zip.html', response)

def model_form_upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        # check if the input is valid
        if form.is_valid(): 
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

    if request.method == 'POST':
        selected = request.POST.getlist('selected')
        result=''
        response={}
        for files in selected:
            os.remove('media/DCM/' + files)

            # check if the file has corresponding report, if yes, remove as well  
            fileName = list(files)[:-4] # remove '.dcm'
            fileName = ''.join(fileName)
            myReport = fileName + '_report.jpg'
            dir_list = os.listdir('media/DCM/JPG/')
            if myReport in dir_list:
                os.remove('media/DCM/JPG/' + myReport)
            
            result+=fileName + ' '
            response['result'] = result
        return render(request, 'core/result.html', response)

    return render(request, 'core/manage_dcm.html', {
        'onlyfiles': onlyfiles,
    })

def show_dcm(request):

    # get the file user clicked from template
    myfile = request.GET.get('file', None)
    request.session['myfile'] = myfile

    # filePath preprocess
    filePath = 'media/DCM/' + myfile
    request.session['filePath'] = filePath

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

    response={
        'filePath': filePath,
        'pid': pid,
        'sex': sex,
        'age': age,
        'mp': mp,
    }

    # ----- Judge from filename, get value or image -----
    zscore=[]
    tscore=[]
    report=''
    fileName = list(myfile)[:-4] #remove '.dcm'
    fileName = ''.join(fileName)
    
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

        response['zscore'] = zscore
        response['tscore'] = tscore

    # get image and save to report from file IMG
    # pydicom example: https://goo.gl/SMyny4
    elif fileName.startswith('IMG'):      
        if cv2.imwrite('media/DCM/JPG/' + fileName + '_report.jpg', dataset.pixel_array):
            response['report'] = '/media/DCM/JPG/' + fileName + '_report.jpg'
    return render(request, 'core/show_dcm.html', response)

def manage_zip(request):

    folderPath = 'media/ZIP/'

    # list files in the folder
    onlyfiles = [f for f in listdir(folderPath) if isfile(join(folderPath, f))]

    return render(request, 'core/manage_zip.html', {
        'onlyfiles': onlyfiles,
    })

def rename(request):
    # get file name from show_DCM
    myfile = request.session['myfile']
    fileName = list(myfile)[:-4] # remove '.dcm'
    fileName = ''.join(fileName)
    myReport = fileName + '_report.jpg'

    if request.method == 'POST':
        form=nameForm(request.POST)
        response={}
        if form.is_valid():
            name=form.cleaned_data['rename']
            response['result']=name
            os.rename('media/DCM/' + myfile, 'media/DCM/' + name)

            # check if the file has corresponding report, if yes, rename as well
            dir_list = os.listdir('media/DCM/JPG/')
            if myReport in dir_list:
                name = list(name)[:-4] # remove '.dcm'
                name = ''.join(name)
                os.rename('media/DCM/JPG/' + myReport, 'media/DCM/JPG/' + name + '_report.jpg')
        return render(request, 'core/result.html', response)
    else:
        return render(request, 'core/result.html')

def remove(request):
    # get file name from show_DCM
    myfile = request.session['myfile']
 
    if request.method == 'POST':
        response={}
        response['result']=myfile
        os.remove('media/DCM/' + myfile)
        return render(request, 'core/result.html', response)
    else:
        return render(request, 'core/result.html')

def download(request):
    # get file path from show_DCM
    filePath = request.session['filePath']

    if request.method == 'POST':
        if os.path.exists(filePath):
            with open(filePath, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/dicom")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(filePath)
                return response
        else:
            return render(request, 'core/show_dcm.html')
    else:
        return render(request, 'core/show_dcm.html')



