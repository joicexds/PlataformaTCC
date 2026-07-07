from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from Model.base import Visita, Empresa, ResponsavelTecnico, TipoInspecao
from django.utils import timezone

@login_required
def inspecao_lista(request):
    inspecoes = Visita.objects.all().order_by('-data_evento')
    return render(request, 'inspecao_lista.html', {'inspecoes': inspecoes})

@login_required
def inspecao_form(request, id_inspecao=None):
    if id_inspecao:
        inspecao = get_object_or_404(Visita, id_visita=id_inspecao)
    else:
        inspecao = None

    if request.method == 'POST':
        fk_empresa_id = request.POST.get('empresa')
        fk_resp_id = request.POST.get('responsavel')
        fk_categoria_id = request.POST.get('categoria')
        data_evento = request.POST.get('data') or timezone.now().date()
        observacao = request.POST.get('observacao')
        anexo = request.FILES.get('anexo')

        if not fk_empresa_id or not fk_resp_id or not fk_categoria_id:
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios (Empresa, Responsável e Categoria).')
            return redirect('inspecao_nova')

        if inspecao:
            inspecao.fk_empresa_id = fk_empresa_id
            inspecao.fk_resp_tecnico_historico_id = fk_resp_id
            inspecao.fk_tipo_inspecao_id = fk_categoria_id
            inspecao.data_evento = data_evento
            inspecao.observacao = observacao
            if anexo:
                inspecao.anexo = anexo
            inspecao.save()
            messages.success(request, 'Inspeção atualizada com sucesso!')
        else:
            Visita.objects.create(
                fk_empresa_id=fk_empresa_id,
                fk_resp_tecnico_historico_id=fk_resp_id,
                fk_tipo_inspecao_id=fk_categoria_id,
                data_evento=data_evento,
                observacao=observacao,
                anexo=anexo
            )
            messages.success(request, 'Nova inspeção registrada com sucesso!')
        
        return redirect('home')

    import json
    empresas = Empresa.objects.all().order_by('nome')
    responsaveis = ResponsavelTecnico.objects.all().order_by('nome')
    categorias = TipoInspecao.objects.all()
    
    empresa_resp_map = {emp.id_empresa: emp.fk_resp_tecnico_atual_id for emp in empresas if emp.fk_resp_tecnico_atual_id}

    return render(request, 'inspecao_form.html', {
        'inspecao': inspecao,
        'empresas': empresas,
        'responsaveis': responsaveis,
        'categorias': categorias,
        'empresa_resp_map': json.dumps(empresa_resp_map)
    })

@login_required
def emitir_inspecao(request):
    empresas = Empresa.objects.all().order_by('nome')
    inspecoes = None
    empresa_selecionada = None

    empresa_id = request.GET.get('empresa')
    if empresa_id:
        empresa_selecionada = get_object_or_404(Empresa, id_empresa=empresa_id)
        inspecoes = Visita.objects.filter(fk_empresa_id=empresa_id).order_by('-data_evento')
    
    return render(request, 'emitir_inspecao.html', {
        'empresas': empresas,
        'inspecoes': inspecoes,
        'empresa_selecionada': empresa_selecionada
    })
