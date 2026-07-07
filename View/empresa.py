from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from Model.base import Empresa, ResponsavelTecnico

@login_required
def empresa_lista(request):
    empresas = Empresa.objects.all()
    return render(request, 'empresa_lista.html', {
        'empresas': empresas
    })

@login_required
def empresa_form(request, id_empresa=None):
    if id_empresa:
        empresa = get_object_or_404(Empresa, id_empresa=id_empresa)
    else:
        empresa = None

    if request.method == 'POST':
        erro = False
        nome = request.POST.get('nome')
        endereco = request.POST.get('endereco')
        cnpj = request.POST.get('cnpj')
        id_resp = request.POST.get('fk_resp_tecnico_atual')
        
        if not nome or not cnpj:
            messages.error(request, 'O Nome e o CNPJ são obrigatórios.')
            erro = True
        else:
            resp_tecnico = get_object_or_404(ResponsavelTecnico, id_resp_tecnico=id_resp) if id_resp else None

            exists = Empresa.objects.filter(cnpj=cnpj)
            if empresa:
                exists = exists.exclude(id_empresa=empresa.id_empresa)
                
            if exists.exists():
                messages.error(request, 'Este CNPJ já está cadastrado no sistema para outra empresa.')
                erro = True
            else:
                if empresa:
                    empresa.nome = nome
                    empresa.endereco = endereco
                    empresa.cnpj = cnpj
                    empresa.fk_resp_tecnico_atual = resp_tecnico
                    empresa.save()
                    messages.success(request, f'Empresa "{nome}" atualizada com sucesso!')
                else:
                    Empresa.objects.create(
                        nome=nome,
                        endereco=endereco,
                        cnpj=cnpj,
                        fk_resp_tecnico_atual=resp_tecnico
                    )
                    messages.success(request, f'Empresa "{nome}" cadastrada com sucesso!')
                
                return redirect('empresa_lista')
                
        if erro:
            if not empresa:
                class DummyEmpresa: pass
                empresa = DummyEmpresa()
            empresa.nome = nome
            empresa.endereco = endereco
            empresa.cnpj = cnpj
            if id_resp:
                empresa.fk_resp_tecnico_atual_id = int(id_resp)

    responsaveis = ResponsavelTecnico.objects.all()
    
    return render(request, 'empresa_form.html', {
        'empresa': empresa,
        'responsaveis': responsaveis
    })

@login_required
def empresa_excluir(request, id_empresa):
    empresa = get_object_or_404(Empresa, id_empresa=id_empresa)
    nome = empresa.nome
    try:
        empresa.delete()
        messages.success(request, f'Empresa "{nome}" excluída com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir empresa: {str(e)}')
    return redirect('empresa_lista')

@login_required
def empresa_detalhe(request, id_empresa):
    empresa = get_object_or_404(Empresa, id_empresa=id_empresa)
    colaboradores = empresa.colaboradores.filter(ativo=True).order_by('-data_entrada')
    documentos = empresa.entregas_documento.all().order_by('-data_entrega')
    visitas = empresa.visitas.all().order_by('-data_evento')
    
    return render(request, 'empresa_detalhe.html', {
        'empresa': empresa,
        'colaboradores': colaboradores,
        'documentos': documentos,
        'visitas': visitas
    })
