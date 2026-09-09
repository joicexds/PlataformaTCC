from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # Gamification Fields
    total_xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    gems = models.IntegerField(default=0)
    streak_days = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    def add_xp(self, amount):
        self.total_xp += amount
        # Level up logic: 1 level per 1000 XP
        new_level = (self.total_xp // 1000) + 1
        if new_level > self.level:
            self.level = new_level
            self.gems += 50  # Bonus gems for leveling up
        self.save()
        return new_level > self.level

    def __str__(self):
        return f"Perfil de {self.user.username}"

class UserMission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='missions')
    mission_code = models.CharField(max_length=100)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'mission_code')
        
    def __str__(self):
        return f"{self.user.username} - {self.mission_code}"


class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    
    # Categorias baseadas no documento de interface e usabilidade (doc)
    rating_design = models.IntegerField(default=5, help_text="Avaliação do Design Visual e Conceito Minimalista")
    rating_colors = models.IntegerField(default=5, help_text="Paleta de Cores e Conforto Visual")
    rating_typography = models.IntegerField(default=5, help_text="Tipografia e Legibilidade")
    rating_usability = models.IntegerField(default=5, help_text="Usabilidade e Navegação")
    rating_vocational_test = models.IntegerField(default=5, help_text="Experiência no Teste Vocacional e Autoconhecimento")
    rating_responsiveness = models.IntegerField(default=5, help_text="Responsividade e Desempenho")
    
    overall_rating = models.IntegerField(default=5, help_text="Satisfação Geral com a Plataforma")
    
    # Perfil do Respondente
    age = models.IntegerField(null=True, blank=True, help_text="Idade do usuário")
    is_working = models.CharField(max_length=100, blank=True, null=True, help_text="Já atua profissionalmente?")
    work_experience_time = models.CharField(max_length=100, blank=True, null=True, help_text="Tempo de atuação profissional")
    
    favorite_feature = models.CharField(max_length=150, blank=True, null=True, help_text="Recurso Favorito")
    suggestions = models.TextField(blank=True, null=True, help_text="Comentários e Sugestões de Melhoria")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback de {self.user.username} ({self.created_at.strftime('%d/%m/%Y')})"
