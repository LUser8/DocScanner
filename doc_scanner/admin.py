from django.contrib import admin
from .models import GoogleAppConfiguration, Source, FilesAddress

admin.site.register([GoogleAppConfiguration, Source, FilesAddress])


