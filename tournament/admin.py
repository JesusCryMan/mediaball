from django.contrib import admin
from django.utils.html import format_html
from .models import Team, Player, Match, PlayerStats

class PlayerStatsInline(admin.TabularInline):
    model = PlayerStats
    extra = 4  # Ровно под формат 3х3 + замена
    verbose_name = "Протокол игрока"
    verbose_name_plural = "Статистика игроков (Протокол матча)"
    
    # Делаем выпадающий список игроков более информативным
    # (показывает команду и категорию рядом с именем)
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "player" and 'object_id' in request.resolver_match.kwargs:
            match_id = request.resolver_match.kwargs['object_id']
            try:
                match = Match.objects.get(pk=match_id)
                kwargs["queryset"] = Player.objects.filter(
                    team__in=[match.team_1, match.team_2]
                ).select_related('team')
            except Match.DoesNotExist:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'count_players')
    search_fields = ('name',)

    # Выводим количество игроков в команде прямо в список
    @admin.display(description="Игроков в составе")
    def count_players(self, obj):
        return obj.players.count()


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    # Добавили 'nickname' в список вывода
    list_display = ('id', 'name', 'nickname', 'get_team_badge', 'get_category_badge')
    list_filter = ('team', 'category')
    search_fields = ('name', 'nickname')  # Теперь можно искать игроков и по никнейму
    list_select_related = ('team',)  # Убирает N+1 проблему с запросами

    @admin.display(description="Команда")
    def get_team_badge(self, obj):
        return format_html('<b style="color: #f97316;">{}</b>', obj.team.name)

    @admin.display(description="Категория")
    def get_category_badge(self, obj):
        # Ключи переведены в верхний регистр в соответствии с новыми моделями
        colors = {'PRO': '#ef4444', 'MEDIA': '#3b82f6', 'AMATEUR': '#10b981'}
        color = colors.get(obj.category.upper(), '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_category_display()
        )


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    # Кастомный вывод счета с подсветкой победителя
    @admin.display(description="Результат (Счет)")
    def display_score(self, obj):
        if not obj.is_finished:
            return format_html('<span style="color: #6b7280; font-style: italic;">Предстоит</span>')
        
        s1, s2 = obj.score_1, obj.score_2
        if s1 > s2:
            return format_html('<b style="color: #22c55e;">{}</b> : {}', s1, s2)
        elif s2 > s1:
            return format_html('{} : <b style="color: #22c55e;">{}</b>', s1, s2)
        return format_html('<b>{} : {}</b>', s1, s2)

    list_display = ('id', 'team_1', 'display_score', 'team_2', 'date', 'status_badges')
    list_filter = ('is_finished', 'is_overtime', 'date')
    search_fields = ('team_1__name', 'team_2__name')
    list_select_related = ('team_1', 'team_2')
    
    # Переносим инлайн протокола внутрь матча
    inlines = [PlayerStatsInline]

    # Красивые бейджи статусов матча в общем списке
    @admin.display(description="Статус")
    def status_badges(self, obj):
        badges = []
        if obj.is_finished:
            badges.append('<span style="color: #10b981;">✓ Завершен</span>')
        else:
            badges.append('<span style="color: #f59e0b;">⏳ Ожидание</span>')
        if obj.is_overtime:
            badges.append('<span style="color: #ef4444; font-weight: bold;">[ОТ]</span>')
        return format_html(" ".join(badges))

    # Группируем поля в карточке редактирования матча для эстетики
    fieldsets = (
        ("Участники матча", {
            'fields': (('team_1', 'team_2'),)
        }),
        ("Результат игры", {
            'fields': (('score_1', 'score_2'), ('is_finished', 'is_overtime'))
        }),
        ("Дата и время", {
            'fields': ('date',),
        }),
        ("Медиа контент", {
            'fields': ('youtube_url', 'tiktok_url'),
        }),
    )