from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Administrateur'),
        ('PROF', 'Professeur'),
        ('INFO','Visiteur'),
    )
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, verbose_name='Rôle')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
    def nom_court(self):
        return f"{self.first_name[0]}. {self.last_name}"



