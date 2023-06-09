from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib import messages


def login_page(request):
    context = {
        'title': 'Person and Object Detectors | Login'
    }
    user = None
    group_name = 'user-all-rounded'

    if request.method == 'POST':
        username_login = request.POST['username']
        password_login = request.POST['password']

        user = authenticate(request, username=username_login, password=password_login)

        if user is not None:
            all_rounded_group = Group.objects.get(name=group_name)
            if all_rounded_group in user.groups.all():
                login(request, user)
                return redirect('landing-page')
            else:
                messages.error(request, 'Anda tidak memiliki akses')
                return redirect('login')
        else:
            messages.error(request, 'Your username or password is incorrect!')
            return redirect('login')
    
    if request.method == 'GET':
        if request.user.is_authenticated:
            # logika untuk user
            return redirect('landing-page')
        else:
            # logika untuk anonymous
            return render(request, 'login.html', context)

@login_required(login_url='login')
def index(request):
    context = {
        'title' : 'Person and Object Detectors'
    }
    return render(request, 'index.html', context)