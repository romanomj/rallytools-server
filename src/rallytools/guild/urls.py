from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GuildViewSet, TeamViewSet, CharacterViewSet, ApplicationViewSet, RecipeCharacterSearchView

router = DefaultRouter()
router.register(r'guilds', GuildViewSet, basename='guild')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'characters', CharacterViewSet, basename='character')
router.register(r'applications', ApplicationViewSet, basename='application')

urlpatterns = [
    path('', include(router.urls)),
    path('recipes/search-characters/', RecipeCharacterSearchView.as_view(), name='recipe-character-search'),
]
