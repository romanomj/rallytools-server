from django.contrib import admin
from .models import *

@admin.register(Guild)
class GuildAdmin(admin.ModelAdmin):
    pass

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    pass

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'name', 'level')
    list_display = ('name', 'realm', 'level', 'playable_class__name')
    search_fields = ('name',)
    ordering = ['name']

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    pass
