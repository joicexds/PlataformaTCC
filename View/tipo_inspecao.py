from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from Model.base import TipoInspecao

@login_required
def tipo_inspecao_index(request):
    tipos = TipoInspecao.objects.all().order_by('nome')
    return render(request, 'tipo_inspecao_index.html', {'tipos': tipos})

@login_required
def tipo_inspecao_form(request, id_tipo_inspecao=None):
    if id_tipo_inspecao:
        tipo = get_object_or_404(TipoInspecao, id_tipo_inspecao=id_tipo_inspecao)
    else:
        tipo = None

    if request.method == 'POST':
        nome = request.POST.get('nome')
        
        if nome:
            exists = TipoInspecao.objects.filter(nome__iexact=nome)
            if tipo:
                exists = exists.exclude(id_tipo_inspecao=tipo.id_tipo_inspecao)
            
            if exists.exists():
                messages.error(request, f'Já existe um Tipo de Inspeção com o nome "{nome}".')
                return redirect('tipo_inspecao_index')

            if tipo:
                tipo.nome = nome
                tipo.save()
                messages.success(request, 'Tipo de Inspeção atualizado com sucesso!')
            else:
                TipoInspecao.objects.create(nome=nome)
                messages.success(request, 'Tipo de Inspeção cadastrado com sucesso!')
            return redirect('tipo_inspecao_index')
        else:
            messages.error(request, 'Preencha o nome do tipo de inspeção.')

    return render(request, 'tipo_inspecao_index.html', {
        'tipo_edit': tipo,
        'tipos': TipoInspecao.objects.all().order_by('nome')
    })

@login_required
def tipo_inspecao_excluir(request, id_tipo_inspecao):
    tipo = get_object_or_404(TipoInspecao, id_tipo_inspecao=id_tipo_inspecao)
    try:
        tipo.delete()
        messages.success(request, 'Tipo de Inspeção excluído com sucesso!')
    except Exception as e:
        messages.error(request, f'Não é possível excluir este tipo pois ele está em uso. ({e})')
    return redirect('tipo_inspecao_index')
