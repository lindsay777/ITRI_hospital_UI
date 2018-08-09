from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from uploads.core.models import Document
from uploads.core.forms import DocumentForm

import matplotlib.pyplot as plt
import pydicom
import cv2
import os
from pydicom.data import get_testdata_files

def home(request):
    documents = Document.objects.all()
    return render(request, 'core/home.html', { 'documents': documents })

def simple_upload(request):
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)

        # create uniqe name for saving reports
        # remove '.dcm' 
        reportname_list = list(filename)[:-4]
        reportname = ''.join(reportname_list)
        
        zscore=[]
        tscore=[]
        report = ''

        dataset = pydicom.dcmread('media/' + myfile.name)

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

        #----- Judge from filename, get value or image -----
        # get value
        if filename.startswith('STR'):
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

        # get image
        elif filename.startswith('IMG'):
            
            # pydicom example: https://goo.gl/SMyny4
    
            if cv2.imwrite('media/' + reportname + '_report.jpg', dataset.pixel_array):
                report = '/media/' + reportname + '_report.jpg'

        uploaded_file_url = fs.url(filename)
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


