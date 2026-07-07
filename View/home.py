from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from View.registro import RegistroUsuarioForm

class CustomLoginView(LoginView):
    template_name = 'login.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Force logout if the user visits the login page while already logged in
        if request.user.is_authenticated:
            logout(request)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['registro_form'] = RegistroUsuarioForm()
        return context

from Model.base import EntregaDocumento, Colaborador, Empresa, TipoDocumento
from datetime import date
from dateutil.relativedelta import relativedelta

@login_required
def home(request):
    hoje = date.today()
    
    # Limites para Documentos
    limite_doc_critico = hoje + relativedelta(days=15)
    limite_doc_andamento = hoje + relativedelta(days=30)
    
    # Limites para Colaboradores (validade de 1 ano)
    limite_colab_critico = hoje - relativedelta(years=1) + relativedelta(days=15)
    limite_colab_andamento = hoje - relativedelta(years=1) + relativedelta(days=30)
    
    # CRÍTICOS (<= 15 dias)
    doc_criticos = EntregaDocumento.objects.filter(data_vencimento_calculada__lte=limite_doc_critico).count()
    colab_criticos = Colaborador.objects.filter(ativo=True, data_entrada__lte=limite_colab_critico).count()
    
    # Empresas para o painel
    todas_empresas = Empresa.objects.select_related('fk_resp_tecnico_atual').all().order_by('nome')
    
    # Documentos Obrigatórios Faltantes (Não entregues)
    tipos_obrigatorios = TipoDocumento.objects.filter(obrigatorio=True)
    qtd_obrigatorios_faltantes = 0
    for emp in todas_empresas:
        for tdoc in tipos_obrigatorios:
            tem_entrega = EntregaDocumento.objects.filter(fk_empresa=emp, fk_tipo_doc=tdoc).exists()
            if not tem_entrega:
                qtd_obrigatorios_faltantes += 1
                
    alertas_criticos = doc_criticos + colab_criticos + qtd_obrigatorios_faltantes
    
    # EM ANDAMENTO (16 a 30 dias)
    doc_andamento = EntregaDocumento.objects.filter(
        data_vencimento_calculada__gt=limite_doc_critico,
        data_vencimento_calculada__lte=limite_doc_andamento
    ).count()
    colab_andamento = Colaborador.objects.filter(
        ativo=True,
        data_entrada__gt=limite_colab_critico,
        data_entrada__lte=limite_colab_andamento
    ).count()
    alertas_andamento = doc_andamento + colab_andamento
    

    context = {
        'pendencias': doc_criticos + doc_andamento,
        'alertas_criticos': alertas_criticos,
        'em_andamento': alertas_andamento,
        'empresas': todas_empresas
    }
    return render(request, 'home.html', context)


@login_required
def alertas_lista(request):
    hoje = date.today()
    
    # Limites para Documentos
    limite_doc_critico = hoje + relativedelta(days=15)
    limite_doc_andamento = hoje + relativedelta(days=30)
    
    # Limites para Colaboradores (validade de 1 ano)
    limite_colab_critico = hoje - relativedelta(years=1) + relativedelta(days=15)
    limite_colab_andamento = hoje - relativedelta(years=1) + relativedelta(days=30)
    
    # CRÍTICOS LISTAS
    doc_criticos_lista = EntregaDocumento.objects.filter(data_vencimento_calculada__lte=limite_doc_critico).select_related('fk_empresa', 'fk_tipo_doc').order_by('data_vencimento_calculada')
    colab_criticos_lista = Colaborador.objects.filter(ativo=True, data_entrada__lte=limite_colab_critico).select_related('fk_empresa').order_by('data_entrada')
    
    # EM ANDAMENTO LISTAS
    doc_andamento_lista = EntregaDocumento.objects.filter(
        data_vencimento_calculada__gt=limite_doc_critico,
        data_vencimento_calculada__lte=limite_doc_andamento
    ).select_related('fk_empresa', 'fk_tipo_doc').order_by('data_vencimento_calculada')
    colab_andamento_lista = Colaborador.objects.filter(
        ativo=True,
        data_entrada__gt=limite_colab_critico,
        data_entrada__lte=limite_colab_andamento
    ).select_related('fk_empresa').order_by('data_entrada')

    # Validação de Documentos Obrigatórios Pendentes (Apenas Faltantes, pois Vencidos já caem em doc_criticos)
    todas_empresas = Empresa.objects.all()
    tipos_obrigatorios = TipoDocumento.objects.filter(obrigatorio=True)
    alertas_obrigatorios_faltantes = []
    
    for emp in todas_empresas:
        for tdoc in tipos_obrigatorios:
            tem_entrega = EntregaDocumento.objects.filter(fk_empresa=emp, fk_tipo_doc=tdoc).exists()
            if not tem_entrega:
                alertas_obrigatorios_faltantes.append({
                    'empresa': emp,
                    'documento': tdoc,
                    'status': 'Faltante (Obrigatório)',
                    'cor': '#ef4444' # red
                })

    context = {
        'doc_criticos': doc_criticos_lista,
        'colab_criticos': colab_criticos_lista,
        'doc_andamento': doc_andamento_lista,
        'colab_andamento': colab_andamento_lista,
        'alertas_obrigatorios': alertas_obrigatorios_faltantes
    }
    return render(request, 'alertas_lista.html', context)
