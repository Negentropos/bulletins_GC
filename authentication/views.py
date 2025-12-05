from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from . import forms
from . import models
from django.contrib.auth import login, authenticate, logout # import des fonctions login et authenticate
from bulletins.models import Journal
def login_page(request):
    form = forms.LoginForm()
    message = ''
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                log=Journal(utilisateur=request.user,message='connexion')
                log.save()
                return redirect('home')
            else:
                message = 'Identifiants invalides.'
    return render(
        request, 'authentication/login.html', context={'form': form, 'message': message})

@login_required
def enseignants_list(request):
    enseignants=models.User.objects.all().order_by('last_name')
    return render(request,'authentication/enseignants_list.html',context={"enseignants":enseignants})

@login_required
def myProfil(request):
    return render(request,'authentication/my_profil.html')

@login_required
def logout_user(request):
    log = Journal(utilisateur=request.user, message='déconnexion')
    log.save()
    logout(request)
    return redirect('login')