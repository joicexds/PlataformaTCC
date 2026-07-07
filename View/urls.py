from django.urls import path
from django.contrib.auth.views import LogoutView
from View.home import home, CustomLoginView, alertas_lista
from View.responsavel import responsavel_lista, responsavel_form, responsavel_excluir
from View.empresa import empresa_lista, empresa_form, empresa_excluir, empresa_detalhe
from View.tipo_documento import tipo_documento_index, tipo_documento_excluir
from View.inspecao import inspecao_lista, inspecao_form, emitir_inspecao
from View.tipo_inspecao import tipo_inspecao_index, tipo_inspecao_form, tipo_inspecao_excluir
from View.colaborador import colaborador_lista, colaborador_form, colaborador_excluir
from View.usuario import usuario_lista, usuario_form, usuario_mudar_senha, usuario_excluir
from View.documentos import necessidade_lista, necessidade_form, necessidade_excluir, entrega_lista, entrega_form, entrega_excluir

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Usuários
    path('usuarios/', usuario_lista, name='usuario_lista'),
    path('usuario/novo/', usuario_form, name='usuario_novo'),
    path('usuario/<int:id_usuario>/', usuario_form, name='usuario_editar'),
    path('usuario/<int:id_usuario>/senha/', usuario_mudar_senha, name='usuario_mudar_senha'),
    path('usuario/<int:id_usuario>/excluir/', usuario_excluir, name='usuario_excluir'),
    
    # Colaboradores
    path('colaboradores/', colaborador_lista, name='colaborador_lista'),
    path('colaborador/novo/', colaborador_form, name='colaborador_novo'),
    path('colaborador/<int:id_colab>/', colaborador_form, name='colaborador_editar'),
    path('colaborador/<int:id_colab>/excluir/', colaborador_excluir, name='colaborador_excluir'),
    
    # Inspeções
    path('inspecoes/', inspecao_lista, name='inspecao_lista'),
    path('inspecao/nova/', inspecao_form, name='inspecao_nova'),
    path('inspecao/emitir/', emitir_inspecao, name='inspecao_emitir'),
    path('inspecao/<int:id_inspecao>/', inspecao_form, name='inspecao_editar'),
    
    # Responsáveis Técnicos
    path('responsaveis/', responsavel_lista, name='responsavel_lista'),
    path('responsavel/novo/', responsavel_form, name='responsavel_novo'),
    path('responsavel/<int:id_resp>/', responsavel_form, name='responsavel_editar'),
    path('responsavel/<int:id_resp>/excluir/', responsavel_excluir, name='responsavel_excluir'),

    # Empresas
    path('empresas/', empresa_lista, name='empresa_lista'),
    path('empresa/nova/', empresa_form, name='empresa_novo'),
    path('empresa/<int:id_empresa>/', empresa_form, name='empresa_editar'),
    path('empresa/<int:id_empresa>/detalhe/', empresa_detalhe, name='empresa_detalhe'),

    path('empresa/<int:id_empresa>/excluir/', empresa_excluir, name='empresa_excluir'),

    # Tipos de Documento
    path('tipos-documento/', tipo_documento_index, name='tipo_documento_index'),
    path('tipo-documento/<int:id_tipo>/', tipo_documento_index, name='tipo_documento_editar'),
    path('tipo-documento/<int:id_tipo>/excluir/', tipo_documento_excluir, name='tipo_documento_excluir'),
    
    # Tipos de Inspeção
    path('tipos-inspecao/', tipo_inspecao_index, name='tipo_inspecao_index'),
    path('tipo-inspecao/<int:id_tipo_inspecao>/', tipo_inspecao_form, name='tipo_inspecao_editar'),
    path('tipo-inspecao/<int:id_tipo_inspecao>/excluir/', tipo_inspecao_excluir, name='tipo_inspecao_excluir'),
    
    # Entregas de Documentos
    path('entregas/', entrega_lista, name='entrega_lista'),
    path('entrega/nova/', entrega_form, name='entrega_novo'),
    path('entrega/<int:id_entrega>/', entrega_form, name='entrega_editar'),
    path('entrega/<int:id_entrega>/excluir/', entrega_excluir, name='entrega_excluir'),
    
    path('', home, name='home'),
    path('alertas/', alertas_lista, name='alertas_lista'),
]
