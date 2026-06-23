from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Sum
from .models import Team, Player, Match, PlayerStats

def tournament_table_view(request):
    """ Главная страница (Index) с турнирной таблицей """
    table_data = Team.objects.all()
    context = {
        'table_data': table_data,
        'current_page': 'index',
    }
    return render(request, 'tournament/index.html', context)


def matches_schedule_view(request):
    """ Страница расписания и результатов матчей """
    now = timezone.now()
    
    # Предстоящие матчи
    upcoming_matches = Match.objects.filter(
        date__gt=now, 
        is_finished=False
    ).select_related('team_1', 'team_2').order_by('date')
    
    # Сыгранные матчи
    past_matches = Match.objects.filter(
        is_finished=True
    ).select_related('team_1', 'team_2').prefetch_related('player_stats__player').order_by('-date')

    context = {
        'upcoming_matches': upcoming_matches,
        'past_matches': past_matches,
        'current_page': 'matches',
    }
    return render(request, 'tournament/matches.html', context)

def players_list_view(request):
    # Исправлено: теперь мы используем правильный метод .order_by('name')
    players = Player.objects.select_related('team').order_by('category', 'name')
    return render(request, 'tournament/players.html', {'players': players})

def teams_list_view(request):
    """ Страница со списком всех команд """
    teams = Team.objects.prefetch_related('players').all()
    context = {
        'teams': teams,
        'current_page': 'teams',
    }
    return render(request, 'tournament/teams.html', context)

def player_detail_view(request, player_id):
    player = get_object_or_404(Player.objects.select_related('team'), pk=player_id)
    
    # Считаем общую сумму очков игрока во всех матчах протокола
    total_points = player.stats.aggregate(total=Sum('points'))['total'] or 0
    
    return render(request, 'tournament/player_profile.html', {
        'player': player,
        'total_points': total_points # Прокидываем переменную в шаблон!
    })

def league_stats_view(request):
    """ Страница индивидуальной статистики лидеров (Бомбардиры) """
    category_filter = request.GET.get('category', 'ALL')
    players_queryset = Player.objects.select_related('team')

    if category_filter and category_filter != 'ALL':
        players_queryset = players_queryset.filter(category=category_filter)

    # Суммируем очки игроков за весь сезон
    stats_data = players_queryset.annotate(
        total_points=Sum('stats__points')
    ).filter(
        total_points__gt=0
    ).order_by('-total_points')

    context = {
        'stats_data': stats_data,
        'current_category': category_filter,
        'current_page': 'stats',
    }
    return render(request, 'tournament/stats.html', context)