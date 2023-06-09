from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from .models import Post, DetectedFace, IpCamera
from .forms import PostForm, IpCameraForm
from django.http import HttpResponse
# from .ml_models.test import train
from .ml_models.main2 import open_camera
from .filters import DatabaseFilter, DetectedFilter
from django.conf import settings
from datetime import date
from .resource import DetectedFaceResource
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.core.files.storage import default_storage

import os


@login_required(login_url='login')
def home(request):
    detected = DetectedFace.objects.all().order_by('-id')
    myFilters = DetectedFilter(request.GET, queryset=detected)

    detected = myFilters.qs
    total_data = len(detected) #untuk menghitung jumlah object

    # print(request.user.get_all_permissions())

    context = {
        'title' : 'Person Detector | Home',
        'detected': detected,
        'myFilters': myFilters,
        'total_data': total_data
    }

    return render(request, 'person_detector/home.html', context)

@login_required(login_url='login')
def export_detected_dace(reqeust):
    detected_face = DetectedFaceResource()
    dataset = detected_face.export()
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=all_detectted_face_record.csv'
    return response

camera_open = False
@login_required(login_url='login')
def cam(request):
    global camera_open
    camera = IpCamera.objects.latest()

    if request.method == 'GET':

        # Buat Cek di prompt
        print(camera.ip_camera)

        if not camera_open:
            try:
                camera_open = True
                open_camera()

                camera_open = False
            except Exception as e:
                camera_open = False
                error_message = f"The camera cannot be opened. Error: {str(e)}"
                messages.error(request, error_message)
        else:
             messages.error(request, 'Camera is currently open')
        
        print('OK')
    return redirect('person_detector:home')

@login_required(login_url='login')
def database(request):
    post_person = Post.objects.all()
    ip_camera = IpCamera.objects.all()
    myFilters = DatabaseFilter(request.GET, queryset=post_person)
    post_person = myFilters.qs
    total_data = len(post_person) #untuk menghitung jumlah object
    context = {
        'title' : 'Person Detector | Database',
        'post': post_person,
        'myFilters': myFilters,
        'total_data': total_data,
        'ip_camera': ip_camera
    }
    return render(request, 'person_detector/database.html', context)



@login_required(login_url='login')
def post_database(request):
    post_person = Post.objects.all() 
    post_form = PostForm(request.POST or None, request.FILES)
    if request.method == "POST":
        if post_form.is_valid():
            name = post_form.cleaned_data['name']
            
            # validasi agar name yang diinput tidak sama dengan name yang sudah ada
            if Post.objects.filter(name=name).exists():
                messages.error(request, f'{name} already exists in the database.')
                return redirect('person_detector:database')

            picture = request.FILES['picture']
            post = post_form.save(commit=False)
            post.picture = picture

            ext = picture.name.split('.')[-1] #mendapatkan ekstensi
            filename = f'{name}.{ext}'
            post.picture.name = filename
            post.save()

            for person in post_person:
                name = person.name           
            messages.success(request, f'{name} successfully added')
            return redirect('person_detector:database')
    
    myFilters = DatabaseFilter(request.GET, queryset=post_person)
    post_person = myFilters.qs  
    context = {
        'title': 'Add Database',
        'action': 'Submit',
        'post_form': post_form,
        'post': post_person,
        'myFilters': myFilters
    }
    return render(request, 'person_detector/add_database.html', context)


@login_required(login_url='login')
def delete(request, delete_id):
    objcet = Post.objects.get(id = delete_id)
    objcet.delete()
    pesan = 'Data deleted successfully'            
    messages.success(request, pesan)
    return redirect('person_detector:database')

@login_required(login_url='login')
def update(request, update_id):
    post_person = Post.objects.all()
    form = Post.objects.get(id = update_id)
    name = form.name

    if request.method == 'POST' :
        # name = request.POST.get('name')
        if len(request.FILES) != 0:
            if len(form.picture) > 0:
                default_storage.delete(form.picture.name)
            picture = request.FILES['picture']
            form.picture = picture

            ext = picture.name.split('.')[-1] #mendapatkan ekstensi
            filename = f'{name}.{ext}'
            form.picture.name = filename

        
        form.fullName = request.POST.get('fullName')


        form.save()

        messages.success(request, 'Data successfully updated')
        return redirect('person_detector:database')
    
    context = {
        'title': 'Update Person Database',
        'form': form,
        'action': 'Update',
        'post': post_person,
    }

    return render(request, 'person_detector/update_database.html', context)

# Update Ip Camera address
@login_required(login_url='login')
def update_ip_camera(request, update_id):
    post_person = Post.objects.all()
    ip_camera = IpCamera.objects.all()
    ip_cam_update = IpCamera.objects.get(id = update_id)

    if request.method == 'POST':
        # Membuat form untuk mengupdate data Camera
        form_ip_cam_update = IpCameraForm(request.POST or None, instance=ip_cam_update)
        
        if form_ip_cam_update.is_valid():

            # Menyimpan perubahan pada instance Camera
            form_ip_cam_update.save()

            messages.success(request, 'Updated Succes')
            return redirect('person_detector:database')
    else:
        # Membuat form untuk mengupdate data Camera dengan menggunakan instance yang sudah ada
        form_ip_cam_update = IpCameraForm(instance=ip_cam_update)
        
        context = {
            'title': 'Update Ip Camera',
            'action': 'Update',
            'form': form_ip_cam_update,
            'post': post_person,
            'ip_camera': ip_camera
        }
    return render(request, 'person_detector/update_ip_camera.html', context)


@login_required(login_url='login')
def reset_all(request):
    obj = DetectedFace.objects.all()
    obj.delete()

    messages.success(request, f'All detected faces have been successfully deleted.')
    return redirect('person_detector:home')


# Menghapus data berdasarkan checkbox pada database person
@login_required(login_url='login')
def person_delete_checkbox(request):
    if request.method == 'POST':
        # Mengambil daftar ID person yang dipilih dari permintaan POST
        person_ids = request.POST.getlist('person_ids')

        # Menghapus setiap objek person berdasarkan ID yang dipilih
        for i in person_ids:
            obj = Post.objects.get(id=i)
            obj.delete()

        # Menampilkan pesan sukses jika ada data yang dihapus, atau pesan bahwa tidak ada data yang dipilih
        if len(person_ids) == 0:
            messages.success(request, 'No data selected')
        else:
            messages.success(request, f'{len(person_ids)} data have been successfully deleted')

    # Mengarahkan pengguna kembali ke halaman database setelah menghapus data
    return redirect('person_detector:database')


# Menghapus semua data person
@login_required(login_url='login')
def person_delete_all(request):
    # Mengambil semua ID camera menggunakan values_list
    person_ids = Post.objects.values_list('id', flat=True)

    # Menghapus setiap objek camera berdasarkan ID
    for i in person_ids:
        obj = Post.objects.get(id=i)
        obj.delete()

    # Menampilkan pesan sukses jika ada data yang dihapus, atau pesan bahwa tidak ada data yang harus dihapus
    if len(person_ids) == 0:
        messages.success(request, 'No data should be deleted')
    else:
        messages.success(request, 'All data have been successfully deleted')

    # Mengarahkan pengguna kembali ke halaman database setelah menghapus data
    return redirect('person_detector:database')