from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Camera, CamCard, Gallery
from .forms import AddCameraForm, ListCameraForm
from .filters import CameraFilter, GalleryFilter
from .ml_models.camera import open_camera
from .ml_models.camera_hdd import open_camera as open_camera_hdd
from django.conf import settings
from datetime import datetime
from django.utils import timezone
from .ml_models.camera import send_message_to_mqtt
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import load_img, img_to_array
import numpy as np 

import os

def buat_model(path_model):
    return load_model(path_model)

def predict(tes_path, model):
    img = load_img(tes_path, target_size=(600, 600))
    x = img_to_array(img)
    x /= 255
    x = np.expand_dims(x, axis=0)
    images = np.vstack([x])
    yhat = model.predict(images)
    yhat = np.argmax(yhat, axis=1)[0]
    return yhat

def predict_ssd(tes_path, model):
    img = load_img(tes_path, target_size=(300, 300))
    x = img_to_array(img)
    x /= 255
    x = np.expand_dims(x, axis=0)
    images = np.vstack([x])
    yhat = model.predict(images)
    yhat = np.argmax(yhat, axis=1)[0]
    return yhat





# Counting SSD tray
def tray_ssd(request, forms):
    # Mendapatkan data yang diinput dari form
    name = forms.cleaned_data.get('name')
    picture = request.FILES['picture']
    current_time = timezone.now()

    # Menyimpan file gambar ke Cloud Storage
    picture_path = settings.GS_BUCKET_NAME
    with open(picture_path, 'wb') as f:
        for chunk in picture.chunks():
            f.write(chunk)

    # Menghitung prediksi menggunakan model
    path_model = os.path.join(settings.BASE_DIR, 'memory_tray_detector', 'ml_models', 'model_SSD.h5')
    model = buat_model(path_model)
    result = predict_ssd(picture_path, model)

    quantity = result
    type_tray = 'SSD'
            
    # Menyimpan data ke dalam model Gallery
    save_to_gallery = Gallery.objects.create(
        name=name,
        picture=picture,
        quantity=quantity,
        type_tray=type_tray,
        timestamp=current_time
    )
    save_to_gallery.save()

    # Mengirim pesan melalui MQTT
    formatted_time = current_time.strftime('%d%m%Y')
    message = {
        'name': str(name),
        'remaining-quantity': str(quantity),
        'type': type_tray,
        'timestamp': formatted_time
    }
    send_message_to_mqtt(message)

    # Menambahkan pesan keberhasilan
    pesan = f'Success upload image for {name}'
    messages.success(request, pesan)

# Counting HDD tray
def tray_hdd(request, forms):
    # Mendapatkan data yang diinput dari form
    name = forms.cleaned_data.get('name')
    picture = request.FILES['picture']
    current_time = timezone.now()

    # Menyimpan file gambar ke Cloud Storage
    picture_path = settings.GS_BUCKET_NAME
    with open(picture_path, 'wb') as f:
        for chunk in picture.chunks():
            f.write(chunk)

    # Menghitung prediksi menggunakan model
    path_model = os.path.join(settings.BASE_DIR, 'memory_tray_detector', 'ml_models', 'model_HDD.h5')
    model = buat_model(path_model)
    result = predict(picture_path, model)

    quantity = result
    type_tray = 'HDD'
            
    # Menyimpan data ke dalam model Gallery
    save_to_gallery = Gallery.objects.create(
        name=name,
        picture=picture,
        quantity=quantity,
        type_tray=type_tray,
        timestamp=current_time
    )
    save_to_gallery.save()

    # Mengirim pesan melalui MQTT
    formatted_time = current_time.strftime('%d%m%Y')
    message = {
        'name': str(name),
        'remaining-quantity': str(quantity),
        'type': type_tray,
        'timestamp': formatted_time
    }
    send_message_to_mqtt(message)

    # Menambahkan pesan keberhasilan
    pesan = f'Success upload image for {name}'
    messages.success(request, pesan)


# Page Home 
@login_required(login_url='login')
def home(request):
    # Mengakses semua instance CamCard
    cam_card = CamCard.objects.all()
    
    # Membuat form untuk input data camera
    forms = ListCameraForm(request.POST or None, request.FILES)

    if request.method == 'POST':
        if forms.is_valid():
            tray_type = forms.cleaned_data['type_tray']
            if tray_type == 'ssd':
                tray_ssd(request, forms)
            elif tray_type == 'hdd':
                tray_hdd(request, forms) 

    # Menghitung total tray yang ada
    total_tray = len(cam_card)

    latest_galleries = Gallery.objects.all().order_by('name', '-timestamp')
    latest_gallery_dict = {}

    for gallery in latest_galleries:
        if gallery.name_id not in latest_gallery_dict:
            latest_gallery_dict[gallery.name_id] = gallery

    latest_galleries = list(latest_gallery_dict.values())

    # Konteks untuk template
    context = {
        'title': 'Memory Tray Detector | Home',
        'cam_card': cam_card,
        'forms': forms,
        'total_tray': total_tray,
        'latest_galleries': latest_galleries
    }
    return render(request, 'memory_tray_detector/home.html', context)


# Page camera
@login_required(login_url='login')
def camera(request):
    # Mengakses instance Camera
    camera = Camera.objects.all()

    # Mengimplementasikan filters untuk list camera
    myFilters = CameraFilter(request.GET, queryset=camera)
    camera = myFilters.qs

    # Menghitung banyaknya camera
    total_cam = len(camera)

    # Konteks untuk template
    context = {
        'title': 'Memory Tray Detector : Camera',
        'camera': camera,
        'total_cam': total_cam,
        'myFilters': myFilters
    }
    return render(request, 'memory_tray_detector/camera.html', context)


# Membuka IP camera berdasarkan ID instance Camera untuk SSD tray
camera_open = False
@login_required(login_url='login')
def open_cam(request, camera_id):
    global camera_open

    if request.method == 'GET':

        if not camera_open:
            try:
                camera_open = True
                open_camera(camera_id)

                camera_open = False
            except Exception as e:
                # Tangkap kesalahan dan kirim pesan error ke pengguna
                camera_open = False
                error_message = f"The camera cannot be opened. Error: {str(e)}"
                messages.error(request, error_message)
        else:
            messages.error(request, 'Camera is currently open')

    return redirect('memory_tray_detector:home')


# Membuka IP camera berdasarkan ID instance Camera untuk HDD tray
camera_open_hdd = False
@login_required(login_url='login')
def open_cam_hdd(request, camera_id):
    global camera_open_hdd

    if request.method == 'GET':

        if not camera_open_hdd:
            try:
                camera_open_hdd = True
                open_camera_hdd(camera_id)

                camera_open_hdd = False
            except Exception as e:
                # Tangkap kesalahan dan kirim pesan error ke pengguna
                camera_open_hdd = False
                error_message = f"The camera cannot be opened. Error: {str(e)}"
                messages.error(request, error_message)
        else:
            messages.error(request, 'Camera is currently open')

    return redirect('memory_tray_detector:home')


# Menambahkan instance Camera
@login_required(login_url='login')
def add_camera(request):
    # Mengakses semua instance Camera
    camera = Camera.objects.all()
    
    # Membuat form untuk menambahkan data camera
    add_form = AddCameraForm(request.POST or None)
    
    if request.method == 'POST':
        if add_form.is_valid():
            # Mendapatkan data yang diinput dari form
            name = add_form.cleaned_data['name']
            ip_camera = add_form.cleaned_data['ip_camera']

            # Validasi agar name dan ip camera yang diinput tidak sama dengan name yang sudah ada
            if Camera.objects.filter(name=name).exists():
                messages.error(request, f'Nama {name} sudah ada di database.')
                return redirect('memory_tray_detector:camera')
            elif Camera.objects.filter(ip_camera=ip_camera).exists() and ip_camera != 'None' and ip_camera != 'none' and ip_camera != '-':
                messages.error(request, 'Alamat IP Camera sudah ada di database.')
                return redirect('memory_tray_detector:camera')
 
            # Menyimpan data ke dalam model Camera
            add_form.save()

            # Menambahkan pesan keberhasilan
            messages.success(request, 'Added Camera Success')
            return redirect('memory_tray_detector:camera')
   
    # Konteks untuk template
    context = {
        'title': 'Add Camera',
        'action': 'Add',
        'add_form': add_form,
        'camera': camera
    }
    return render(request, 'memory_tray_detector/add_camera.html', context)


# Menghapus instance Camera
@login_required(login_url='login')
def delete(request, delete_id):
    # Mengambil instance Camera berdasarkan ID yang diberikan
    cam_object = Camera.objects.get(id=delete_id)
    
    # Menghapus instance Camera
    cam_object.delete()
    
    # Menambahkan pesan keberhasilan
    messages.success(request, 'Camera berhasil dihapus')

    # Mengarahkan pengguna kembali ke halaman camera
    return redirect('memory_tray_detector:camera')


# Menghapus photo di Gallery
@login_required(login_url='login')
def delete_gallery(request, delete_id):
    # Mengambil instance Gallery berdasarkan ID yang diberikan
    gal_object = Gallery.objects.get(id=delete_id)
    
    # Menghapus instance Gallery
    gal_object.delete()
    
    # Menambahkan pesan keberhasilan
    messages.success(request, 'Deleted Success')

    # Mengarahkan pengguna kembali ke halaman gallery
    return redirect('memory_tray_detector:gallery')


# Untuk Update instance Camera
@login_required(login_url='login')
def update(request, update_id):
    # Mengambil semua instance Camera
    camera = Camera.objects.all()
    
    # Mengambil instance Camera yang akan diupdate berdasarkan ID yang diberikan
    cam_update = Camera.objects.get(id=update_id)
    
    if request.method == 'POST':
        # Membuat form untuk mengupdate data Camera
        form_cam_update = AddCameraForm(request.POST or None, instance=cam_update)
        
        # Menonaktifkan field name agar pengguna tidak dapat mengubahnya
        form_cam_update.fields['name'].disabled = True
        
        if form_cam_update.is_valid():
            # Memeriksa apakah terdapat perubahan pada field ip_camera
            if 'ip_camera' in form_cam_update.changed_data:
                # Jika terdapat perubahan pada field ip_camera
                ip_camera = form_cam_update.cleaned_data['ip_camera']
                
                # Memeriksa apakah alamat IP Camera sudah ada di database
                if Camera.objects.filter(ip_camera=ip_camera).exists() and ip_camera != 'None' and ip_camera != 'none' and ip_camera != '-':
                    messages.error(request, 'Alamat IP Camera sudah ada di database.')
                    return redirect('memory_tray_detector:camera')

            # Menyimpan perubahan pada instance Camera
            form_cam_update.save()

            messages.success(request, 'Updated Succes')
            return redirect('memory_tray_detector:camera')
    else:
        # Membuat form untuk mengupdate data Camera dengan menggunakan instance yang sudah ada
        form_cam_update = AddCameraForm(instance=cam_update)
        
        # Menonaktifkan field name agar pengguna tidak dapat mengubahnya
        form_cam_update.fields['name'].disabled = True
        
        context = {
            'title': 'Update Camera',
            'action': 'Update',
            'add_form': form_cam_update,
            'camera': camera
        }
    
    return render(request, 'memory_tray_detector/add_camera.html', context)


# Page Gallery
@login_required(login_url='login')
def gallery(request):
    # Mengambil semua instance dari model Gallery dan diurutkan berdasarkan ID secara menurun (paling baru)
    gall = Gallery.objects.all().order_by('-id')

    # Menerapkan filter pada list instance di Gallery berdasarkan permintaan GET yang diterima
    myFilters = GalleryFilter(request.GET, queryset=gall)
    gall = myFilters.qs

    # Menghitung jumlah instance di Gallery
    total_pic = len(gall)

    context = {
        'title': 'Memory Tray Detector | Gallery',
        'gallery': gall,
        'myFilters': myFilters,
        'total_pic': total_pic
    }
    return render(request, 'memory_tray_detector/gallery.html', context)


# Menghapus data berdasarkan checkbox pada gallery
@login_required(login_url='login')
def gallery_delete_checkbox(request):
    if request.method == 'POST':
        # Mengambil daftar ID galeri yang dipilih dari permintaan POST
        gallery_ids = request.POST.getlist('gallery_ids')

        # Menghapus setiap objek galeri berdasarkan ID yang dipilih
        for i in gallery_ids:
            obj = Gallery.objects.get(id=i)
            obj.delete()

        # Menampilkan pesan sukses jika ada data yang dihapus, atau pesan bahwa tidak ada data yang dipilih
        if len(gallery_ids) == 0:
            messages.success(request, 'No data selected')
        else:
            messages.success(request, f'{len(gallery_ids)} data have been successfully deleted')

    # Mengarahkan pengguna kembali ke halaman galeri setelah menghapus data
    return redirect('memory_tray_detector:gallery')


# Menghapus semua data di gallery
@login_required(login_url='login')
def gallery_delete_all(request):
    # Mengambil semua ID galeri menggunakan values_list
    gallery_ids = Gallery.objects.values_list('id', flat=True)

    # Menghapus setiap objek galeri berdasarkan ID
    for i in gallery_ids:
        obj = Gallery.objects.get(id=i)
        obj.delete()

    # Menampilkan pesan sukses jika ada data yang dihapus, atau pesan bahwa tidak ada data yang harus dihapus
    if len(gallery_ids) == 0:
        messages.success(request, 'No data should be deleted')
    else:
        messages.success(request, 'All data have been successfully deleted')

    # Mengarahkan pengguna kembali ke halaman galeri setelah menghapus data
    return redirect('memory_tray_detector:gallery')


# Menghapus data berdasarkan checkbox pada page camera
@login_required(login_url='login')
def camera_delete_checkbox(request):
    if request.method == 'POST':
        # Mengambil daftar ID galeri yang dipilih dari permintaan POST
        camera_ids = request.POST.getlist('camera_ids')

        # Menghapus setiap objek galeri berdasarkan ID yang dipilih
        for i in camera_ids:
            obj = Camera.objects.get(id=i)
            obj.delete()

        # Menampilkan pesan sukses jika ada data yang dihapus, atau pesan bahwa tidak ada data yang dipilih
        if len(camera_ids) == 0:
            messages.success(request, 'No data selected')
        else:
            messages.success(request, f'{len(camera_ids)} data have been successfully deleted')

    # Mengarahkan pengguna kembali ke halaman galeri setelah menghapus data
    return redirect('memory_tray_detector:camera')


# Menghapus semua data di camera
@login_required(login_url='login')
def camera_delete_all(request):
    # Mengambil semua ID galeri menggunakan values_list
    camera_ids = Camera.objects.values_list('id', flat=True)

    # Menghapus setiap objek galeri berdasarkan ID
    for i in camera_ids:
        obj = Camera.objects.get(id=i)
        obj.delete()

    # Menampilkan pesan sukses jika ada data yang dihapus, atau pesan bahwa tidak ada data yang harus dihapus
    if len(camera_ids) == 0:
        messages.success(request, 'No data should be deleted')
    else:
        messages.success(request, 'All data have been successfully deleted')

    # Mengarahkan pengguna kembali ke halaman galeri setelah menghapus data
    return redirect('memory_tray_detector:camera')

