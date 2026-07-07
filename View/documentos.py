from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from Model.base import NecessidadeDocumento, EntregaDocumento, Empresa, TipoDocumento, ResponsavelTecnico

@login_required
def necessidade_lista(request):
    necessidades = NecessidadeDocumento.objects.all().select_related('fk_empresa', 'fk_tipo_doc')
    return render(request, 'necessidade_lista.html', {
        'necessidades': necessidades
    })

@login_required
def necessidade_form(request, id_necessidade=None):
    if id_necessidade:
        necessidade = get_object_or_404(NecessidadeDocumento, id_necessidade=id_necessidade)
    else:
        necessidade = None

    if request.method == 'POST':
        fk_empresa_id = request.POST.get('empresa')
        fk_tipo_doc_id = request.POST.get('tipo_doc')
        
        if fk_empresa_id and fk_tipo_doc_id:
            if necessidade:
                necessidade.fk_empresa_id = fk_empresa_id
                necessidade.fk_tipo_doc_id = fk_tipo_doc_id
                necessidade.save()
                messages.success(request, 'Necessidade atualizada com sucesso!')
            else:
                NecessidadeDocumento.objects.create(
                    fk_empresa_id=fk_empresa_id,
                    fk_tipo_doc_id=fk_tipo_doc_id
                )
                messages.success(request, 'Necessidade cadastrada com sucesso!')
            return redirect('necessidade_lista')
        else:
            messages.error(request, 'Preencha todos os campos.')

    empresas = Empresa.objects.all().order_by('nome')
    # Documentos não obrigatórios
    tipos_doc = TipoDocumento.objects.filter(obrigatorio=False).order_by('nome')
    
    return render(request, 'necessidade_form.html', {
        'necessidade': necessidade,
        'empresas': empresas,
        'tipos_doc': tipos_doc
    })

@login_required
def necessidade_excluir(request, id_necessidade):
    necessidade = get_object_or_404(NecessidadeDocumento, id_necessidade=id_necessidade)
    necessidade.delete()
    messages.success(request, 'Necessidade excluída com sucesso!')
    return redirect('necessidade_lista')

@login_required
def entrega_lista(request):
    entregas = EntregaDocumento.objects.all().select_related('fk_empresa', 'fk_tipo_doc', 'fk_resp_tecnico_entrega').order_by('-data_entrega')
    return render(request, 'entrega_lista.html', {
        'entregas': entregas
    })

@login_required
def entrega_form(request, id_entrega=None):
    if id_entrega:
        entrega = get_object_or_404(EntregaDocumento, id_entrega=id_entrega)
    else:
        entrega = None

    if request.method == 'POST':
        fk_empresa_id = request.POST.get('empresa')
        fk_tipo_doc_id = request.POST.get('tipo_doc')
        data_entrega = request.POST.get('data_entrega')
        arquivo = request.FILES.get('arquivo')
        
        if fk_empresa_id and fk_tipo_doc_id and data_entrega:
            empresa_selecionada = get_object_or_404(Empresa, id_empresa=fk_empresa_id)
            if not empresa_selecionada.fk_resp_tecnico_atual:
                messages.error(request, 'A empresa selecionada não possui um Responsável Técnico vinculado. Cadastre ou vincule um responsável à empresa antes de registrar entregas.')
            else:
                fk_resp_tecnico_id = empresa_selecionada.fk_resp_tecnico_atual.id_resp_tecnico
                if entrega:
                    entrega.fk_empresa_id = fk_empresa_id
                    entrega.fk_tipo_doc_id = fk_tipo_doc_id
                    entrega.fk_resp_tecnico_entrega_id = fk_resp_tecnico_id
                    entrega.data_entrega = data_entrega
                    if arquivo:
                        entrega.arquivo = arquivo
                    entrega.save()
                    messages.success(request, 'Entrega atualizada com sucesso!')
                else:
                    EntregaDocumento.objects.create(
                        fk_empresa_id=fk_empresa_id,
                        fk_tipo_doc_id=fk_tipo_doc_id,
                        fk_resp_tecnico_entrega_id=fk_resp_tecnico_id,
                        data_entrega=data_entrega,
                        arquivo=arquivo
                    )
                    messages.success(request, 'Entrega registrada com sucesso!')
                return redirect('entrega_lista')
        else:
            messages.error(request, 'Preencha todos os campos.')

    empresas = Empresa.objects.all().order_by('nome')
    tipos_doc = TipoDocumento.objects.all().order_by('nome')
    
    return render(request, 'entrega_form.html', {
        'entrega': entrega,
        'empresas': empresas,
        'tipos_doc': tipos_doc
    })

@login_required
def entrega_excluir(request, id_entrega):
    entrega = get_object_or_404(EntregaDocumento, id_entrega=id_entrega)
    entrega.delete()
    messages.success(request, 'Entrega excluída com sucesso!')
    return redirect('entrega_lista')
