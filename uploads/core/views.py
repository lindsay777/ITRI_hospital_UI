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
        reportname_list = list(filename)
        reportname_list = reportname_list[:-4]
        print(reportname_list)
        reportname = ''.join(reportname_list)
        print(reportname)

        print(os.getcwd())

        zscore=[]
        tscore=[]
        report = ''

        dataset = pydicom.dcmread('media/' + myfile.name)

        # get sex
        sex = dataset.PatientSex
        print(sex)
        # get age
        age = dataset.PatientAge
        age_list = list(age)
        del age_list[-1]
        if age_list[0]=='0':
            del age_list[0]
        age = ''.join(age_list)
        print(age)
        # get MP
        name = dataset.PatientName
        temp = str(name)
        if "(PM" in temp:
            temp = temp.split('(')[1]
            temp = temp.split(')')[0]
            temp_list = list(temp)
            del temp_list[0:2]
            mp = ''.join(temp_list)
        print(mp)

        # Judge from filename, get value or image
        if filename.startswith('STR'):
            str1 = dataset.ImageComments
            str2 = str1.split('><')
            # get zscore
            match_zscore = [s for s in str2 if "BMD_ZSCORE" in s]
            for substring in match_zscore:
                substring = substring.split('</')[0]
                substring = substring.split('>')[1]
                zscore.append(substring)
            print(zscore)

            # get tscore
            match_tscore = [s for s in str2 if "BMD_TSCORE" in s]
            for substring in match_tscore:
                substring = substring.split('</')[0]
                substring = substring.split('>')[1]
                tscore.append(substring)
            print(tscore)


        elif filename.startswith('IMG'):
            # get image
            print("get image")
            rows = int(dataset.Rows)
            cols = int(dataset.Columns)
            print("Image size.......: {rows:d} x {cols:d}, {size:d} bytes".format(
                rows=rows, cols=cols, size=len(dataset.PixelData)))
            if 'PixelSpacing' in dataset:
                print("Pixel spacing....:", dataset.PixelSpacing)

            
            # if cv2.imwrite('/media/'+reportname+'_report.jpg', dataset.pixel_array):
            #     print('cv2!!')
            #     report = '/media/'+reportname+'_report.jpg'
            #     print('report: '+ report)
            if cv2.imwrite('media/' + reportname + '_report.jpg', dataset.pixel_array):
                report = 'media/' + reportname + '_report.jpg'
                print(report)


        uploaded_file_url = fs.url(filename)
        return render(request, 'core/simple_upload.html', {
            'uploaded_file_url': uploaded_file_url,
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


