from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter, NumberFilter
from .models import Guild, Team, Character, Application
from .serializers import GuildSerializer, TeamSerializer, CharacterSerializer, ApplicationSerializer

class GuildViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Guild.objects.all()
    serializer_class = GuildSerializer
    queryset = Guild.objects.all().order_by('pk') # Added default ordering
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'realm']
    filterset_fields = ['name', 'realm', 'faction', 'region']
    ordering_fields = '__all__'

class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Team.objects.all().select_related('guild').order_by('pk') # Added default ordering
    serializer_class = TeamSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'short_name', 'guild__name'] # For partial match on Team Name
    filterset_fields = ['name', 'short_name', 'guild__id', 'guild__name']
    ordering_fields = '__all__'

# Custom FilterSet for Character to handle specific field names and lookups
class CharacterFilter(FilterSet):
    player_name = CharFilter(field_name='name', lookup_expr='icontains')
    guild_name = CharFilter(field_name='guild__name', lookup_expr='icontains')
    realm_name = CharFilter(field_name='realm', lookup_expr='icontains') # model field is 'realm'
    playable_class_name = CharFilter(field_name='playable_class__name', lookup_expr='icontains')
    playable_spec_name = CharFilter(field_name='active_spec__name', lookup_expr='icontains') # model field is 'active_spec'

    achievement_points_gt = NumberFilter(field_name='achievement_points', lookup_expr='gt')
    achievement_points_lt = NumberFilter(field_name='achievement_points', lookup_expr='lt')

    average_item_level_gt = NumberFilter(field_name='average_item_level', lookup_expr='gt')
    average_item_level_lt = NumberFilter(field_name='average_item_level', lookup_expr='lt')

    equipped_item_level_gt = NumberFilter(field_name='equipped_item_level', lookup_expr='gt')
    equipped_item_level_lt = NumberFilter(field_name='equipped_item_level', lookup_expr='lt')

    team_name = CharFilter(field_name='team__name', lookup_expr='icontains')
    # known_recipes_name = CharFilter(field_name='known_recipes__name', lookup_expr='icontains') # Removed

    class Meta:
        model = Character
        fields = [
            'player_name', 'guild_name', 'realm_name', 'playable_class_name', 'playable_spec_name',
            'achievement_points', 'achievement_points_gt', 'achievement_points_lt',
            'average_item_level', 'average_item_level_gt', 'average_item_level_lt',
            'equipped_item_level', 'equipped_item_level_gt', 'equipped_item_level_lt',
            'team_name', # Removed 'known_recipes_name',
            # Direct model fields for exact matches if needed
            'name', 'guild__id', 'realm', 'playable_class__id', 'active_spec__id', 'team__id'
        ]

class CharacterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Character.objects.all().prefetch_related('team', 'guild', 'playable_class', 'active_spec').order_by('pk') # Removed 'known_recipes'
    serializer_class = CharacterSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CharacterFilter # Use the custom filterset

    # General search can supplement specific filters if broad matching is also desired
    search_fields = [
        'name',
        'guild__name',
        'realm',
        'playable_class__name',
        'active_spec__name',
        'team__name',
        # 'known_recipes__name', # Removed
    ]
    ordering_fields = '__all__'


class ApplicationFilter(FilterSet):
    team_name = CharFilter(field_name='team__name', lookup_expr='icontains')

    class Meta:
        model = Application
        fields = ['name', 'discord_name', 'team_name', 'guild__id', 'team__id']


class ApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Application.objects.all().select_related('team', 'guild').order_by('pk') # Added default ordering
    serializer_class = ApplicationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ApplicationFilter
    search_fields = ['name', 'discord_name', 'team__name'] # For broad partial matches
    ordering_fields = '__all__'


# New View for searching characters by known recipe name
from rest_framework import generics
from rest_framework.response import Response
from .serializers import CharacterNameOnlySerializer # Will create this serializer

class RecipeCharacterSearchView(generics.ListAPIView):
    serializer_class = CharacterNameOnlySerializer
    filter_backends = [filters.SearchFilter] # Using DRF's SearchFilter for recipe name
    search_fields = ['known_recipes__name'] # This will search on the Character model's M2M field

    def get_queryset(self):
        """
        This view should return a list of all characters that have
        a known recipe matching the 'name' query parameter.
        """
        recipe_name = self.request.query_params.get('name', None)
        if recipe_name:
            # We need to filter characters based on the recipe name.
            # The SearchFilter will handle the ?search=<recipe_name> if we set it up on the view.
            # However, the request is to use a query param `name`.
            # Let's adjust to use DjangoFilterBackend for a specific field or modify to use search.
            # For simplicity with a 'name' query param, let's filter directly.
            return Character.objects.filter(known_recipes__name__icontains=recipe_name).values('name').distinct().order_by('name')
        return Character.objects.none() # Return no characters if no recipe name is provided

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # The queryset is already .values('name').distinct().order_by('name')
        # It returns a list of dictionaries like [{'name': 'Char1'}, {'name': 'Char2'}]
        # The CharacterNameOnlySerializer expects this format.
        serializer = self.get_serializer(queryset, many=True)
        # If we want a flat list of names: ['Char1', 'Char2']
        # character_names = [item['name'] for item in queryset]
        # return Response(character_names)
        return Response(serializer.data)
