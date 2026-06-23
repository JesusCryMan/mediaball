from django.urls import path
from . import views

urlpatterns = [
    # Если главной страницей у тебя будет турнирная таблица:
    path('', views.tournament_table_view, name='index'), 
    
    # Остальные страницы лиги:
    path('matches/', views.matches_schedule_view, name='matches'),
    path('stats/', views.league_stats_view, name='stats'),
    path('teams/', views.teams_list_view, name='teams'),
    path('players/', views.players_list_view, name='players_list'),
    path('players/<int:player_id>/', views.player_detail_view, name='player_detail'),
]