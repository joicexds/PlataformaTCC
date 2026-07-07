from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from Model.base import TipoDocumento

@login_required
def tipo_documento_index(request, id_tipo=None):
    if id_tipo:
        tipo = get_object_or_404(TipoDocumento, id_tipo_doc=id_tipo)
    else:
        tipo = None

    if request.method == 'POST':
        nome = request.POST.get('nome')
        prazo = request.POST.get('prazo_validade_meses')
        obrigatorio = request.POST.get('obrigatorio') == 'on'

        exists = TipoDocumento.objects.filter(nome__iexact=nome)
        if tipo:
            exists = exists.exclude(id_tipo_doc=tipo.id_tipo_doc)
        
        if exists.exists():
            messages.error(request, f'Já existe um Tipo de Documento com o nome "{nome}".')
            return redirect('tipo_documento_index')

        if tipo:
            tipo.nome = nome
            tipo.prazo_validade_meses = prazo
            tipo.obrigatorio = obrigatorio
            tipo.save()
            messages.success(request, f'Tipo de documento "{nome}" atualizado com sucesso!')
        else:
            TipoDocumento.objects.create(
                nome=nome,
                prazo_validade_meses=prazo,
                obrigatorio=obrigatorio
            )
            messages.success(request, f'Tipo de documento "{nome}" cadastrado com sucesso!')
        
        return redirect('tipo_documento_index')

    tipos = TipoDocumento.objects.all()
    return render(request, 'tipo_documento_index.html', {
        'tipo': tipo,
        'tipos': tipos
    })

@login_required
def tipo_documento_excluir(request, id_tipo):
    tipo = get_object_or_404(TipoDocumento, id_tipo_doc=id_tipo)
    nome = tipo.nome
    try:
        tipo.delete()
        messages.success(request, f'Tipo de documento "{nome}" excluído com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir: {str(e)}')
    return redirect('tipo_documento_index')
