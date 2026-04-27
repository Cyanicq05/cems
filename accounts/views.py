from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import CustomUser


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if not email.endswith('@northumbria.ac.uk'):
            return render(request, 'auth/register.html', {'error': 'Please use your Northumbria University email (@northumbria.ac.uk).'})

        if password1 != password2:
            return render(request, 'auth/register.html', {'error': 'Passwords do not match.'})

        if len(password1) < 8:
            return render(request, 'auth/register.html', {'error': 'Password must be at least 8 characters.'})

        if CustomUser.objects.filter(username=username).exists():
            return render(request, 'auth/register.html', {'error': 'Username already taken.'})

        if CustomUser.objects.filter(email=email).exists():
            return render(request, 'auth/register.html', {'error': 'Email already registered.'})

        user = CustomUser.objects.create_user(username=username, email=email, password=password1)
        user.role = 'student'
        user.save()

        login(request, user)
        return redirect('student_dashboard')

    return render(request, 'auth/register.html')
    