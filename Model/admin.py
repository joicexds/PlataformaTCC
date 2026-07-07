from django.contrib import admin
from Model.base import (
    LogAuditoria, ResponsavelTecnico, Empresa, TipoDocumento, 
    TipoInspecao, Colaborador, NecessidadeDocumento, 
    EntregaDocumento, Visita, Usuario
)
from django.contrib.auth.admin import UserAdmin

@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    pass

@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'fk_usuario', 'data_hora', 'codigo')
    list_filter = ('tipo', 'data_hora')
    search_fields = ('descricao', 'codigo')

@admin.register(ResponsavelTecnico)
class ResponsavelTecnicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf')
    search_fields = ('nome', 'cpf')

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'fk_resp_tecnico_atual')
    search_fields = ('nome', 'cnpj')
    list_filter = ('fk_resp_tecnico_atual',)

@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'prazo_validade_meses', 'obrigatorio')
    list_filter = ('obrigatorio',)

@admin.register(TipoInspecao)
class TipoInspecaoAdmin(admin.ModelAdmin):
    list_display = ('nome',)

@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'fk_empresa', 'cpf', 'ativo')
    list_filter = ('ativo', 'fk_empresa')
    search_fields = ('nome', 'cpf')

@admin.register(NecessidadeDocumento)
class NecessidadeDocumentoAdmin(admin.ModelAdmin):
    list_display = ('fk_empresa', 'fk_tipo_doc')
    list_filter = ('fk_empresa', 'fk_tipo_doc')

@admin.register(EntregaDocumento)
class EntregaDocumentoAdmin(admin.ModelAdmin):
    list_display = ('fk_empresa', 'fk_tipo_doc', 'data_entrega', 'data_vencimento_calculada')
    list_filter = ('fk_empresa', 'fk_tipo_doc', 'data_entrega')
    readonly_fields = ('data_vencimento_calculada',)

@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ('fk_empresa', 'fk_tipo_inspecao', 'data_evento', 'fk_resp_tecnico_historico')
    list_filter = ('fk_empresa', 'fk_tipo_inspecao', 'data_evento')
    search_fields = ('observacao',)
