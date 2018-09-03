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

# variable naming principle:
# myfile: .dcm
# myZipFile: .zip
# zipFolder: folder
# fileName: no .dcm

# session:
# upload_zip: myZipFile
# show_dcm/ manage_show_zip: myfile

#TODO: TBS
#TODO: MANAGE_ZIP: multi file process
#check if getting data is not from filename
#template 

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

def patient_data(dataset):
    data={}
    # get patient's ID
    pid = dataset.PatientID
    # get name
    name = dataset.PatientName
    # get sex
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
    data={
        'pid': pid,
        'name': name,
        'sex': sex,
        'age': age,
        'mp': mp,
    }
    return data

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
    return comments

def upload_dcm(request):
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        myfile = fs.save(myfile.name, myfile)
        fileName = list(myfile)[:-4] # remove '.dcm'
        fileName = ''.join(fileName)
    
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

            # read file
            dataset = pydicom.dcmread(dcmFilePath) 

            data = patient_data(dataset)
            pid = data['pid']
            name = data['name']
            sex = data['sex']
            age = data['age']
            mp = data['mp']

            response={
                'pid': pid,
                'name': name,
                'sex': sex,
                'age': age,
                'mp': mp,
                'dataset': dataset,
            } 

            # ----- get image report from IMG file -----  
            # pydicom example: https://goo.gl/SMyny4
            try:
                dataset.pixel_array
                if cv2.imwrite('media/DCM/JPG/' + fileName + '_report.jpg', dataset.pixel_array):
                    # must add a '/' ahead
                    response['report'] = '/media/DCM/JPG/' + fileName + '_report.jpg'

            # -------- get value from STR file --------
            except:   
                comment = dataset.ImageComments
                comment = comment.split('><')

                match = [s for s in comment if "SCAN type" in s]
                length = len(match)

                # 02 frax: major fracture
                if length == 0:
                    keyword = [s for s in comment if "MAJOR_OSTEO_FRAC_RISK units" in s]
                    fracture = ''.join(keyword)
                    fracture = fracture.split('</')[0].split('>')[1]
                    response['fracture'] = fracture

                # at least one scanType:
                else:
                    comments = t_z_r(comment)
                    tscore = comments['tscore']
                    zscore = comments['zscore']
                    region = comments['region']
                    response['tscore'] = tscore
                    response['zscore'] = zscore
                    response['region'] = region
                    
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
                                lva.append(substring)
                            while 'None' in lva:
                                lva.remove(substring)
                            response['lva'] = lva
                        # AP Spine
                        elif scanType == 'AP Spine':
                            APSpine = list(zip(region, tscore, zscore))
                            response['APSpine'] = APSpine
                        # Dual Femur
                        elif scanType == 'DualFemur':
                            DualFemur = list(zip(region, tscore, zscore))
                            response['DualFemur'] = DualFemur

                        else:
                            print('error input')

                    # multi scanType: combination
                    elif length == 3:
                        del region[1:4]
                        combination = list(zip(region, tscore, zscore))
                        response['combination'] = combination
                        # get LVA
                        T7 = [s for s in comment if "DEFORMITY" in s]
                        T7 = ''.join(T7)
                        T7 = T7.split('</')[0].split('>')[1]
                        response['T7'] = T7   

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

        # get folder name of the extracted zip file
        zipFolder = list(myZipFile)[:-4] #remove '.zip'
        zipFolder = ''.join(zipFolder)
        zipFilePath = 'media/ZIP/' + zipFolder
        
        # get file list in the folder
        onlyfiles = [f for f in listdir('media/ZIP/') if isfile(join('media/ZIP/', f))]
        # if the file name already exists, show warning
        if myZipFile in onlyfiles:
            os.remove('media/'+myZipFile)
            response = {
                'warning':myZipFile
            }
            return render(request, 'core/upload_zip.html', response)
        
        else: 
            # move file form media/ to media/zip/ folder
            shutil.move('media/'+myZipFile, 'media/ZIP/'+myZipFile)
            # read zip file
            zip_file = zipfile.ZipFile(os.path.join(os.getcwd(), 'media/ZIP/', myZipFile))
            # extract zip file
            for file in zip_file.namelist():
                zip_file.extract(file, os.path.join(os.getcwd(), 'media/ZIP/'))

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

            response['uploaded_file_url'] = fs.url(myZipFile)
            
            return render(request, 'core/upload_zip.html', response)
    else: 
        return render(request, 'core/upload_zip.html')

def show_zip(request):
    zipFolder = request.session['myZipFile']
    zipFolder = list(zipFolder)[:-4] # remove '.zip'
    zipFolder = ''.join(zipFolder)

    # get the file name user clicked from template
    myfile = request.GET.get('file', None)
    fileName = list(myfile)[:-4] # remove '.zip'
    fileName = ''.join(fileName)

    if myfile.startswith('STR'):
        filePath = 'media/ZIP/' + zipFolder + '/SDY00000/' + myfile
    elif myfile.startswith('IMG'):
        filePath = 'media/ZIP/' + zipFolder + '/SDY00000/SRS00000/' + myfile

    # read file
    dataset = pydicom.dcmread(filePath) 

    data = patient_data(dataset)
    pid = data['pid']
    name = data['name']
    sex = data['sex']
    age = data['age']
    mp = data['mp']

    response={
        'pid': pid,
        'name': name,
        'sex': sex,
        'age': age,
        'mp': mp,
        'dataset': dataset,
    }

     # ----- get image report from IMG file -----  
    # pydicom example: https://goo.gl/SMyny4
    try:
        dataset.pixel_array
        if cv2.imwrite('media/ZIP/JPG/' + fileName + '_report.jpg', dataset.pixel_array):
            # must add a '/' ahead
            response['report'] = '/media/ZIP/JPG/' + fileName + '_report.jpg'


    # -------- get value from STR file --------
    except:
        comment = dataset.ImageComments
        comment = comment.split('><')

        match = [s for s in comment if "SCAN type" in s]
        length = len(match)

        # no scanType: major fracture
        if length == 0:
            response['scanType'] = 'FRAX'
            keyword = [s for s in comment if "MAJOR_OSTEO_FRAC_RISK units" in s]
            fracture = ''.join(keyword)
            fracture = fracture.split('</')[0].split('>')[1]
            response['fracture'] = fracture

        # at least one scanType:
        else:
            comments = t_z_r(comment)
            tscore = comments['tscore']
            zscore = comments['zscore']
            region = comments['region']
            response['tscore'] = tscore
            response['zscore'] = zscore
            response['region'] = region
            
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
                        lva.append(substring)
                    while 'None' in lva:
                        lva.remove(substring)
                    response['lva'] = lva
                # AP Spine
                elif scanType == 'AP Spine':
                    APSpine = list(zip(region, tscore, zscore))
                    response['APSpine'] = APSpine
                # Dual Femur
                elif scanType == 'DualFemur':
                    DualFemur = list(zip(region, tscore, zscore))
                    response['DualFemur'] = DualFemur

                else:
                    print('error input')

            # multi scanType: combination
            else:
                del region[1:4]
                combination = list(zip(region, tscore, zscore))
                response['combination'] = combination
                # get LVA
                T7 = [s for s in comment if "DEFORMITY" in s]
                T7 = ''.join(T7)
                T7 = T7.split('</')[0].split('>')[1]
                response['T7'] = T7   

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

def show_dcm(request):

    # get the file user clicked from template
    myfile = request.GET.get('file', None)
    request.session['myfile'] = myfile

    fileName = list(myfile)[:-4] # remove '.dcm'
    fileName = ''.join(fileName)

    # filePath preprocess
    filePath = 'media/DCM/' + myfile
    request.session['filePath'] = filePath

    # read file
    dataset = pydicom.dcmread(filePath)

    data = patient_data(dataset)
    pid = data['pid']
    name = data['name']
    sex = data['sex']
    age = data['age']
    mp = data['mp']

    response={
        'filePath': filePath,
        'pid': pid,
        'name': name,
        'sex': sex,
        'age': age,
        'mp': mp,
        'dataset': dataset,
    }

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
        comment = dataset.ImageComments
        comment = comment.split('><')

        match = [s for s in comment if "SCAN type" in s]
        length = len(match)

        # no scanType: major fracture
        if length == 0:
            keyword = [s for s in comment if "MAJOR_OSTEO_FRAC_RISK units" in s]
            fracture = ''.join(keyword)
            fracture = fracture.split('</')[0].split('>')[1]
            response['fracture'] = fracture

        # at least one scanType:
        else:
            comments = t_z_r(comment)
            tscore = comments['tscore']
            zscore = comments['zscore']
            region = comments['region']
            response['tscore'] = tscore
            response['zscore'] = zscore
            response['region'] = region
            
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
                        lva.append(substring)
                    while 'None' in lva:
                        lva.remove(substring)
                    response['lva'] = lva
                # AP Spine
                elif scanType == 'AP Spine':
                    APSpine = list(zip(region, tscore, zscore))
                    response['APSpine'] = APSpine
                # Dual Femur
                elif scanType == 'DualFemur':
                    DualFemur = list(zip(region, tscore, zscore))
                    response['DualFemur'] = DualFemur

                else:
                    print('error input')

            # multi scanType: combination
            else:
                del region[1:4]
                combination = list(zip(region, tscore, zscore))
                response['combination'] = combination
                # get LVA
                T7 = [s for s in comment if "DEFORMITY" in s]
                T7 = ''.join(T7)
                T7 = T7.split('</')[0].split('>')[1]
                response['T7'] = T7

    return render(request, 'core/show_dcm.html', response)

def manage_zip(request):

    folderPath = 'media/ZIP/'

    # list files in the folder
    onlyfiles = [f for f in listdir(folderPath) if isfile(join(folderPath, f))]
    # select files to remove
    if request.method == 'POST':
        selected = request.POST.getlist('selected')
        result=''
        response={}
        for files in selected:
            fileName = list(files)[:-4] # remove '.zip'
            fileName = ''.join(fileName)
            # remove zip file and extract folder
            os.remove('media/ZIP/' + files) 
            shutil.rmtree('media/ZIP/' + fileName)
            
            result+=fileName + ' '
            response['result'] = result
        return render(request, 'core/result.html', response)

    return render(request, 'core/manage_zip.html', {
        'onlyfiles': onlyfiles,
    })

def manage_show_zip(request):
    # get the file name user clicked from template
    myfile = request.GET.get('file', None)
    request.session['myfile'] = myfile
    zipFilePath = 'media/ZIP/' + myfile
    request.session['filePath'] = zipFilePath

    zipFolder = list(myfile)[:-4] # remove '.zip'
    zipFolder = ''.join(zipFolder)
    zipFolderPath = 'media/ZIP/' + zipFolder
    
    response={
        'myfile': myfile,
        'zipFilePath': zipFilePath,
    }

    # remove selected files
    if request.method == 'POST':
        selected = request.POST.getlist('selected')
        result=''
        response={}
        for files in selected:
            os.remove('media/ZIP/' + files)            
            result+=myfile + ' '
            response['result'] = result
        return render(request, 'core/result.html', response)

    # directory tree
    dir_tree = []
    # contain '.dcm' files 
    file_tree = []
    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk(zipFolderPath):
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
    # need: apspine, lva, frax
    # get the file name user clicked from template
    myZIPFile = request.session['myfile']
    print(myZIPFile)
    zipFolder = list(myZIPFile)[:-4] # remove '.zip'
    zipFolder = ''.join(zipFolder)

    zipFilePath = 'media/ZIP/' + zipFolder
    strFilePath = zipFilePath + '/SDY00000/'
    response={}
    
    # recognize files through dataset
    # get list of the directory
    onlyFiles = os.listdir(strFilePath)
    lstFilesDCM = []
    # get only 'str' files from the list
    for files in onlyFiles:
        if "STR" in files:
            lstFilesDCM.append(files)
    # browse through each file, search from dataset(scantype), and recognize the information(datatype)
    for files in lstFilesDCM:
        filesPath = strFilePath + files
        print(filesPath)
        dataset = pydicom.dcmread(filesPath)
        comment = dataset.ImageComments
        comment = comment.split('><')

        match = [s for s in comment if "SCAN type" in s]
        length = len(match)

        # no scanType: major fracture
        if length == 0:
            file_frax = files
        
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
        print(files)

    apspineFilePath = 'media/ZIP/' + zipFolder + '/SDY00000/' + file_apspine

    # read file
    dataset = pydicom.dcmread(apspineFilePath)

    data = patient_data(dataset)
    pid = data['pid']
    name = data['name']
    age = data['age']
    mp = data['mp']
    sex = data['sex']

    comment = dataset.ImageComments
    comment = comment.split('><')
    comments = t_z_r(comment)
    region = comments['region']
    tscore = comments['tscore']
    zscore = comments['zscore']
    response = {
        'pid': pid,
        'name': name,
        'sex': sex,
        'age': age,
        'mp': mp,
        'tscore': tscore,
        'zscore': zscore,
        'region': region,
    }

    # decide group
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

    # zip
    merge = list(zip(region, tscore, zscore))
    # get the outcome from the machine
    machineMerge = merge[4:]
    machineOutcome = []
    for substring in machineMerge:
        machineOutcome.append(substring[0])
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
        response['dist1'] = dist1
        response['dist2'] = dist2
    elif group:
        merge = sorted(merge, key=getZ)
        # get mean and absolute value
        mean = (float(merge[1][2]) + float(merge[2][2]))/2
        dist1 = abs(float(merge[0][2]) - mean)
        dist2 = abs(mean - float(merge[3][2]))
        response['dist1'] = dist1
        response['dist2'] = dist2

    # regionFilter: remove outlier
    regionFilter = ['L1','L2','L3','L4']
    if dist1 > 1:
        regionFilter.remove(merge[0][0])
    if dist2 > 1:
        regionFilter.remove(merge[3][0])
    response['regionFilter'] = regionFilter

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
    response['outcome'] = outcome
    
    # check the result to determine re-gen or not
    if outcome in machineOutcome:
        response['result'] = 'Correct, go to the next step.'
        # Obtain LVA
        lvaFilePath = 'media/ZIP/' + zipFolder + '/SDY00000/' + file_lva
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
        grade = [s for s in merge if s[1] != 'None']
        response['grade'] = grade

        # Obtain frax
        fraxFilePath = 'media/ZIP/' + zipFolder + '/SDY00000/' + file_frax
        # read file
        dataset = pydicom.dcmread(fraxFilePath)
        comment = dataset.ImageComments
        comment = comment.split('><')

        # get major frac
        majorFrac = [s for s in comment if "MAJOR_OSTEO_FRAC_RISK units" in s]
        majorFrac = ''.join(majorFrac)
        majorFrac = majorFrac.split('</')[0].split('>')[1]
        response['majorFrac'] = majorFrac
        #get hip frac
        hipFrac = [s for s in comment if "HIP_FRAC_RISK units" in s]
        hipFrac = ''.join(hipFrac)
        hipFrac = hipFrac.split('</')[0].split('>')[1]
        response['hipFrac'] = hipFrac

        return render(request, 'core/check_apspine.html', response)

    else:
        response['result'] = 'Warn!! Please Re-gen.'

    return render(request, 'core/check_apspine.html', response)

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

def remove(request):
    # get file name from show_DCM/manage_show_zip
    myfile = request.session['myfile']

    # get file type (dcm or zip)
    fileType = list(myfile)[-3:]
    fileType = ''.join(fileType)
 
    if request.method == 'POST':
        response={}
        response['result']=myfile

        # if the file is a zip, remove both zip and the extracted folder
        if fileType.startswith('zip'):
            folderName = list(myfile)[:-4]
            folderName = ''.join(folderName)

            os.remove('media/ZIP/' + myfile)
            shutil.rmtree('media/ZIP/' + folderName)
        # if the file is a dcm, remove dcm
        elif fileType.startswith('dcm'):
            os.remove('media/DCM/' + myfile)
            dir_list = os.listdir('media/DCM/JPG/')
            fileName = list(myfile)[:-4]
            fileName = ''.join(fileName)
            reportName = fileName + '_report.jpg'
            if reportName in dir_list:
                os.remove('media/DCM/JPG/' + reportName)

        return render(request, 'core/result.html', response)
    else:
        return render(request, 'core/result.html')

def download(request):
    # get file path from show_DCM
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