# authentication/forms.py
from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(max_length=63, widget=forms.TextInput(attrs={'placeholder': 'Identifiant'}))
    password = forms.CharField(max_length=63, widget=forms.PasswordInput(attrs={'placeholder': 'Mot de passe'}))
