from django.contrib import admin
from .models import *

class ReadOnlyAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PlayableRace)
class PlayableRaceAdmin(ReadOnlyAdmin):
    pass

@admin.register(PlayableClass)
class PlayableClassAdmin(ReadOnlyAdmin):
    pass

@admin.register(PlayableSpecialization)
class PlayableSpecializationAdmin(ReadOnlyAdmin):
    pass

@admin.register(Profession)
class ProfessionAdmin(ReadOnlyAdmin):
    pass

@admin.register(ProfessionSkillTier)
class ProfessionSkillTierAdmin(ReadOnlyAdmin):
    list_display = ('id', 'name', 'profession__name')
    search_fields = ('id', 'name', 'profession__name')
    ordering = ['profession', 'name']

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Recipe)
class RecipeAdmin(ReadOnlyAdmin):
    list_display = ('name', 'profession', 'profession_skill_tier')
    search_fields = ('id', 'name', 'profession__name', 'profession_skill_tier__name')
    ordering = ['profession', 'profession_skill_tier', 'name']

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Reagent)
class ReagentAdmin(ReadOnlyAdmin):
    pass

@admin.register(RecipeReagent)
class RecipeReagentAdmin(ReadOnlyAdmin):
    pass

@admin.register(Item)
class ItemAdmin(ReadOnlyAdmin):
    pass
