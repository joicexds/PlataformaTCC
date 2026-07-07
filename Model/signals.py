import inspect
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import LogAuditoria, Usuario
from django.apps import apps
from django.forms.models import model_to_dict

from Model.middleware import get_current_user

@receiver(post_save)
def log_post_save(sender, instance, created, **kwargs):
    if sender._meta.app_label != 'core' or sender == LogAuditoria or sender == Usuario:
        return
        
    tipo = "Inserir" if created else "Alterar"
    
    # Prepara descricao com os dados
    try:
        dados = model_to_dict(instance)
        desc = f"Dados: {dados}"
    except Exception:
        desc = f"Instância de {sender.__name__}"

    LogAuditoria.objects.create(
        fk_usuario=get_current_user(),
        codigo=instance.pk,
        tipo=tipo,
        descricao=f"Tabela: {sender.__name__}. {desc}"
    )

@receiver(post_delete)
def log_post_delete(sender, instance, **kwargs):
    if sender._meta.app_label != 'core' or sender == LogAuditoria or sender == Usuario:
        return
        
    try:
        dados = model_to_dict(instance)
        desc = f"Dados apagados: {dados}"
    except Exception:
        desc = f"Instância apagada de {sender.__name__}"

    LogAuditoria.objects.create(
        fk_usuario=get_current_user(),
        codigo=instance.pk,
        tipo="Deletar",
        descricao=f"Tabela: {sender.__name__}. {desc}"
    )
