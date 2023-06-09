from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Camera, CamCard, Gallery
from .forms import AddCameraForm, ListCameraForm
from .filters import CameraFilter, GalleryFilter
from .ml_models.camera import open_camera
from django.conf import settings
from datetime import datetime
from django.utils import timezone
from .ml_models.camera import send_message_to_mqtt
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import load_img, img_to_array
import numpy as np
from django.db.models import Max

import os


# Count status trash-can
def loadModel(path_model):
    return load_model(path_model)

def prediksi(model, tes_path):
    img = load_img(tes_path, target_size=(150, 150))
    x = img_to_array(img)
    x /= 255
    x = np.expand_dims(x, axis=0)
    images = np.vstack([x])
    predict = model.predict(images)
    if predict[0][0] >= 0.5:
        return 1
    return 0

# path_model = os.path.join(settings.BASE_DIR, 'trash_can_detector', 'ml_models', 'new_model.h5')
# model = loadModel(path_model)

# Page Home
@login_required(login_url='login')
def home(request):
    # Mengakses semua instance CamCard
    cam_card = CamCard.objects.all()

    # Membuat instance form
    forms = ListCameraForm(request.POST or None, request.FILES)

    if request.method == 'POST':
        if forms.is_valid():
            # Mendapatkan data dari form yang valid
            name = forms.cleaned_data.get('name')
            picture = request.FILES['picture']
            current_time = timezone.now()

            # Menyimpan file gambar ke Cloud Storage
            picture_path = settings.GS_BUCKET_NAME
            with open(picture_path, 'wb') as f:
                for chunk in picture.chunks():
                    f.write(chunk)

            # Menghitung prediksi dengan menggunakan model
            path_model = os.path.join(settings.BASE_DIR, 'trash_can_detector', 'ml_models', 'newest_model.h5')
            model = load_model(path_model)
            result = prediksi(model, picture_path)

            # Menghapus file gambar setelah selesai digunakan
            os.remove(picture_path)

            # result = ''
            if result == 0:
                capacity = 'Not Full'
            else:
                capacity = 'Full'

            # Menyimpan data ke dalam model Gallery
            save_to_gallery = Gallery.objects.create(
                name=name,
                picture=picture,
                capacity=capacity,
                timestamp=current_time
            )
            save_to_gallery.save()

            # Mengirim pesan ke MQTT
            formatted_time = current_time.strftime('%d%m%Y')
            message = {
                'name': str(name),
                'capacity': str(result),
                'timestamp': formatted_time
            }
            send_message_to_mqtt(message)

            # Menambahkan pesan sukses ke dalam messages Django
            pesan = f'Success upload image for {name}'
            messages.success(request, pesan)

    # Menghitung jumlah total cam_card
    total_trash_can = len(cam_card)

        
    latest_galleries = Gallery.objects.all().order_by('name', '-timestamp')
    latest_gallery_dict = {}

    for gallery in latest_galleries:
        if gallery.name_id not in latest_gallery_dict:
            latest_gallery_dict[gallery.name_id] = gallery

    latest_galleries = list(latest_gallery_dict.values())



    # Konteks untuk template
    context = {
        'title': 'Trash Can Detector | Home',
        'cam_card': cam_card,
        'forms': forms,
        'total_trash_can': total_trash_can,
        'latest_galleries': latest_galleries
    }
    return render(request, 'trash_can_detector/home.html', context)


# page camera
@login_required(login_url='login')
def camera(request):
    # Mengakses instance Camera
    camera = Camera.objects.all()

    # Mengimplementasikan filters untuk list camera
    myFilters = CameraFilter(request.GET, queryset=camera)
    camera = myFilters.qs

    # Menghitung jumlah total camera
    total_cam = len(camera)

    # Konteks untuk template
    context = {
        'title': 'Trash Can Detector : Camera',
        'camera': camera,
        'total_cam': total_cam,
        'myFilters': myFilters
    }
    return render(request, 'trash_can_detector/camera.html', context)

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

    return redirect('trash_can_detector:home')


# Menambahkan instance Camera
@login_required(login_url='login')
def add_camera(request):
    # Mengakses semua instance Camera
    camera = Camera.objects.all()

    # Membuat instance form untuk menambahkan kamera
    add_form = AddCameraForm(request.POST or None)

    if request.method == 'POST':
        if add_form.is_valid():
            # Mendapatkan data dari form yang valid
            name = add_form.cleaned_data['name']
            ip_camera = add_form.cleaned_data['ip_camera']

            # Validasi agar name dan ip camera yang diinput tidak sama dengan yang sudah ada
            if Camera.objects.filter(name=name).exists():
                messages.error(request, 'Nama sudah ada di database.')
                return redirect('trash_can_detector:camera')
            elif Camera.objects.filter(ip_camera=ip_camera).exists() and ip_camera != 'None' and ip_camera != 'none' and ip_camera != '-':
                messages.error(request, 'Alamat IP Camera sudah ada di database.')
                return redirect('trash_can_detector:camera')

            # Menyimpan data ke dalam model Camera
            add_form.save()

            # Menambahkan pesan sukses ke dalam messages Django
            messages.success(request, 'Added Camera Success')
            return redirect('trash_can_detector:camera')

    # Konteks untuk template
    context = {
        'title': 'Add Camera',
        'action': 'Add',
        'add_form': add_form,
        'camera': camera
    }
    return render(request, 'trash_can_detector/add_camera.html', context)


# Menghapus instance Camera
@login_required(login_url='login')
def delete(request, delete_id):
    # Mengakses objek Camera berdasarkan ID yang ingin dihapus
    cam_object = Camera.objects.get(id=delete_id)
    
    # Menghapus objek Camera dari database
    cam_object.delete()

    # Menambahkan pesan sukses ke dalam messages Django
    messages.success(request, 'Camera berhasil dihapus')

    return redirect('trash_can_detector:camera')


# Untuk menghapus photo di Gallery
@login_required(login_url='login')
def delete_gallery(request, delete_id):
    # Mengakses objek Gallery berdasarkan ID yang ingin dihapus
    gal_object = Gallery.objects.get(id=delete_id)
    
    # Menghapus objek Gallery dari database
    gal_object.delete()

    # Menambahkan pesan sukses ke dalam messages Django
    messages.success(request, 'Deleted Success')

    return redirect('trash_can_detector:gallery')


# Update instance Camera
@login_required(login_url='login')
def update(request, update_id):
    # Mengakses semua instance Camera
    camera = Camera.objects.all()

    # Mengakses objek Camera yang ingin diupdate
    cam_update = Camera.objects.get(id=update_id)

    if request.method == 'POST':
        # Membuat instance form untuk mengupdate kamera
        form_cam_update = AddCameraForm(request.POST or None, instance=cam_update)

        # Mengatur field 'name' menjadi disabled agar tidak dapat diupdate oleh user
        form_cam_update.fields['name'].disabled = True

        if form_cam_update.is_valid():
            # Memeriksa apakah ada perubahan pada field 'ip_camera'
            if 'ip_camera' in form_cam_update.changed_data:
                # Jika ada perubahan pada field 'ip_camera'
                ip_camera = form_cam_update.cleaned_data['ip_camera']
                if Camera.objects.filter(ip_camera=ip_camera).exists() and ip_camera != 'None' and ip_camera != 'none' and ip_camera != '-':
                    messages.error(request, 'Alamat IP Camera sudah ada di database.')
                    return redirect('trash_can_detector:camera')

            # Menyimpan perubahan pada objek Camera
            form_cam_update.save()

            # Menambahkan pesan sukses ke dalam messages Django
            messages.success(request, 'Updated Succes')
            return redirect('trash_can_detector:camera')
    else:
        # Membuat instance form dengan objek Camera yang ingin diupdate
        form_cam_update = AddCameraForm(instance=cam_update)

        # Mengatur field 'name' menjadi disabled agar tidak dapat diupdate oleh user
        form_cam_update.fields['name'].disabled = True

    # Konteks untuk template
    context = {
        'title': 'Update Camera',
        'action': 'Update',
        'add_form': form_cam_update,
        'camera': camera
    }

    return render(request, 'trash_can_detector/add_camera.html', context)


# Page Gallery
@login_required(login_url='login')
def gallery(request):
    # Mengakses semua instance dalam Gallery dan diurutkan dari yang paling baru
    gall = Gallery.objects.all().order_by('-id')

    # Menerapkan filter pada list instance dalam Gallery
    myFilters = GalleryFilter(request.GET, queryset=gall)
    gall = myFilters.qs

    # Menghitung jumlah instance dalam Gallery
    total_pic = len(gall)

    # Konteks untuk template
    context = {
        'title': 'Trash Can Detector | Gallery',
        'gallery': gall,
        'myFilters': myFilters,
        'total_pic': total_pic
    }
    return render(request, 'trash_can_detector/gallery.html', context)


# Menghapus data berdasarkan checkbox
@login_required(login_url='login')
def gallery_delete_checkbox(request):
    if request.method == 'POST':
        # Mendapatkan daftar ID galeri yang dipilih dari POST data
        gallery_ids = request.POST.getlist('gallery_ids')
        
        for i in gallery_ids:
            # Mengakses objek Gallery berdasarkan ID yang dipilih
            obj = Gallery.objects.get(id=i)
            
            # Menghapus objek Gallery dari database
            obj.delete()
        
        if len(gallery_ids) == 0:
            # Menambahkan pesan keberhasilan ketika tidak ada data yang dipilih
            messages.success(request, 'No data selected')
        else:
            # Menambahkan pesan keberhasilan ketika data berhasil dihapus
            messages.success(request, f'{len(gallery_ids)} data have been succesfully deleted')

    return redirect('trash_can_detector:gallery')


# Menghapus semua data yang ada di gallery
@login_required(login_url='login')
def gallery_delete_all(request):
    # Mengakses daftar ID galeri dari semua objek Gallery
    gallery_ids = Gallery.objects.values_list('id', flat=True)
    
    for i in gallery_ids:
        # Mengakses objek Gallery berdasarkan ID
        obj = Gallery.objects.get(id=i)
        
        # Menghapus objek Gallery dari database
        obj.delete()
    
    if len(gallery_ids) == 0:
        # Menambahkan pesan keberhasilan ketika tidak ada data yang harus dihapus
        messages.success(request, 'No data should be deleted')
    else:
        # Menambahkan pesan keberhasilan ketika semua data berhasil dihapus
        messages.success(request, 'All data have been successfully deleted')

    return redirect('trash_can_detector:gallery')


# Menghapus data berdasarkan checkbox pada camera
@login_required(login_url='login')
def camera_delete_checkbox(request):
    if request.method == 'POST':
        # Mendapatkan daftar ID galeri yang dipilih dari POST data
        camera_ids = request.POST.getlist('camera_ids')
        
        for i in camera_ids:
            # Mengakses objek Gallery berdasarkan ID yang dipilih
            obj = Camera.objects.get(id=i)
            
            # Menghapus objek Gallery dari database
            obj.delete()
        
        if len(camera_ids) == 0:
            # Menambahkan pesan keberhasilan ketika tidak ada data yang dipilih
            messages.success(request, 'No data selected')
        else:
            # Menambahkan pesan keberhasilan ketika data berhasil dihapus
            messages.success(request, f'{len(camera_ids)} data have been succesfully deleted')

    return redirect('trash_can_detector:camera')


# Menghapus semua data yang ada di camera
@login_required(login_url='login')
def camera_delete_all(request):
    # Mengakses daftar ID galeri dari semua objek Gallery
    camera_ids = Camera.objects.values_list('id', flat=True)
    
    for i in camera_ids:
        # Mengakses objek Gallery berdasarkan ID
        obj = Camera.objects.get(id=i)
        
        # Menghapus objek Gallery dari database
        obj.delete()
    
    if len(camera_ids) == 0:
        # Menambahkan pesan keberhasilan ketika tidak ada data yang harus dihapus
        messages.success(request, 'No data should be deleted')
    else:
        # Menambahkan pesan keberhasilan ketika semua data berhasil dihapus
        messages.success(request, 'All data have been successfully deleted')

    return redirect('trash_can_detector:camera')
