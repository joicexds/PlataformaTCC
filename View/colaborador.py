from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from Model.base import Colaborador, Empresa
import datetime

@login_required
def colaborador_lista(request):
    colaboradores = Colaborador.objects.all().order_by('nome')
    hoje = datetime.date.today()
    for colab in colaboradores:
        delta = hoje - colab.data_entrada
        colab.tempo_empresa_anos = delta.days // 365
        colab.tempo_empresa_meses = (delta.days % 365) // 30
        
        dias_para_vencer = 365 - delta.days
        if dias_para_vencer <= 0:
            colab.status_vencimento = 'vencido'
        elif dias_para_vencer <= 30:
            colab.status_vencimento = 'alerta'
        else:
            colab.status_vencimento = 'ok'
            
    return render(request, 'colaborador_lista.html', {'colaboradores': colaboradores})

@login_required
def colaborador_form(request, id_colab=None):
    if id_colab:
        colaborador = get_object_or_404(Colaborador, id_colaborador=id_colab)
    else:
        colaborador = None

    if request.method == 'POST':
        erro = False
        nome = request.POST.get('nome')
        cpf_raw = request.POST.get('cpf')
        fk_empresa_id = request.POST.get('empresa')
        data_entrada = request.POST.get('data_entrada')
        ativo = request.POST.get('ativo') == 'on'

        if cpf_raw == '***.***.***-**' and colaborador:
            cpf = colaborador.cpf
        else:
            cpf = ''.join(filter(str.isdigit, cpf_raw)) if cpf_raw else ''

        if not fk_empresa_id or not nome or not cpf or not data_entrada:
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
            erro = True
        else:
            todos_colaboradores = Colaborador.objects.all()
            exists = any(c.cpf == cpf and (not colaborador or c.id_colaborador != colaborador.id_colaborador) for c in todos_colaboradores)
                
            if exists:
                messages.error(request, 'Este CPF já está cadastrado no sistema para outro colaborador.')
                erro = True
            else:
                if colaborador:
                    colaborador.nome = nome
                    colaborador.cpf = cpf
                    colaborador.fk_empresa_id = fk_empresa_id
                    colaborador.data_entrada = data_entrada
                    colaborador.ativo = ativo
                    colaborador.save()
                    messages.success(request, 'Colaborador atualizado com sucesso!')
                else:
                    Colaborador.objects.create(
                        nome=nome,
                        cpf=cpf,
                        fk_empresa_id=fk_empresa_id,
                        data_entrada=data_entrada,
                        ativo=ativo
                    )
                    messages.success(request, 'Novo colaborador cadastrado com sucesso!')
                
                return redirect('colaborador_lista')

        if erro:
            if not colaborador:
                class DummyColab: pass
                colaborador = DummyColab()
            colaborador.nome = nome
            colaborador.cpf = cpf_raw
            colaborador.fk_empresa_id = int(fk_empresa_id) if fk_empresa_id else None
            colaborador.data_entrada = data_entrada
            colaborador.ativo = ativo



    empresas = Empresa.objects.all().order_by('nome')
    return render(request, 'colaborador_form.html', {
        'colaborador': colaborador,
        'empresas': empresas
    })

@login_required
def colaborador_excluir(request, id_colab):
    colaborador = get_object_or_404(Colaborador, id_colaborador=id_colab)
    nome = colaborador.nome
    colaborador.delete()
    messages.success(request, f'Colaborador {nome} removido.')
    return redirect('colaborador_lista')
