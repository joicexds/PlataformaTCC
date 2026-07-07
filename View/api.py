from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from Model.base import Empresa, ResponsavelTecnico

@login_required
def search_empresas(request):
    query = request.GET.get('q', '')
    if query:
        # Busca por Nome ou CNPJ
        empresas = Empresa.objects.filter(
            Q(nome__icontains=query) | 
            Q(cnpj__icontains=query)
        )[:10]  # Limite de 10 resultados para performance
    else:
        empresas = Empresa.objects.all()[:10]
    
    results = [
        {'id': emp.id_empresa, 'text': f"{emp.nome} ({emp.cnpj})"} 
        for emp in empresas
    ]
    return JsonResponse({'results': results})

@login_required
def search_responsaveis(request):
    query = request.GET.get('q', '')
    if query:
        # Busca por Nome ou CPF
        responsaveis = ResponsavelTecnico.objects.filter(
            Q(nome__icontains=query) | 
            Q(cpf__icontains=query)
        )[:10]
    else:
        responsaveis = ResponsavelTecnico.objects.all()[:10]
    
    results = [
        {'id': resp.id_resp_tecnico, 'text': f"{resp.nome} ({resp.cpf})"} 
        for resp in responsaveis
    ]
    return JsonResponse({'results': results})
