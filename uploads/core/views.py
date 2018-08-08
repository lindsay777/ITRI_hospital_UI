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

        os.chdir('C:/Users/Lindsay/Desktop/0807_v3/simple-file-upload/media')
        dir_path = os.path.dirname(os.path.realpath(__file__))

        zscore=[]
        report = ''

        if filename.startswith('STR00000'):
            dataset = pydicom.dcmread(myfile.name)
            str1 = dataset.ImageComments
            str2 = str1.split('><')
            match_zscore = [s for s in str2 if "BMD_ZSCORE" in s]
            #fo = open('filename.txt', 'w')
            for substring in match_zscore:
                substring = substring.split('</')[0]
                substring = substring.split('>')[1]
                zscore.append(substring)
            #fo.write(zscore)
            print(zscore)

        elif filename.startswith('IMG00000'):
            dataset = pydicom.dcmread(myfile.name)
            if 'PixelData' in dataset:
                rows = int(dataset.Rows)
                cols = int(dataset.Columns)
                print("Image size.......: {rows:d} x {cols:d}, {size:d} bytes".format(
                    rows=rows, cols=cols, size=len(dataset.PixelData)))
                if 'PixelSpacing' in dataset:
                    print("Pixel spacing....:", dataset.PixelSpacing)

            
            if cv2.imwrite('C:/Users/Lindsay/Desktop/0807_v3/simple-file-upload/media/report.jpg', dataset.pixel_array):
                report = 'C:/Users/Lindsay/Desktop/0807_v3/simple-file-upload/media/report.jpg'
                print(report)


        uploaded_file_url = fs.url(filename)
        return render(request, 'core/simple_upload.html', {
            'uploaded_file_url': uploaded_file_url,
            'zscore': zscore,
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


