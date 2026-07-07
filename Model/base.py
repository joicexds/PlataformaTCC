from django.db import models
from django.contrib.auth.models import AbstractUser
from django_cryptography.fields import encrypt
from django.utils import timezone
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

class Usuario(AbstractUser):
    area = models.CharField(max_length=100, null=True, blank=True)
    cpf = encrypt(models.CharField(max_length=14, null=True, blank=True))
    endereco = models.TextField(null=True, blank=True)
    
    class Meta:
        app_label = 'core'

class LogAuditoria(models.Model):
    class Meta:
        app_label = 'core'
    id_log = models.AutoField(primary_key=True)
    fk_usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    codigo = models.IntegerField(help_text="ID do registro afetado")
    tipo = models.CharField(max_length=50, help_text="Ex: Inserir, Alterar, Deletar")
    data_hora = models.DateTimeField(auto_now_add=True)
    descricao = models.TextField()

    def __str__(self):
        return f"{self.tipo} em {self.data_hora}"

class ResponsavelTecnico(models.Model):
    class Meta:
        app_label = 'core'
    id_resp_tecnico = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255)
    cpf = encrypt(models.CharField(max_length=14))

    def __str__(self):
        return self.nome

class Empresa(models.Model):
    class Meta:
        app_label = 'core'
    id_empresa = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255)
    endereco = models.TextField()
    cnpj = models.CharField(max_length=18, unique=True)
    fk_resp_tecnico_atual = models.ForeignKey(ResponsavelTecnico, on_delete=models.RESTRICT, related_name='empresas_atuais', null=True, blank=True)

    def __str__(self):
        return self.nome

class TipoDocumento(models.Model):
    class Meta:
        app_label = 'core'
    id_tipo_doc = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255)
    prazo_validade_meses = models.IntegerField()
    obrigatorio = models.BooleanField(default=False)

    def __str__(self):
        return self.nome

class TipoInspecao(models.Model):
    class Meta:
        app_label = 'core'
    id_tipo_inspecao = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome

class Colaborador(models.Model):
    class Meta:
        app_label = 'core'
    id_colaborador = models.AutoField(primary_key=True)
    fk_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='colaboradores')
    nome = models.CharField(max_length=255)
    cpf = encrypt(models.CharField(max_length=14))
    data_entrada = models.DateField()
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class NecessidadeDocumento(models.Model):
    class Meta:
        app_label = 'core'
    id_necessidade = models.AutoField(primary_key=True)
    fk_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='necessidades_documento')
    fk_tipo_doc = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.fk_empresa.nome} - {self.fk_tipo_doc.nome}"

class EntregaDocumento(models.Model):
    class Meta:
        app_label = 'core'
    id_entrega = models.AutoField(primary_key=True)
    fk_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='entregas_documento')
    fk_tipo_doc = models.ForeignKey(TipoDocumento, on_delete=models.RESTRICT)
    fk_resp_tecnico_entrega = models.ForeignKey(ResponsavelTecnico, on_delete=models.RESTRICT)
    data_entrega = models.DateField()
    data_vencimento_calculada = models.DateField(blank=True, null=True)
    arquivo = models.FileField(upload_to='documentos/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.fk_tipo_doc and self.data_entrega:
            if isinstance(self.data_entrega, str):
                self.data_entrega = datetime.strptime(self.data_entrega, '%Y-%m-%d').date()
            self.data_vencimento_calculada = self.data_entrega + relativedelta(months=self.fk_tipo_doc.prazo_validade_meses)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fk_empresa.nome} - {self.fk_tipo_doc.nome} entregue em {self.data_entrega}"

class Visita(models.Model):
    class Meta:
        app_label = 'core'
    id_visita = models.AutoField(primary_key=True)
    fk_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='visitas')
    fk_tipo_inspecao = models.ForeignKey(TipoInspecao, on_delete=models.RESTRICT)
    fk_resp_tecnico_historico = models.ForeignKey(ResponsavelTecnico, on_delete=models.RESTRICT)
    data_evento = models.DateField()
    anexo = models.FileField(upload_to='inspecoes/', null=True, blank=True)
    observacao = models.TextField()

    def __str__(self):
        return f"Visita {self.fk_tipo_inspecao.nome} - {self.fk_empresa.nome} ({self.data_evento})"
