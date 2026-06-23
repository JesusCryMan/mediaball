import os
from django.db import models
from django.core.exceptions import ValidationError

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название команды")
    logo = models.ImageField(upload_to='teams/', blank=True, null=True, verbose_name="Логотип команды")

    class Meta:
        verbose_name = "Команда"
        verbose_name_plural = "Команды"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def logo_name(self):
        """Автоматически генерирует безопасный путь к логотипу для шаблона"""
        safe_name = "".join([c for c in self.name.lower() if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '-')
        return f"tournament/img/{safe_name}.png"


class Player(models.Model):
    PLAYER_CATEGORIES = [
        ('PRO', 'Профи'),
        ('MEDIA', 'Медиа'),
        ('AMATEUR', 'Любитель'),
    ]
    
    # Существующие поля
    name = models.CharField(max_length=100, verbose_name="Имя игрока")
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name="Никнейм (Игровое имя)")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players', verbose_name="Команда")
    avatar = models.ImageField(upload_to='players/', blank=True, null=True, verbose_name="Аватар игрока")
    category = models.CharField(max_length=10, choices=PLAYER_CATEGORIES, default='AMATEUR', verbose_name="Категория игрока")

    # НОВЫЕ ПОЛЯ ИЗ МАКЕТА
    age = models.PositiveIntegerField(blank=True, null=True, verbose_name="Возраст")
    height = models.PositiveIntegerField(blank=True, null=True, verbose_name="Рост (см)")
    weight = models.PositiveIntegerField(blank=True, null=True, verbose_name="Вес (кг)")
    position = models.CharField(max_length=100, blank=True, null=True, default="Атакующий защитник", verbose_name="Позиция")
    leading_hand = models.CharField(
        max_length=20, 
        choices=[('Правая', 'Правая'), ('Левая', 'Левая')], 
        default='Правая', 
        verbose_name="Ведущая рука"
    )

    class Meta:
        verbose_name = "Игрок"
        verbose_name_plural = "Игроки"
        ordering = ['name']

    def __str__(self):
        if self.nickname:
            return f"{self.name} \"{self.nickname}\" ({self.get_category_display()})"
        return f"{self.name} ({self.get_category_display()})"

    class Meta:
        verbose_name = "Игрок"
        verbose_name_plural = "Игроки"
        ordering = ['name']

    def __str__(self):
        if self.nickname:
            return f"{self.name} \"{self.nickname}\" ({self.get_category_display()})"
        return f"{self.name} ({self.get_category_display()})"


class Match(models.Model):
    team_1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team1', verbose_name="Команда 1")
    team_2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team2', verbose_name="Команда 2")
    
    score_1 = models.PositiveIntegerField(default=0, verbose_name="Очки Команны 1")
    score_2 = models.PositiveIntegerField(default=0, verbose_name="Очки Команды 2")
    
    date = models.DateTimeField(verbose_name="Дата и время матча")
    is_finished = models.BooleanField(default=False, verbose_name="Матч завершен?")
    is_overtime = models.BooleanField(default=False, verbose_name="Был овертайм?")
    
    youtube_url = models.URLField(blank=True, null=True, verbose_name="Ссылка на YouTube")
    tiktok_url = models.URLField(blank=True, null=True, verbose_name="Ссылка на TikTok")

    class Meta:
        verbose_name = "Матч"
        verbose_name_plural = "Матчи"
        ordering = ['-date']

    def __str__(self):
        status = f"({self.score_1}:{self.score_2})" if self.is_finished else "(Предстоит)"
        return f"{self.team_1} vs {self.team_2} — {self.date.strftime('%d.%m %H:%M')} {status}"

    def clean(self):
        super().clean()
        if self.team_1_id and self.team_2_id and self.team_1 == self.team_2:
            raise ValidationError("Команда не может играть сама с собой!")


class PlayerStats(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='player_stats', verbose_name="Матч")
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='stats', verbose_name="Игрок")
    points = models.PositiveIntegerField(default=0, verbose_name="Набранные очки")

    class Meta:
        verbose_name = "Статистика игрока в матче"
        verbose_name_plural = "Статистика игроков в матчах"
        unique_together = ('match', 'player')

    def __str__(self):
        return f"{self.player.name} — {self.points} очк. (Матч: {self.match_id})"

    def clean(self):
        super().clean()
        if self.match_id and self.player_id:
            allowed_teams = [self.match.team_1, self.match.team_2]
            if self.player.team not in allowed_teams:
                raise ValidationError(f"Игрок {self.player.name} не играет за участников этого матча!")