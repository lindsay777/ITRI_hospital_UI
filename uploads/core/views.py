# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseRedirect
from .models import PATIENT, FRAX, LVA, APSPINE, DUALFEMUR, COMBINATION

from uploads.core.models import Document
from uploads.core.forms import nameForm

from os import listdir
from os.path import isfile, join

import matplotlib.pyplot as plt
import pydicom
import zipfile
import cv2
import os
import shutil
import time
import re
from datetime import datetime
from pydicom.data import get_testdata_files

import io
from django.http import FileResponse
from reportlab.pdfgen import canvas

# variable naming principle:
# myfile: .dcm
# myZipFile: .zip
# zipFolder: folder
# fileName: no .dcm

# session:
# upload_zip: myZipFile, pid
# show_dcm/ manage_show_zip: myfile

#TODO: TBS

def home(request):
    return render(request, 'core/home.html')

def patient_data(filepath, saveType):
    # read file
    dataset = pydicom.dcmread(filepath)

    # add upload time
    datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pid = dataset.PatientID
    name = str(dataset.PatientName)
    sex = dataset.PatientSex
    # get age (ex. 063Y->63)
    age_list = list(dataset.PatientAge)
    del age_list[-1]
    if age_list[0]=='0':
        del age_list[0]
    age = int(''.join(age_list))
    # get MP
    PatientName = str(dataset.PatientName)
    if "(PM" in PatientName:
        PatientName = PatientName.split('(')[1].split(')')[0]
        name_list = list(PatientName)
        del name_list[0:2]
        mp = ''.join(name_list)
    else:
        mp = ''
    response={
        'pid': pid,
        'name': name,
        'sex': sex,
        'age': age,
        'mp': mp,
        'dataset': dataset,
        'dateTime': datetime_str,
    }
    if saveType == 'uploadZIP':
        file_path = '/media/ZIP/' + pid
        # save to DB
        fileInstance = PATIENT(pid=pid, file_path=file_path, pub_date=datetime_str, name=name, sex=sex, age=age, mp=mp)
        fileInstance.save()
    else:
        print('file does not save to DB')
    return response

def str_data(dataset, saveType):
    response = {}
    pid = dataset.PatientID
    comment = dataset.ImageComments
    comment = comment.split('><')

    match = [s for s in comment if "SCAN type" in s]
    length = len(match)

    # 02 frax: major fracture
    if length == 0:
        response['scanType'] = 'FRAX'
        majorFrac = [s for s in comment if "MAJOR_OSTEO_FRAC_RISK units" in s]
        majorFrac = ''.join(majorFrac)
        if majorFrac == '':
            majorFrac = '(None)'
        else:        
            majorFrac = majorFrac.split('</')[0].split('>')[1]
        response['majorFrac'] = majorFrac
        # get hip frac
        hipFrac = [s for s in comment if "HIP_FRAC_RISK units" in s]
        hipFrac = ''.join(hipFrac)
        if hipFrac == '':
            hipFrac = '(None)'
        else:
            hipFrac = hipFrac.split('</')[0].split('>')[1]
        response['hipFrac'] = hipFrac

        if saveType == 'uploadZIP':
            # save to DB
            fileInstance = FRAX(pid=pid, scantype='FRAX', majorFracture=majorFrac, hipFracture=hipFrac)
            fileInstance.save()
        else:
            print('file does not save to DB')
    # at least one scanType:
    else:
        comments = t_z_r(comment)
        response['tscore'] = comments['str_tscore']
        response['zscore'] = comments['str_zscore']
        response['region'] = comments['str_region']
        tscore = comments['tscore']
        zscore = comments['zscore']
        region = comments['region']
        
        # classify through scanType
        if length == 1:
            scanType = ''.join(match)
            scanType = scanType.split('"')[1]
            response['scanType'] = scanType
            # LVA
            if scanType == 'LVA':
                keyword = [s for s in comment if "DEFORMITY" in s]
                lva=[]
                for substring in keyword:
                    substring = substring.split('</')[0].split('>')[1]
                    if substring != 'None':
                        lva.append(substring)
                response['lva'] = lva
                if saveType == 'uploadZIP':
                    # save to DB
                    fileInstance = LVA(pid=pid, scantype=scanType, lva=lva)
                    fileInstance.save()
                else:
                    print('file does not save to DB')
            # AP Spine
            elif scanType == 'AP Spine':
                APSpine = ''
                for i in range(len(tscore)):
                    if APSpine == '':
                        APSpine += '(' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')'
                    else:
                        APSpine += ', (' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')' 
                response['APSpine'] = APSpine
                if saveType == 'uploadZIP':
                    # save to DB
                    fileInstance = APSPINE(pid=pid, scantype=scanType, tscore=tscore, zscore=zscore, region=region, apspine=APSpine)
                    fileInstance.save()
                else:
                    print('file does not save to DB')

            # Dual Femur
            elif scanType == 'DualFemur':
                DualFemur = ''
                for i in range(len(tscore)):
                    if DualFemur == '':
                        DualFemur += '(' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')'
                    else:
                        DualFemur += ', (' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')' 
                response['DualFemur'] = DualFemur
                if saveType == 'uploadZIP':
                    # save to DB
                    fileInstance = DUALFEMUR(pid=pid, scantype=scanType, tscore=tscore, zscore=zscore, region=region, dualfemur=DualFemur)
                    fileInstance.save()
                else:
                    print('file does not save to DB')
            else:
                print('error input')
        # multi scanType: combination
        elif length == 2:
            scanType = 'combination'
            response['scanType'] = scanType
            del region[1:-4]
            combination = ''
            for i in range(len(tscore)):
                if combination == '':
                    combination += '(' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')'
                else:
                    combination += ', (' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')' 
            response['combination'] = combination
            # get APSpine
            APSpine = ''
            for i in range(len(tscore)):
                if APSpine == '':
                    APSpine += '(' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')'
                else:
                    APSpine += ', (' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')' 
            response['APSpine'] = APSpine
            # get DualFemur
            DualFemur = ''
            for i in range(len(tscore)):
                if DualFemur == '':
                    DualFemur += '(' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')'
                else:
                    DualFemur += ', (' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')' 
            response['DualFemur'] = DualFemur
            # # get T7
            # T7 = [s for s in comment if "DEFORMITY" in s]
            # T7 = ''.join(T7)
            # T7 = T7.split('</')[0].split('>')[1]
            # response['T7'] = T7

            if saveType == 'uploadZIP':
                # save to DB
                fileInstance = COMBINATION(pid=pid, scantype=scanType, tscore=tscore, zscore=zscore, region=region, lva='None', apspine=APSpine, dualfemur=DualFemur, combination=combination, t7='None')
                fileInstance.save()
            else:
                print('file does not save to DB')

        # multi scanType: combination
        elif length == 3:
            scanType = 'combination'
            response['scanType'] = scanType
            del region[1:-4] #TODO: zip file with lva
            combination = ''
            for i in range(len(tscore)):
                if combination == '':
                    combination += '(' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')'
                else:
                    combination += ', (' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')' 
            response['combination'] = combination
            # get LVA
            keyword = []
            keyword = [s for s in comment if "DEFORMITY" in s]
            lva=[]
            for substring in keyword:
                substring = substring.split('</')[0].split('>')[1]
                lva.append(substring)
            while 'None' in lva:
                lva.remove(substring)
            response['lva'] = lva
            # get APSpine
            APSpine = ''
            for i in range(len(tscore)):
                if APSpine == '':
                    APSpine += '(' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')'
                else:
                    APSpine += ', (' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')' 
            response['APSpine'] = APSpine
            # get DualFemur
            DualFemur = ''
            for i in range(len(tscore)):
                if DualFemur == '':
                    DualFemur += '(' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')'
                else:
                    DualFemur += ', (' + region[i] + ',' + tscore[i] + ',' + zscore[i] +')' 
            response['DualFemur'] = DualFemur
            # get T7
            T7 = [s for s in comment if "DEFORMITY" in s]
            T7 = ''.join(T7)
            T7 = T7.split('</')[0].split('>')[1]
            response['T7'] = T7

            if saveType == 'uploadZIP':
                # save to DB
                fileInstance = COMBINATION(pid=pid, scantype=scanType, tscore=tscore, zscore=zscore, region=region, lva=lva, apspine=APSpine, dualfemur=DualFemur, combination=combination, t7=T7)
                fileInstance.save()
            else:
                print('file does not save to DB')
    return response

def t_z_r(comment):
    comments = {}
    match_tscore = [s for s in comment if "BMD_TSCORE" in s]
    tscore=[]
    for substring in match_tscore:
        substring = substring.split('</')[0].split('>')[1]
        tscore.append(substring)
    comments['tscore'] = tscore

    match_zscore = [s for s in comment if "BMD_ZSCORE" in s]
    zscore=[]
    for substring in match_zscore:
        substring = substring.split('</')[0].split('>')[1]
        zscore.append(substring)
    comments['zscore'] = zscore

    match_region = [s for s in comment if "ROI region" in s]
    region=[]
    for substring in match_region:
        substring = substring.split('"')[1]
        region.append(substring)
    comments['region'] = region

    comments['str_region'] = ', '.join(region)
    comments['str_tscore'] = ', '.join(tscore)
    comments['str_zscore'] = ', '.join(zscore)

    return comments

def main_upload(request):
    return render(request, 'core/main_upload.html')

def upload_dcm(request):
    if request.method == 'POST' and request.FILES['myfile']:
        response = {}
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        myfile = fs.save(myfile.name, myfile)
        fileName = ''.join(list(myfile)[:-4])

        # get file list in the folder
        onlyfiles = [f for f in listdir('media/DCM/') if isfile(join('media/DCM/', f))]
        # if the file name already exists, show warning
        if myfile in onlyfiles:
            os.remove('media/'+myfile)
            response = {
                'warning':myfile
            }
            return render(request, 'core/upload_dcm.html', response)
        
        else:
            # move file form media/ to media/dcm/ folder
            shutil.move('media/'+myfile, 'media/DCM/'+myfile)
            dcmFilePath = 'media/DCM/' + myfile

            # patient_data
            data = patient_data(dcmFilePath, 'dcm')
            dataset = data['dataset']
            response.update(data)

            # ----- get image report from IMG file -----  
            # pydicom example: https://goo.gl/SMyny4
            try:
                dataset.pixel_array
                if cv2.imwrite('media/DCM/JPG/' + fileName + '_report.jpg', dataset.pixel_array):
                    # must add a '/' ahead
                    response['report'] = '/media/DCM/JPG/' + fileName + '_report.jpg'

            # -------- get value from STR file --------
            except:   
                # str_data
                response.update(str_data(dataset, 'dcm'))

            uploaded_file_url = fs.url(myfile)
            response['uploaded_file_url'] = uploaded_file_url

        return render(request, 'core/upload_dcm.html', response)
    else:
        return render(request, 'core/upload_dcm.html')
        
def zip_process(myZipFile, zipFolder):
    response={}
    # get file list in the folder
    onlyfiles = [f for f in listdir('media/ZIP/') if isfile(join('media/ZIP/', f))]

    DCMFiles = []
    # read zip file
    zip_file = zipfile.ZipFile(os.path.join(os.getcwd(), 'media/', myZipFile))
    # extract zip file
    for _file in zip_file.namelist():
        zip_file.extract(_file, os.path.join(os.getcwd(), 'media/'))
        if ".dcm" in _file.lower():
            DCMFiles.append(_file)
    zip_file.close()
    
    # if the filename(pid.zip) already exists, show warning
    dcmFilePath = 'media/' + str(DCMFiles[-1])
    pid = pydicom.dcmread(dcmFilePath).PatientID + '.zip'

    if pid in onlyfiles:
        os.remove('media/'+myZipFile)
        shutil.rmtree('media/'+zipFolder)
        response = {
            'warning_origin':myZipFile,
            'warning_pid':pid
        }
    else:
        # move file from media/ to media/zip/ folder
        shutil.move('media/'+myZipFile, 'media/ZIP/'+myZipFile)
        shutil.move('media/'+zipFolder, 'media/ZIP/'+zipFolder)
        # read each file and save to DB
        for file in DCMFiles:
            dcmFilePath = 'media/ZIP/' + file
            dataset = pydicom.dcmread(dcmFilePath)

            try:    # get image report from IMG file
                dataset.pixel_array
                if cv2.imwrite('media/ZIP/JPG/' + file + '_report.jpg', dataset.pixel_array):
                    # must add a '/' ahead
                    response['report'] = '/media/ZIP/JPG/' + file + '_report.jpg'
            except: # get value from STR file
                response.update(str_data(dataset, 'uploadZIP'))

        response.update(patient_data(dcmFilePath, 'uploadZIP'))
        
        #change filename to pid
        os.rename('media/ZIP/' + myZipFile, 'media/ZIP/' + response['pid'] + '.zip')
        os.rename('media/ZIP/' + zipFolder, 'media/ZIP/' + response['pid'])
        
        response['myZipFile'] = myZipFile
    return response

def upload_zip(request):
    if request.method == 'POST' and request.FILES['myfile']:
        response = {}

        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        myZipFile = fs.save(myfile.name, myfile)
        request.session['myZipFile']=myZipFile

        # get folder name of the extracted zip file
        zipFolder = list(myZipFile)[:-4] #remove '.zip'
        zipFolder = ''.join(zipFolder)

        response.update(zip_process(myZipFile, zipFolder))

        if 'warning_origin' in response:
            return render(request, 'core/upload_zip.html', response)
        else:
            request.session['pid'] = response['pid']
            pidFolder = 'media/ZIP/' + response['pid']

            # directory tree
            dir_tree = []
            # contain '.dcm' files 
            file_tree = []
            # traverse root directory, and list directories as dirs and files as files
            for root, dirs, files in os.walk(pidFolder):
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

            response['uploaded_file_url'] = fs.url(myZipFile)
            
            return render(request, 'core/upload_zip.html', response)
    else: 
        return render(request, 'core/upload_zip.html')

def upload_multi_zip(request):
    if request.method == 'POST' and request.FILES.getlist('myfile'):
        start = time.clock()
        response = {}
        errorlist = []
        successlist = []

        myfiles = request.FILES.getlist('myfile')
        fs = FileSystemStorage()

        for myfile in myfiles:
            data={}
            myZipFile = fs.save(myfile.name, myfile)
            # get folder name of the extracted zip file
            zipFolder = list(myZipFile)[:-4] #remove '.zip'
            zipFolder = ''.join(zipFolder)
            data = zip_process(myZipFile, zipFolder)

            try:
                data['warning_origin']
                errorlist.append(data['warning_origin'])     
            except:
                successlist.append(myZipFile)
        response['failed'] = errorlist
        response['success'] = successlist

        response['time'] = time.clock() - start
        response['uploaded_file_url'] = fs.url(myZipFile)  
        return render(request, 'core/upload_multi_zip.html', response)
    else: 
        return render(request, 'core/upload_multi_zip.html')

def upload_multi_in_one_zip(request):
    if request.method == 'POST' and request.FILES['myfile']:
        start = time.clock()
        response = {}
        listFolder = []
        errorlist = []
        successlist = []

        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        myZipFile = fs.save(myfile.name, myfile)
        zipFolder = ''.join(list(myZipFile[:-4]))
        print(myZipFile)
        print(zipFolder)

        # read zip file
        zip_file = zipfile.ZipFile(os.path.join(os.getcwd(), 'media/', myZipFile))
        print(zip_file.namelist())
        # extract zip file
        for _file in zip_file.namelist():
            zip_file.extract(_file, os.path.join(os.getcwd(), 'media/'))
        zip_file.close()

        # get folders
        extractFolder = 'media/' + zipFolder
        for folders in os.listdir(extractFolder):
            listFolder.append(folders)
        print('listFolder', listFolder)

        onlyfiles = []
        # get file list in the folder
        for f in os.listdir('media/ZIP/'):
            onlyfiles.append(f)
        print('onlyfiles', onlyfiles)

        DCMFiles = []
        for _folders in listFolder:
            DCMFiles = []
            folders = extractFolder + '/' + _folders
            print('_folders', _folders)
            print('folders', folders)

            # get dataset
            # if the zip file has normal constructure
            if os.path.isdir(folders + '/SDY00000/'):
                tag = 'normal_folder'
                strFolderPath = folders + '/SDY00000/'
                for _file in os.listdir(strFolderPath):
                    print(_file)
                    if ".dcm" in _file.lower():
                        DCMFiles.append('/SDY00000/' + _file)
                pid = pydicom.dcmread(folders + DCMFiles[0]).PatientID
            # if the file has abnormal folder constructure
            else:
                tag = 'abnormal_folder'
                for _path in os.listdir(folders):
                    print('_path', _path)
                    _file_dir = os.path.join(folders, _path)
                    for path_ in os.listdir(_file_dir):
                        print('path_', path_)
                        file_dir = os.path.join(_file_dir, path_)
                        for path in os.listdir(file_dir):
                            print('path', path)
                            filePath = os.path.join(file_dir, path)
                            dataset = pydicom.dcmread(filePath)
                            try:
                                dataset.ImageComments
                                DCMFiles.append(filePath)
                            except:
                                print('not str dcm file')
                print(_file_dir)
                print(file_dir)
                print(filePath)
                pid = pydicom.dcmread(filePath).PatientID

            print('DCMFiles')
            print(DCMFiles)
            print(pid)
            print('---------------------------------------')
            # rename from pid
            if pid in onlyfiles:
                shutil.rmtree(folders)
                errorlist.append(_folders)
            else:
                # move file from media/ to media/zip/ folder
                shutil.move('media/'+zipFolder+'/'+_folders, 'media/ZIP/'+_folders)
                # read each file and save to DB
                for _file in DCMFiles:
                    print('_file',_file)
                    dcmFilePath = 'media/ZIP/' + _folders + _file
                    dataset = pydicom.dcmread(dcmFilePath)
                    try:    # get image report from IMG file
                        dataset.pixel_array
                        if cv2.imwrite('media/ZIP/JPG/' + _file + '_report.jpg', dataset.pixel_array):
                            # must add a '/' ahead
                            response['report'] = '/media/ZIP/JPG/' + _file + '_report.jpg'
                    except: # get value from STR file
                        response.update(str_data(dataset, 'uploadZIP'))

                response.update(patient_data(dcmFilePath, 'uploadZIP'))
                
                #change filename to pid
                os.rename('media/ZIP/' + _folders, 'media/ZIP/' + pid)

                successlist.append(_folders)
                
        os.remove('media/' + myZipFile)
        shutil.rmtree('media/' + zipFolder)

        response['failed'] = errorlist
        response['success'] = successlist

        response['time'] = time.clock() - start
        response['uploaded_file_url'] = fs.url(myZipFile)  
        return render(request, 'core/upload_multi_in_one_zip.html', response)
    else: 
        return render(request, 'core/upload_multi_in_one_zip.html')

def show_zip(request):
    response = {}
    zipFile = request.session['myfile']
    pid = ''.join(list(zipFile[:-4]))
    # get the file name user clicked from template
    myfile = request.GET.get('file', None)
    fileName = list(myfile)[:-4] # remove '.zip'
    fileName = ''.join(fileName)   

    if myfile.startswith('STR'):
        filePath = 'media/ZIP/' + pid + '/SDY00000/' + myfile
    elif myfile.startswith('IMG'):
        filePath = 'media/ZIP/' + pid + '/SDY00000/SRS00000/' + myfile
    else:
        _file_dir = os.getcwd() + '/media/ZIP/' + pid
        if fileName in os.listdir(_file_dir):
            filePath = os.path.join(_file_dir, myfile)
        else:
            for path in os.listdir(_file_dir):
                file_dir = os.path.join(_file_dir, path)
                if myfile in os.listdir(file_dir):
                    filePath = os.path.join(file_dir, myfile)
            
    # read file
    data = patient_data(filePath, 'zip')
    dataset = data['dataset']
    response.update(data)

    # ----- get image report from IMG file -----  
    # pydicom example: https://goo.gl/SMyny4
    try:
        dataset.pixel_array
        if cv2.imwrite('media/ZIP/JPG/' + fileName + '_report.jpg', dataset.pixel_array):
            # must add a '/' ahead
            response['report'] = '/media/ZIP/JPG/' + fileName + '_report.jpg'

    # -------- get value from STR file --------
    except:
        response.update(str_data(dataset, 'zip'))

    return render(request, 'core/show_zip.html', response)

def main_manage(request):
    return render(request, 'core/main_manage.html')

def manage_dcm(request): #remove
    folderPath = 'media/DCM/'
    # list files in the folder
    onlyfiles = [f for f in listdir(folderPath) if isfile(join(folderPath, f))]
    # remove selected files
    if request.method == 'POST':
        selected = request.POST.getlist('selected')
        result = '' 
        response = {}
        for files in selected:
            os.remove(folderPath + files)

            # check if the file has corresponding report, if yes, remove as well  
            fileName = list(files)[:-4] # remove '.dcm'
            fileName = ''.join(fileName)
            myReport = fileName + '_report.jpg'
            dir_list = os.listdir(folderPath + 'JPG/')
            if myReport in dir_list:
                os.remove(folderPath + 'JPG/' + myReport)
            
            result += fileName + ' '
            response['result'] = result
        return render(request, 'core/result.html', response)

    return render(request, 'core/manage_dcm.html', {
        'onlyfiles': onlyfiles,
    })

def show_dcm(request): #remove
    response = {}

    if request.method == 'POST':
        remove(request.session['myfile'], 'dcm')
        response['result'] = request.session['myfile']
        return render(request, 'core/result.html', response)

    # get the file user clicked from template
    myfile = request.GET.get('file', None)
    request.session['myfile'] = myfile    

    fileName = list(myfile)[:-4] # remove '.dcm'
    fileName = ''.join(fileName)

    # filePath preprocess
    filePath = 'media/DCM/' + myfile
    request.session['filePath'] = filePath

    # patient_data & upload to DB
    data = patient_data(filePath, 'dcm')
    dataset = data['dataset']
    response.update(data)

    # ----- get image report from IMG file -----  
    # pydicom example: https://goo.gl/SMyny4
    # if dataset.pixel_array in dataset.dict:
    try:
        dataset.pixel_array
        if cv2.imwrite('media/DCM/JPG/' + fileName + '_report.jpg', dataset.pixel_array):
            # must add a '/' ahead
            response['report'] = '/media/DCM/JPG/' + fileName + '_report.jpg'

    # -------- get value from STR file --------
    except:
        # str_data & upload to DB
        response.update(str_data(dataset, 'dcm'))

    return render(request, 'core/show_dcm.html', response)

def manage_zip(request): #remove
    response={}
    # select files to remove
    if request.method == 'POST':
        checked = request.POST.getlist('checked')
        if len(checked) > 1:
            remove(checked, 'multiZIP')
        else:
            remove(checked, 'zip')
        response['result'] = checked
        return render(request, 'core/result.html', response)
    # get patient data from DB
    patients = PATIENT.objects.all()

    return render(request, 'core/manage_zip.html', {'patients': patients})

def manage_show_zip(request): 
    response={}
    if request.method == 'POST':    #remove
        remove(request.session['myfile'], 'zip')
        response['result'] = request.session['myfile']
        return render(request, 'core/result.html', response)

    # get the file name user clicked from template
    myfile = request.GET.get('file', None)
    request.session['myfile'] = myfile + '.zip'
    zipFilePath = 'media/ZIP/' + myfile
    request.session['filePath'] = zipFilePath + '.zip'
    
    response={
        'myZipFile': myfile,
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

    response['uploaded_file_url'] = myfile
    
    return render(request, 'core/manage_show_zip.html', response)

def check_apspine(request):
    # get the file name user clicked from template
    pidFolder = ''.join(list(request.session['myfile'])[:-4])
    response={}
    listFilesDCM = []
    tag = ''
    file_apspine=''
    file_lva=''
    zipFilePath = 'media/ZIP/' + pidFolder

    # if the zip file has normal constructure
    if os.path.isdir(zipFilePath + '/SDY00000/'):
        tag = 'normal_folder'
        strFolderPath = zipFilePath + '/SDY00000/'
        # recognize files through dataset
        # get list of the directory
        onlyFiles = os.listdir(strFolderPath)
        # get only 'str' files from the list
        for files in onlyFiles:
            if "STR" in files:
                listFilesDCM.append(files)

    # if the file has abnormal folder constructure
    else:
        tag = 'abnormal_folder'
        _file_dir = os.getcwd() + '/media/ZIP/' + pidFolder
        for _path in os.listdir(_file_dir):
            file_dir = os.path.join(_file_dir, _path)
            for path in os.listdir(file_dir):
                filePath = os.path.join(file_dir, path)
                dataset = pydicom.dcmread(filePath)
                try:
                    dataset.ImageComments
                    listFilesDCM.append('/' + path)
                    strFolderPath = file_dir.replace(os.getcwd(),'')
                    strFolderPath = ''.join(list(strFolderPath)[1:])
                    strFolderPath = strFolderPath.replace('\\','/')
                except:
                    print('not str dcm file')
    
    # browse through each file, search from dataset(scantype), and recognize the information(datatype)
    for files in listFilesDCM:
        filesPath = strFolderPath + files
        dataset = pydicom.dcmread(filesPath)
        comment = dataset.ImageComments
        comment = comment.split('><')

        match = [s for s in comment if "SCAN type" in s]
        length = len(match)

        # no scanType: major fracture
        if length == 0:
            file_frax = files
            scanType = 'Frax'
            response['scanType'] = scanType
        
        # at least one scanType:
        else:           
            # classify through scanType
            if length == 1:
                scanType = ''.join(match)
                scanType = scanType.split('"')[1]
                response['scanType'] = scanType
                # LVA
                if scanType == 'LVA':
                    file_lva = files
                # AP Spine
                elif scanType == 'AP Spine':
                    file_apspine = files
                # Dual Femur
                elif scanType == 'DualFemur':
                    file_dualfemur = files
                else:
                    print('error input')

            # multi scanType: combination
            else:
                file_combination = files
                scanType = 'combination'
                response['scanType'] = scanType
    
    # step 2: Obtain APspine
    if file_apspine=='':
        response['result_warn'] = 'Insufficient file resources: AP Spine'
        return render(request, 'core/check_apspine.html', response)
    
    if tag == 'normal_folder':
        apspineFilePath = 'media/ZIP/' + pidFolder + '/SDY00000/' + file_apspine
    else:
        apspineFilePath = strFolderPath + file_apspine

    # read file
    dataset = pydicom.dcmread(apspineFilePath)

    comment = dataset.ImageComments
    comment = comment.split('><')
    comments = t_z_r(comment)

    response['region'] = comments['str_region']
    response['tscore'] = comments['str_tscore']
    response['zscore'] = comments['str_zscore']
    region = comments['region']
    tscore = comments['tscore']
    zscore = comments['zscore']

    data = patient_data(apspineFilePath, 'zip')
    response.update(data)
    
    # decide group
    age = int(data['age'])
    mp = data['mp']
    sex = data['sex']

    if age<20:
        group = 'Z'
    elif 20<=age<50:
        if mp == '':
            group = 'Z'
        else:
            if sex == 'F':
                group = 'T'
            else:
                group = 'Z'
    else:
        if mp == '':
            if sex == 'F':
                group = 'Z'
            else:
                group = 'T'
        else:
            group = 'T'
    response['group'] = group

    merge = list(zip(region, tscore, zscore))

    # get the outcome from the machine
    machineMerge = merge[4:]

    machineOutcome = ''
    list_machineOutcome =[]
    for substring in machineMerge:
        if machineOutcome == '':
            machineOutcome = str(substring[0])
        else:
            machineOutcome = machineOutcome + ', ' + str(substring[0])
        list_machineOutcome.append(substring[0])
    response['machineOutcome'] = machineOutcome

    merge = merge[:4]

    # sort(according to tscore or zscore)
    def getT(item):
        return float(item[1])
    def getZ(item):
        return float(item[2])

    if group == 'T':
        merge = sorted(merge, key=getT)     
        # get mean and absolute value
        mean = (float(merge[1][1]) + float(merge[2][1]))/2
        dist1 = abs(float(merge[0][1]) - mean)
        dist2 = abs(mean - float(merge[3][1]))
        response['mean'] = mean
        response['dist1'] = dist1
        response['dist2'] = dist2
    elif group:
        merge = sorted(merge, key=getZ)
        # get mean and absolute value
        mean = (float(merge[1][2]) + float(merge[2][2]))/2
        dist1 = abs(float(merge[0][2]) - mean)
        dist2 = abs(mean - float(merge[3][2]))
        response['mean'] = mean
        response['dist1'] = dist1
        response['dist2'] = dist2

    # regionFilter: remove outlier
    regionFilter = ['L1','L2','L3','L4']
    if dist1 > 1:
        regionFilter.remove(merge[0][0])
    if dist2 > 1:
        regionFilter.remove(merge[3][0])
    response['regionFilter'] = ', '.join(regionFilter)

    # deal with value in '()'
    start = regionFilter[0]
    end = regionFilter[-1]
    region = ['L1','L2','L3','L4']
    index1 = region.index(start)
    index2 = region.index(end)
    region = region[index1:index2+1]
    diffRegion = ','.join([item for item in region if item not in regionFilter])

    if diffRegion == '':
        outcome = str(start + '-' + end)
    else:
        outcome = str(start + '-' + end + '(' + diffRegion + ')')
    list_outcome = ''.join(list(outcome))
    response['outcome'] = outcome
    
    # check the result to determine re-gen or not
    if list_outcome in list_machineOutcome:
        # step 4: Obtain LVA
        if file_lva=='':
            response['result_warn'] = 'Insufficient file resources: LVA'
            return render(request, 'core/check_apspine.html', response)
        if tag == 'normal_folder':
            lvaFilePath = 'media/ZIP/' + pidFolder + '/SDY00000/' + file_lva
        else:
            lvaFilePath = strFolderPath + file_lva
        # read file
        dataset = pydicom.dcmread(lvaFilePath)
        comment = dataset.ImageComments
        comment = comment.split('><')

        # get region
        region4 = [s for s in comment if "ROI region" in s]
        region=[]
        for substring in region4:
            substring = substring.split('"')[1]
            region.append(substring)
        # get deformity    
        keyword4 = [s for s in comment if "DEFORMITY" in s]
        lva=[]
        for substring in keyword4:
            substring = substring.split('</')[0].split('>')[1]
            lva.append(substring)
        # zip two feature
        merge = list(zip(region, lva))

        # get outcome
        lvagrade = ''
        for substring in merge:
            if substring[1] != 'None':
                if lvagrade == '':
                    lvagrade = '(' + substring[0] + ', ' + substring[1] + ')'
                else:
                    lvagrade += ', ' + '(' + substring[0] + ', ' + substring[1] + ')'
        response['grade'] = lvagrade

        # step 4: Obtain FRAX
        if file_frax=='':
            response['result_warn'] = 'Insufficient file resources: frax'
            return render(request, 'core/check_apspine.html', response)
        if tag == 'normal_folder':
            fraxFilePath = 'media/ZIP/' + pidFolder + '/SDY00000/' + file_frax
        else:
            fraxFilePath = strFolderPath + file_frax
        # read file
        dataset = pydicom.dcmread(fraxFilePath)
        comment = dataset.ImageComments
        comment = comment.split('><')

        # get major frac
        majorFrac = [s for s in comment if "MAJOR_OSTEO_FRAC_RISK units" in s]
        majorFrac = ''.join(majorFrac)
        majorFrac = majorFrac.split('</')[0].split('>')[1]
        response['majorFrac'] = majorFrac
        # get hip frac
        hipFrac = [s for s in comment if "HIP_FRAC_RISK units" in s]
        hipFrac = ''.join(hipFrac)
        hipFrac = hipFrac.split('</')[0].split('>')[1]
        response['hipFrac'] = hipFrac

        response['result_correct'] = 'Correct'

        #TODO: Object of type 'bytes' is not JSON serializable
        #request.session['reportVar'] = response['group']
        # for key in list(response.keys()):
        #     request.session[key] = response[key]
            # print(key)

        # must add after session
        response.update(data)
        return render(request, 'core/check_apspine.html', response)

    else:
        response['result_warn'] = 'Warn!! Please Re-gen.'

    return render(request, 'core/check_apspine.html', response)

def statistics(request):
    return render(request, 'core/statistics.html')
    
def report(request):
    reportVar = request.session['reportVar']
    print(reportVar)
    reportText = "Average bone mineral density(BMD) of L1 to L4 is " + reportVar['group'] + "gm/cm2, "
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="somefilename.pdf"'

    # Create the PDF object, using the response object as its "file."
    p = canvas.Canvas(response)

    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    p.drawString(90, 750, reportText)

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    return response

def rename(request):
    # get file name from show_DCM/manage_show_zip
    myfile = request.session['myfile']
    # get file type (dcm or zip)
    fileType = list(myfile)[-3:]
    fileType = ''.join(fileType)
    # remove '.dcm'
    fileName = list(myfile)[:-4]
    fileName = ''.join(fileName)
    myReport = fileName + '_report.jpg'

    if request.method == 'POST':
        form=nameForm(request.POST)
        response={}
        if form.is_valid():
            name=form.cleaned_data['rename']
            response['result']=name

            folderName = list(name)[:-4]
            folderName = ''.join(folderName)

            if fileType.startswith('zip'):
                os.rename('media/ZIP/' + myfile, 'media/ZIP/' + name)
                os.rename('media/ZIP/' + fileName, 'media/ZIP/' + folderName)

            elif fileType.startswith('dcm'):
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

def remove(myfiles, fileType):
    # if the file is a zip, remove both zip and the extracted folder
    if fileType=='multiZIP':
        for myfile in myfiles:
            # remove from DB
            PATIENT.objects.filter(pid=myfile).delete()
            COMBINATION.objects.filter(pid=myfile).delete()
            DUALFEMUR.objects.filter(pid=myfile).delete()
            FRAX.objects.filter(pid=myfile).delete()
            LVA.objects.filter(pid=myfile).delete()
            APSPINE.objects.filter(pid=myfile).delete()
            # remove from folder
            os.remove('media/ZIP/' + myfile + '.zip')
            shutil.rmtree('media/ZIP/' + myfile)
    elif fileType=='zip':
        myfiles = myfiles[0]
        # remove from DB
        PATIENT.objects.filter(pid=myfiles).delete()
        COMBINATION.objects.filter(pid=myfiles).delete()
        DUALFEMUR.objects.filter(pid=myfiles).delete()
        FRAX.objects.filter(pid=myfiles).delete()
        LVA.objects.filter(pid=myfiles).delete()
        APSPINE.objects.filter(pid=myfiles).delete()
        # remove from folder
        os.remove('media/ZIP/' + myfiles + '.zip')
        shutil.rmtree('media/ZIP/' + myfiles)
    # if the file is a dcm, remove dcm
    elif fileType=='dcm':
        os.remove('media/DCM/' + myfiles)
        dir_list = os.listdir('media/DCM/JPG/')
        fileName = list(myfiles)[:-4]
        fileName = ''.join(fileName)
        reportName = fileName + '_report.jpg'
        if reportName in dir_list:
            os.remove('media/DCM/JPG/' + reportName)
    else:
        print('Wrong File Type!!!')

def download(request):
    # get file path from show_DCM/manage_show_zip
    filePath = request.session['filePath']
    # get file name from show_DCM/manage_show_zip
    myfile = request.session['myfile']
    # get file type (dcm or zip)
    fileType = list(myfile)[-3:] 
    fileType = ''.join(fileType)
    if request.method == 'POST':
        if os.path.exists(filePath):
            with open(filePath, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/dicom")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(filePath)
                return response
        else:
            if fileType.startswith('dcm'):
                return render(request, 'core/show_dcm.html')
            elif fileType.startswith('zip'):
                return render(request, 'core/manage_show_zip.html')
