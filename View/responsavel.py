from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from Model.base import ResponsavelTecnico, Empresa

@login_required
def responsavel_lista(request):
    responsaveis = ResponsavelTecnico.objects.all().order_by('nome')
    return render(request, 'responsavel_lista.html', {
        'responsaveis': responsaveis
    })

@login_required
def responsavel_form(request, id_resp=None):
    if id_resp:
        responsavel = get_object_or_404(ResponsavelTecnico, id_resp_tecnico=id_resp)
        empresas_vinculadas = responsavel.empresas_atuais.all()
    else:
        responsavel = None
        empresas_vinculadas = []

    if request.method == 'POST':
        erro = False
        nome = request.POST.get('nome')
        cpf_raw = request.POST.get('cpf')
        cpf = ''.join(filter(str.isdigit, cpf_raw)) if cpf_raw else ''
        empresas_selecionadas = request.POST.getlist('empresas')

        if not nome or not cpf:
            messages.error(request, 'Nome e CPF são obrigatórios.')
            erro = True
        else:
            # django-cryptography doesn't support .filter(cpf=cpf) directly
            todos_responsaveis = ResponsavelTecnico.objects.all()
            exists = any(r.cpf == cpf and (not responsavel or r.id_resp_tecnico != responsavel.id_resp_tecnico) for r in todos_responsaveis)
                
            if exists:
                messages.error(request, 'Este CPF já está cadastrado no sistema para outro responsável.')
                erro = True
            else:
                if responsavel:
                    responsavel.nome = nome
                    responsavel.cpf = cpf
                    responsavel.save()
                    messages.success(request, f'Responsável {nome} atualizado com sucesso!')
                else:
                    responsavel = ResponsavelTecnico.objects.create(nome=nome, cpf=cpf)
                    messages.success(request, f'Responsável {nome} cadastrado com sucesso!')

                # Atualiza o vínculo das empresas
                if empresas_selecionadas:
                    Empresa.objects.filter(id_empresa__in=empresas_selecionadas).update(fk_resp_tecnico_atual=responsavel)
                
                return redirect('responsavel_lista')

        if erro:
            if not responsavel:
                class DummyResp: pass
                responsavel = DummyResp()
            responsavel.nome = nome
            responsavel.cpf = cpf_raw



    todas_empresas = Empresa.objects.all().order_by('nome')

    return render(request, 'responsavel_form.html', {
        'responsavel': responsavel,
        'empresas_vinculadas': empresas_vinculadas,
        'todas_empresas': todas_empresas
    })

@login_required
def responsavel_excluir(request, id_resp):
    responsavel = get_object_or_404(ResponsavelTecnico, id_resp_tecnico=id_resp)
    nome = responsavel.nome
    try:
        responsavel.delete()
        messages.success(request, f'Responsável {nome} removido.')
    except Exception as e:
        messages.error(request, f'Não foi possível excluir {nome} pois ele possui vínculos ativos.')
    
    return redirect('responsavel_lista')
