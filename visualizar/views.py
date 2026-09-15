from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from .forms import RegisterForm

@staff_member_required
def list_users(request):
    """Admin view that lists all usernames for debugging."""
    users = User.objects.all().values('username', 'first_name', 'last_name')
    return render(request, 'list_users.html', {'users': users})

@login_required
def home(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    # Generic streak update just in case they just open this page
    complete_mission(request.user, None, 0)
    
    completed_missions = set(UserMission.objects.filter(user=request.user).values_list('mission_code', flat=True))
    
    next_level_xp = profile.level * 1000
    xp_in_level = profile.total_xp % 1000
    xp_percent = int((xp_in_level / 1000) * 100)
    
    # Etapas
    etapas = [
        {'id': 1, 'code': 'profile_completed', 'title': 'Introdução'},
        {'id': 2, 'code': 'test_vocational', 'title': 'Competências'},
        {'id': 3, 'code': 'watched_youtube_video', 'title': 'Áreas de Interesse'},
        {'id': 4, 'code': 'future_mission_1', 'title': 'Valores Pessoais'},
        {'id': 5, 'code': 'future_mission_2', 'title': 'Resultado Final'}
    ]
    
    etapas_completas = 0
    for etapa in etapas:
        if etapa['code'] in completed_missions:
            etapa['status'] = 'completed'
            etapas_completas += 1
        elif etapa['id'] == etapas_completas + 1:
            etapa['status'] = 'active'
        else:
            etapa['status'] = 'locked'
            
    # Missões Recentes
    missoes_recentes = [
        {'title': 'O Despertar (Perfil)', 'status': 'completed' if 'profile_completed' in completed_missions else 'active', 'xp': 500, 'icon': 'user', 'url': 'profile', 'progress': 100 if 'profile_completed' in completed_missions else 0},
        {'title': 'Teste Vocacional', 'status': 'completed' if 'test_vocational' in completed_missions else 'active', 'xp': 1000, 'icon': 'award', 'url': 'iniciar_teste', 'progress': 100 if 'test_vocational' in completed_missions else 0},
        {'title': 'Visão do Futuro (IA)', 'status': 'completed' if 'watched_youtube_video' in completed_missions else 'active', 'xp': 200, 'icon': 'play-circle', 'url': 'explorar_profissoes', 'progress': 100 if 'watched_youtube_video' in completed_missions else 0},
        {'title': 'Voz da Comunidade (Feedback)', 'status': 'completed' if 'feedback_completed' in completed_missions else 'active', 'xp': 300, 'icon': 'message-square', 'url': 'feedback', 'progress': 100 if 'feedback_completed' in completed_missions else 0},
    ]
    
    context = {
        'profile': profile,
        'xp_percent': xp_percent,
        'etapas': etapas,
        'etapas_completas': etapas_completas,
        'missoes_recentes': missoes_recentes
    }
    
    return render(request, 'home.html', context)

class CustomLoginView(LoginView):
    template_name = 'login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Log the user in using the explicit ModelBackend.
        This avoids the "multiple authentication backends" ValueError.
        """
        from django.contrib.auth import login as auth_login
        user = form.get_user()
        auth_login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect(self.get_success_url())

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after registration
            from django.contrib.auth import login as auth_login
            # Specify backend explicitly because multiple auth backends are configured
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required
def explorar_profissoes(request):
    return render(request, 'explorar_profissoes.html')


from .models import UserProfile, UserMission, Feedback
from .forms import UserProfileForm
from django.utils import timezone

def complete_mission(user, mission_code, xp_reward):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    today = timezone.now().date()
    if profile.last_activity_date != today:
        if profile.last_activity_date == today - timezone.timedelta(days=1):
            profile.streak_days += 1
        elif profile.last_activity_date is None or profile.last_activity_date < today - timezone.timedelta(days=1):
            profile.streak_days = 1
        profile.last_activity_date = today
        profile.save()
        
    if mission_code:
        mission, created = UserMission.objects.get_or_create(user=user, mission_code=mission_code)
        if created and xp_reward > 0:
            profile.add_xp(xp_reward)
            return True
    
    # Just update streak if it's a generic action or already completed
    if xp_reward == 0:
        profile.save()
    return False

@login_required
def profile(request):
    profile_instance, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile_instance, user=request.user)
        if form.is_valid():
            # Update User fields
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.username = form.cleaned_data['email']
            user.save()
            
            # Save Profile
            form.save()
            complete_mission(request.user, 'profile_completed', 500)
            return redirect('profile')
    else:
        # Render registration form if GET
        form = RegisterForm()
        return render(request, 'register.html', {'form': form})
        form = UserProfileForm(instance=profile_instance, user=request.user)
        
    return render(request, 'profile.html', {'form': form, 'profile': profile_instance})


try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
import json
import random
from django.conf import settings

BACKUP_TEST = {
    "perguntas": [
        {
            "id": 1,
            "enunciado": "O que você mais curte fazer no seu tempo livre?",
            "image_prompt": "young friends having pleasant conversation coffee books culture",
            "alternativas": [
                {"letra": "A", "texto": "Ir a um café ou centro cultural com amigos para conversar, debater ideias, ler um livro ou assistir a uma peça/filme.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Organizar minhas metas e finanças pessoais, explorar ferramentas digitais, jogar jogos de estratégia/lógica ou montar algo técnico.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Praticar atividade física, preparar uma refeição nutritiva para quem eu gosto e cuidar do descanso e bem-estar do corpo e mente.", "categoria": "Saude"},
                {"letra": "D", "texto": "Fazer uma trilha ou caminhada ao ar livre, passear em um parque arborizado, cuidar de plantas ou passar tempo com animais.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 2,
            "enunciado": "Você e seus amigos estão planejando uma viagem de férias e precisam dividir as tarefas. Qual papel você assume naturalmente?",
            "image_prompt": "friends planning travel with map and notebook smiling",
            "alternativas": [
                {"letra": "A", "texto": "Alinhar o roteiro com o grupo, mediar diferentes vontades e garantir que todos se sintam incluídos, motivados e confortáveis.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Montar a planilha de custos, comparar orçamentos de hospedagem e transporte e calcular a divisão exata dos gastos de cada um.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Montar o kit de primeiros socorros, checar condições de higiene e segurança dos locais e planejar pausas para descanso e refeições saudáveis.", "categoria": "Saude"},
                {"letra": "D", "texto": "Pesquisar passeios em contato com o meio ambiente, trilhas ecológicas, praias preservadas e opções sustentáveis de turismo.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 3,
            "enunciado": "Ao realizar um trabalho em equipe (na escola, faculdade ou comunidade), em qual parte você sente que contribui melhor?",
            "image_prompt": "team brainstorming around desk collaborative project",
            "alternativas": [
                {"letra": "A", "texto": "Redigir a apresentação, criar uma narrativa envolvente e defender oralmente a ideia com clareza e empatia.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Estruturar a parte técnica, organizar os dados numéricos, criar gráficos e garantir a coerência lógica e funcional do projeto.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Avaliar o impacto prático na rotina e no bem-estar das pessoas envolvidas, reduzindo estresse e sobrecarga dos participantes.", "categoria": "Saude"},
                {"letra": "D", "texto": "Garantir a responsabilidade socioambiental, escolha de materiais sustentáveis e o respeito aos recursos naturais locais.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 4,
            "enunciado": "Navegando pelas redes sociais ou sites de notícias no dia a dia, qual destas manchetes desperta sua curiosidade imediata?",
            "image_prompt": "person reading interesting news on digital device casual",
            "alternativas": [
                {"letra": "A", "texto": "'Estudo revela mudanças históricas nas relações sociais, na cultura e na comunicação entre novas gerações.'", "categoria": "Humanas"},
                {"letra": "B", "texto": "'Novo avanço tecnológico utiliza inteligência artificial e algoritmos para otimizar cálculos e processos complexos.'", "categoria": "Exatas"},
                {"letra": "C", "texto": "'Pesquisa descobre novos hábitos alimentares e rotinas diárias que aumentam a longevidade e a imunidade.'", "categoria": "Saude"},
                {"letra": "D", "texto": "'Expedição documenta recuperação de espécies da fauna e flora nativa através de técnicas ecológicas inovadoras.'", "categoria": "Natureza"}
            ]
        },
        {
            "id": 5,
            "enunciado": "Um amigo muito próximo procura você em um dia difícil, visivelmente chateado e desabafando. Qual é o seu primeiro instinto?",
            "image_prompt": "two friends sitting together talking supportive empathy",
            "alternativas": [
                {"letra": "A", "texto": "Escutar atentamente com acolhimento e sem julgamentos, validando o que ele sente e oferecendo apoio emocional e conselhos sinceros.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Ajudá-lo a analisar friamente a situação, identificar a causa-raiz do problema e desenhar um plano de ação objetivo para resolver.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Ajudá-lo a relaxar o corpo, sugerir que ele durma bem, se alimente direito e ver se ele precisa de algo para aliviar a tensão física.", "categoria": "Saude"},
                {"letra": "D", "texto": "Convidá-lo para sair de casa, respirar ar puro em um parque ou dar uma volta com o pet para clarear os pensamentos em contato com o ar livre.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 6,
            "enunciado": "Se você decidisse transformar completamente o seu quarto ou espaço de estudos, o que seria prioritário para você?",
            "image_prompt": "cozy modern organized study room inspiring",
            "alternativas": [
                {"letra": "A", "texto": "A harmonia estética, as cores das paredes, quadros com frases ou artes que expressem minha identidade e estilo de vida.", "categoria": "Humanas"},
                {"letra": "B", "texto": "A funcionalidade e medidas exatas: organizar prateleiras por categorias, otimizar fios, cabos e calcular o orçamento milimétrico.", "categoria": "Exatas"},
                {"letra": "C", "texto": "A ergonomia da mesa e cadeira, iluminação adequada para a visão, ventilação correta e conforto térmico para prevenir fadiga.", "categoria": "Saude"},
                {"letra": "D", "texto": "A integração com elementos naturais: plantas em vasos, luz natural direta, ventilação cruzada e móveis de madeira de reflorestamento.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 7,
            "enunciado": "Se você ganhasse uma bolsa de estudos para um curso livre de curta duração para fazer no próximo mês, qual escolheria?",
            "image_prompt": "online learning workshop young adult focused",
            "alternativas": [
                {"letra": "A", "texto": "Oratória, Escrita Criativa, Mediação de Conflitos ou Psicologia das Relações Interpessoais.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Lógica de Programação, Educação Financeira e Investimentos ou Análise de Dados.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Noções de Primeiros Socorros, Nutrição Prática no Cotidiano ou Anatomia e Fisiologia do Exercício.", "categoria": "Saude"},
                {"letra": "D", "texto": "Cultivo de Hortas Urbanas, Manejo e Comportamento Animal ou Gestão de Resíduos e Sustentabilidade.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 8,
            "enunciado": "Durante uma reunião ou evento de família/amigos, ocorre um imprevisto prático que paralisa tudo. Como você reage?",
            "image_prompt": "gathering of people solving a sudden practical problem",
            "alternativas": [
                {"letra": "A", "texto": "Tomo a frente para manter o bom humor e o ânimo de todos, comunicando as informações para que ninguém fique ansioso ou confuso.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Avalio o mecanismo ou equipamento com defeito, analiso conexões lógicas e busco testar alternativas metódicas para consertar.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Checo se todos estão em segurança, garanto água e suprimentos essenciais e cuido para que idosos ou crianças fiquem tranquilos.", "categoria": "Saude"},
                {"letra": "D", "texto": "Avalio como aproveitar o ambiente externo, evitar desperdício de recursos e propor alternativas simples em harmonia com o espaço.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 9,
            "enunciado": "Se você pudesse dedicar duas horas semanais a uma iniciativa social voluntária no seu bairro, onde você mais gostaria de colaborar?",
            "image_prompt": "volunteers working together in community action outdoors",
            "alternativas": [
                {"letra": "A", "texto": "Aulas de reforço escolar, oficinas de leitura, teatro ou orientação de direitos dos cidadãos.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Apoio a pequenos empreendedores com planilhas, controle de caixa ou aulas básicas de computação e lógica.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Ações de saúde comunitária, caminhadas orientadas para idosos e campanhas de prevenção de doenças e vacinação.", "categoria": "Saude"},
                {"letra": "D", "texto": "Mutirões de plantio de árvores, recuperação de praças e hortas comunitárias ou cuidado e adoção de animais resgatados.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 10,
            "enunciado": "Quando você precisa escolher um podcast ou vídeo longo no YouTube para ouvir enquanto faz suas tarefas diárias, qual é o tema preferido?",
            "image_prompt": "young person listening to podcast with headphones relaxing",
            "alternativas": [
                {"letra": "A", "texto": "Histórias de vida reais, debates sobre comportamento da sociedade, filosofia de vida, cinema e literatura.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Tendências de inovação, inteligência artificial, física aplicada, economia ou desmontagem de mecanismos complexos.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Conversas com médicos e especialistas sobre sono, qualidade de vida, neurociência do estresse e hábitos saudáveis.", "categoria": "Saude"},
                {"letra": "D", "texto": "Expedições na vida selvagem, comportamento de animais exóticos, documentários ecológicos e preservação do planeta.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 11,
            "enunciado": "Ao planejar a compra de algo de maior valor (como um celular, notebook ou curso), qual é o seu critério decisivo?",
            "image_prompt": "person comparing products thoughtfully at desk",
            "alternativas": [
                {"letra": "A", "texto": "A reputação ética da marca, os valores que a empresa transmite e a indicação de pessoas que confio e admiro.", "categoria": "Humanas"},
                {"letra": "B", "texto": "O comparativo detalhado de especificações técnicas, custo-benefício por centavo, dados de benchmarks e durabilidade calculada.", "categoria": "Exatas"},
                {"letra": "C", "texto": "O impacto no meu dia a dia de forma saudável: ergonomia do produto, menor cansaço visual e preservação da minha saúde postural.", "categoria": "Saude"},
                {"letra": "D", "texto": "A pegada ecológica: se os materiais são recicláveis, se a empresa tem selo verde de sustentabilidade e menor impacto ambiental.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 12,
            "enunciado": "Em uma feira cultural ou de profissões, em qual estande você passaria mais tempo conversando com as pessoas?",
            "image_prompt": "students exploring education careers fair dynamic booth",
            "alternativas": [
                {"letra": "A", "texto": "No estande de Direitos Humanos, Jornalismo, Ciências Sociais, Psicologia ou Artes e Comunicação.", "categoria": "Humanas"},
                {"letra": "B", "texto": "No estande de Ciência da Computação, Engenharia, Análise Financeira, Estatística ou Robótica.", "categoria": "Exatas"},
                {"letra": "C", "texto": "No estande de Medicina, Enfermagem, Nutrição, Fisioterapia ou Biomedicina.", "categoria": "Saude"},
                {"letra": "D", "texto": "No estande de Engenharia Ambiental, Medicina Veterinária, Agronomia, Biologia ou Gestão Ecológica.", "categoria": "Natureza"}
            ]
        }
    ]
}

def extract_preference_scores(prefs):
    """
    Mapeia com precisão as preferências iniciais do usuário para pontos de afinidade vocacional.
    Evita qualquer viés forçado para Exatas.
    """
    scores = {'Humanas': 0.0, 'Exatas': 0.0, 'Saude': 0.0, 'Natureza': 0.0}
    
    materia = (prefs.get('materia') or '').lower()
    hobby = (prefs.get('hobby') or '').lower()
    habilidade = (prefs.get('habilidade') or '').lower()
    objetivo = (prefs.get('objetivo') or '').lower()
    
    # 1. Matéria de afinidade
    if 'exatas' in materia or 'matemática' in materia or 'física' in materia or 'cálculos' in materia:
        scores['Exatas'] += 1.5
    elif 'biológicas' in materia or 'vida' in materia:
        scores['Saude'] += 1.2
        scores['Natureza'] += 0.8
    elif 'humanas' in materia or 'história' in materia or 'filosofia' in materia or 'sociedade' in materia:
        scores['Humanas'] += 1.5
    elif 'linguagens' in materia or 'literatura' in materia or 'idiomas' in materia or 'artes' in materia or 'design' in materia:
        scores['Humanas'] += 1.5
    elif 'negócios' in materia or 'administração' in materia or 'economia' in materia:
        scores['Humanas'] += 0.8
        scores['Exatas'] += 0.8
        
    # 2. Atividade de tempo livre (Hobby)
    if 'lógica' in hobby or 'estratégia' in hobby or 'codar' in hobby or 'enigmas' in hobby:
        scores['Exatas'] += 1.5
    elif 'leitura' in hobby or 'documentários' in hobby or 'estudo contínuo' in hobby:
        scores['Humanas'] += 1.2
    elif 'prática física' in hobby or 'esportes' in hobby:
        scores['Saude'] += 1.2
    elif 'natureza' in hobby or 'externos' in hobby or 'reservas' in hobby:
        scores['Natureza'] += 1.5
    elif 'construção criativa' in hobby or 'audiovisual' in hobby or 'desenho' in hobby:
        scores['Humanas'] += 1.2
    elif 'socialização' in hobby or 'conversas' in hobby or 'voluntárias' in hobby:
        scores['Humanas'] += 1.2
        scores['Saude'] += 0.5
        
    # 3. Habilidade preponderante
    if 'analítica' in habilidade or 'lógica' in habilidade or 'algorítmica' in habilidade:
        scores['Exatas'] += 1.5
    elif 'empatia' in habilidade or 'comportamental' in habilidade:
        scores['Humanas'] += 1.2
        scores['Saude'] += 0.8
    elif 'oratória' in habilidade or 'persuasão' in habilidade or 'comunicação' in habilidade:
        scores['Humanas'] += 1.5
    elif 'meticulosidade' in habilidade or 'precisão' in habilidade:
        scores['Exatas'] += 0.8
        scores['Saude'] += 0.5
    elif 'liderança' in habilidade or 'coordenar' in habilidade:
        scores['Humanas'] += 1.2
        scores['Exatas'] += 0.5

    # 4. Objetivo e Propósito de vida
    if 'inovação' in objetivo or 'tecnológica' in objetivo or 'automatizar' in objetivo or 'ai' in objetivo:
        scores['Exatas'] += 1.5
    elif 'saúde' in objetivo or 'medicinal' in objetivo or 'bem-estar humano' in objetivo or 'mortalidade' in objetivo:
        scores['Saude'] += 2.0
    elif 'equidade' in objetivo or 'justiça' in objetivo or 'social' in objetivo or 'leis' in objetivo:
        scores['Humanas'] += 2.0
    elif 'crescimento financeiro' in objetivo or 'mercado' in objetivo or 'corporações' in objetivo:
        scores['Exatas'] += 1.0
        scores['Humanas'] += 1.0
    elif 'conservação' in objetivo or 'resgate botânico' in objetivo or 'biodiversidade' in objetivo or 'oceanos' in objetivo:
        scores['Natureza'] += 2.0
        
    return scores

def calculate_vocational_diagnosis(category_counts, user_prefs):
    """
    Calcula com precisão o perfil vencedor e as porcentagens de cada uma das 4 áreas.
    Dá peso de 3 pontos para cada resposta direta no teste situacional e peso de 1 ponto
    para afinidades expressas nas características iniciais do usuário.
    """
    final_scores = {'Humanas': 0.0, 'Exatas': 0.0, 'Saude': 0.0, 'Natureza': 0.0}
    
    # 1. Pontos das perguntas respondidas (Peso maior: 3.0 por pergunta)
    for cat, count in category_counts.items():
        if cat in final_scores:
            final_scores[cat] += count * 3.0
            
    # 2. Pontos das características do usuário
    pref_scores = extract_preference_scores(user_prefs)
    for cat, p_score in pref_scores.items():
        final_scores[cat] += p_score
        
    total_points = sum(final_scores.values())
    if total_points == 0:
        # Fallback equilibrado se não houver dados
        total_points = 1.0
        final_scores = {'Humanas': 0.25, 'Exatas': 0.25, 'Saude': 0.25, 'Natureza': 0.25}

    # Ordenar áreas da maior para a menor pontuação
    sorted_areas = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    winner = sorted_areas[0][0]
    secondary_winner = sorted_areas[1][0] if len(sorted_areas) > 1 else winner
    
    # Calcular percentuais inteiros normalizados
    percentages = {}
    for cat, pts in final_scores.items():
        percentages[cat] = int(round((pts / total_points) * 100))
        
    # Ajustar para somar 100% exatamente
    diff = 100 - sum(percentages.values())
    if diff != 0:
        percentages[winner] += diff
        
    return winner, secondary_winner, percentages, final_scores

@login_required
def iniciar_teste(request):
    if request.method == 'POST':
        materia = request.POST.get('materia', '')
        hobby = request.POST.get('hobby', '')
        habilidade = request.POST.get('habilidade', '')
        objetivo = request.POST.get('objetivo', '')
        
        # Save to session for personalized result later
        user_prefs = {
            'materia': materia,
            'hobby': hobby,
            'habilidade': habilidade,
            'objetivo': objetivo
        }
        request.session['user_preferences'] = user_prefs
        
        # Call Gemini if API Key is configured
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        questions_data = None
        
        if HAS_GEMINI and api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 0.7})
                prompt = f"""
                Você é um psicólogo e orientador vocacional experiente.
                O usuário respondeu às seguintes características e interesses pessoais:
                - Área de estudo que tem afinidade: {materia}
                - Atividade de tempo livre que mais gosta: {hobby}
                - Habilidade que executa com facilidade: {habilidade}
                - Objetivo e propósito de carreira: {objetivo}

                SUA TAREFA:
                Gere exatamente 5 perguntas situacionais realistas sobre o DIA A DIA PRÁTICO (estudos, lazer, amizades, resolução de problemas cotidianos, trabalhos em grupo ou eventos).
                
                REGRAS FUNDAMENTAIS:
                1. NÃO crie cenários de ficção científica, naves espaciais, invasões ou apocalipse. Foque no mundo real e no cotidiano de jovens e estudantes.
                2. Cada pergunta deve descrever uma situação comum (ex: resolver um conflito entre amigos, planejar uma viagem de fim de semana, organizar um projeto comunitário, ajudar alguém que está passando por um momento difícil, reagir a um imprevisto prático).
                3. Cada uma das 5 perguntas DEVE ter 4 alternativas (A, B, C, D) equilibradas, atraentes e correspondentes a:
                   - 'Humanas': Foco em comunicação, empatia, acolhimento de pessoas, artes, sociedade, debate e justiça.
                   - 'Exatas': Foco em raciocínio lógico, organização de métricas, finanças, dados e processos estruturados.
                   - 'Saude': Foco em bem-estar físico e mental, cuidados com o corpo, saúde preventiva e alívio do estresse.
                   - 'Natureza': Foco em meio ambiente, ecologia, contato com plantas, animais e sustentabilidade ao ar livre.
                4. Não favoreça nenhuma área específica nas formulações.

                Retorne ESTRITAMENTE em formato JSON, sem blocos markdown (sem ```json):
                {{
                  "perguntas": [
                    {{
                      "id": 1,
                      "enunciado": "Texto da pergunta situacional do dia a dia...",
                      "image_prompt": "prompt em inglês para ilustrar a situação cotidiana",
                      "alternativas": [
                        {{"letra": "A", "texto": "Ação com foco em comunicação e empatia humana.", "categoria": "Humanas"}},
                        {{"letra": "B", "texto": "Ação com foco em lógica, dados e estruturação.", "categoria": "Exatas"}},
                        {{"letra": "C", "texto": "Ação com foco em cuidado com o corpo e saúde.", "categoria": "Saude"}},
                        {{"letra": "D", "texto": "Ação com foco em sustentabilidade e vida natural.", "categoria": "Natureza"}}
                      ]
                    }}
                  ]
                }}
                """
                response = model.generate_content(prompt)
                text = response.text.replace("```json", "").replace("```", "").strip()
                questions_data = json.loads(text)
            except Exception as e:
                # Fallback to backup
                print("Gemini fallback due to:", e)
                questions_list = random.sample(BACKUP_TEST['perguntas'], 5)
                for i, q in enumerate(questions_list): q['id'] = i + 1
                questions_data = {'perguntas': questions_list}
        else:
            questions_list = random.sample(BACKUP_TEST['perguntas'], 5)
            for i, q in enumerate(questions_list): q['id'] = i + 1
            questions_data = {'perguntas': questions_list}
            
        request.session['vocational_test_questions'] = questions_data.get('perguntas')
        return redirect('responder_teste')
        
    return render(request, 'teste_iniciar.html')

@login_required
def responder_teste(request):
    questions = request.session.get('vocational_test_questions')
    if not questions:
        return redirect('iniciar_teste')
    return render(request, 'teste_responder.html', {'questions': questions})

@login_required
def resultado_teste(request):
    if request.method == 'POST':
        # Collect chosen options and categories
        user_answers = []
        category_counts = {}
        questions = request.session.get('vocational_test_questions', [])
        
        for key, value in request.POST.items():
            if key.startswith('pergunta_'):
                try:
                    q_id = int(key.split('_')[1])
                except ValueError:
                    continue
                category_counts[value] = category_counts.get(value, 0) + 1
                
                # Find the question text and chosen alternative text
                q_text = ""
                alt_text = ""
                for q in questions:
                    if q.get('id') == q_id:
                        q_text = q.get('enunciado', '')
                        for alt in q.get('alternativas', []):
                            if alt.get('categoria') == value:
                                alt_text = alt.get('texto', '')
                                break
                        break
                if q_text and alt_text:
                    user_answers.append({'pergunta': q_text, 'resposta': alt_text, 'categoria': value})

        # Calculate scores incorporating user preferences and answers without bias
        prefs = request.session.get('user_preferences', {})
        winner, secondary_winner, percentages, final_scores = calculate_vocational_diagnosis(category_counts, prefs)
        
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        resultado = None
        
        if HAS_GEMINI and api_key and user_answers:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 0.7})
                prompt = f"""
                Gere um resultado de teste vocacional altamente personalizado e acolhedor para um usuário cujo perfil predominante no teste foi a área de: {winner}.
                Sua segunda afinidade mais forte foi: {secondary_winner}.
                
                As respostas dele nas situações do dia a dia foram:
                {json.dumps(user_answers, ensure_ascii=False, indent=2)}
                
                E suas preferências e aspirações declaradas foram:
                - Matéria de afinidade: {prefs.get('materia', '')}
                - Atividade de tempo livre: {prefs.get('hobby', '')}
                - Habilidade principal: {prefs.get('habilidade', '')}
                - Objetivo de vida: {prefs.get('objetivo', '')}
                
                Crie um perfil vocacional envolvente, positivo e preciso, conectando o dia a dia dele com o mercado de trabalho.
                Retorne ESTRITAMENTE em formato JSON, sem marcações markdown:
                {{
                    "titulo": "Título criativo e inspirador do perfil (ex: Comunicador e Estrategista Humano)",
                    "descricao": "Uma descrição envolvente de até 3 linhas explicando por que as ações do dia a dia desse usuário indicam essa vocação.",
                    "carreiras": [
                        {{"nome": "Nome da Profissão", "salario": "R$ X.XXX", "icone": "icone lucide (ex: users, heart, leaf, code, briefcase, globe, book, smile, etc)"}},
                        {{"nome": "...", "salario": "...", "icone": "..."}},
                        {{"nome": "...", "salario": "...", "icone": "..."}},
                        {{"nome": "...", "salario": "...", "icone": "..."}}
                    ]
                }}
                """
                response = model.generate_content(prompt)
                text = response.text.replace("```json", "").replace("```", "").strip()
                resultado = json.loads(text)
            except Exception as e:
                resultado = None

        if not resultado:
            # Fallback Profiles mapping detalhado para cada uma das 4 áreas
            profiles = {
                'Humanas': {
                    'titulo': 'Pensador, Mediador e Comunicador de Humanas',
                    'descricao': 'Você possui forte sensibilidade interpessoal, apreço pela escuta atenta, comunicação clara e justiça social. Suas decisões no dia a dia valorizam o diálogo, a empatia e a convivência harmoniosa.',
                    'carreiras': [
                        {'nome': 'Psicologia', 'salario': 'R$ 4.800', 'icone': 'users'},
                        {'nome': 'Direito', 'salario': 'R$ 7.500', 'icone': 'scale'},
                        {'nome': 'Jornalismo e Comunicação', 'salario': 'R$ 4.500', 'icone': 'mic'},
                        {'nome': 'Pedagogia e Educação', 'salario': 'R$ 4.200', 'icone': 'book-open'}
                    ]
                },
                'Exatas': {
                    'titulo': 'Explorador da Lógica e Resolução Prática',
                    'descricao': 'Você se destaca pela clareza de raciocínio, método analítico e gosto por entender o funcionamento lógico das coisas. No cotidiano, busca soluções objetivas, processos eficientes e baseados em dados.',
                    'carreiras': [
                        {'nome': 'Engenharia de Software', 'salario': 'R$ 8.500', 'icone': 'code'},
                        {'nome': 'Ciência de Dados', 'salario': 'R$ 9.000', 'icone': 'database'},
                        {'nome': 'Engenharia Civil / Produção', 'salario': 'R$ 7.800', 'icone': 'settings'},
                        {'nome': 'Economia e Finanças', 'salario': 'R$ 6.800', 'icone': 'trending-up'}
                    ]
                },
                'Saude': {
                    'titulo': 'Protetor do Cuidado, Bem-Estar e Saúde',
                    'descricao': 'Seu foco espontâneo está no bem-estar físico e mental das pessoas ao seu redor. Você demonstra zelo genuíno, empatia diante de dificuldades e preocupação constante com hábitos saudáveis e acolhimento.',
                    'carreiras': [
                        {'nome': 'Medicina', 'salario': 'R$ 14.500', 'icone': 'heart'},
                        {'nome': 'Enfermagem', 'salario': 'R$ 5.800', 'icone': 'activity'},
                        {'nome': 'Fisioterapia', 'salario': 'R$ 4.500', 'icone': 'shield-plus'},
                        {'nome': 'Nutrição', 'salario': 'R$ 4.200', 'icone': 'apple'}
                    ]
                },
                'Natureza': {
                    'titulo': 'Cientista e Guardião da Natureza',
                    'descricao': 'Você tem profunda afinidade com o meio ambiente, com os animais, plantas e ecossistemas. Suas escolhas refletem consciência sustentável, gosto pelo ar livre e respeito pelas leis da biodiversidade.',
                    'carreiras': [
                        {'nome': 'Medicina Veterinária', 'salario': 'R$ 5.500', 'icone': 'dog'},
                        {'nome': 'Engenharia Ambiental', 'salario': 'R$ 7.200', 'icone': 'leaf'},
                        {'nome': 'Biotecnologia e Ciências Biológicas', 'salario': 'R$ 5.800', 'icone': 'flask-conical'},
                        {'nome': 'Agronomia e Agroecologia', 'salario': 'R$ 6.800', 'icone': 'sprout'}
                    ]
                }
            }
            resultado = profiles.get(winner, profiles['Humanas'])
            
        complete_mission(request.user, 'test_vocational', 1000)
        return render(request, 'teste_resultado.html', {
            'resultado': resultado,
            'winner': winner,
            'secondary_winner': secondary_winner,
            'percentages': percentages
        })
        
    return redirect('iniciar_teste')
import urllib.request
import urllib.parse
import re
import json

def search_youtube_video(query):
    query = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={query}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
        
        # Buscar no ytInitialData para pegar exatamente o primeiro vídeo de conteúdo e ignorar sugestões/ads
        match = re.search(r'var ytInitialData = (\{.*?\});</script>', html)
        if match:
            data = json.loads(match.group(1))
            try:
                contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
                for section in contents:
                    if 'itemSectionRenderer' in section:
                        items = section['itemSectionRenderer']['contents']
                        for item in items:
                            if 'videoRenderer' in item:
                                return item['videoRenderer']['videoId']
            except KeyError:
                pass
        
        # Fallback se a estrutura mudar
        video_ids = re.findall(r"watch\?v=(\S{11})", html)
        if video_ids:
            return video_ids[0]
    except Exception as e:
        print("Erro YouTube:", e)
    return None

@login_required
def detalhe_profissao(request, nome):
    # Base fallback structure
    dados = {
        'nome': nome.title(),
        'descricao': f'A profissão de {nome.title()} é fundamental para o desenvolvimento e funcionamento da sociedade atual. Os profissionais dessa área lidam com desafios dinâmicos e possuem um amplo campo de oportunidades.',
        'resumo_pratico': 'No dia a dia, este profissional resolve problemas práticos, analisa dados e atua diretamente na sua área de especialidade garantindo resultados eficientes.',
        'tempo_formacao': '4 a 5 anos',
        'niveis_atuacao': ['Júnior', 'Pleno', 'Sênior', 'Especialista'],
        'salario_medio': 'R$ 3.500 a R$ 12.000',
        'custo_curso': 'R$ 800 a R$ 2.500 / mês',
        'areas': [
            {'nome': 'Setor Privado', 'desc': 'Atuação em empresas nacionais e multinacionais em diversos cargos estratégicos.'},
            {'nome': 'Setor Público', 'desc': 'Concursos públicos e órgãos governamentais com estabilidade.'},
            {'nome': 'Autônomo / Empreendedor', 'desc': 'Trabalho independente, prestando consultorias ou abrindo a própria empresa.'}
        ]
    }

    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if HAS_GEMINI and api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 0.5})
            prompt = f"""
            Você é um especialista em carreiras e mercado de trabalho no Brasil. O usuário quer saber detalhes reais e extremamente precisos sobre a profissão: "{nome}".
            Por favor, pesquise os DADOS REAIS E ATUAIS (2025/2026) dessa profissão no Brasil. O foco é fornecer valores exatos de mensalidade de faculdades e tempo exato de duração dos cursos.
            Gere um retorno ESTRITAMENTE em formato JSON, sem marcações markdown:
            {{
                "nome": "Nome oficial da profissão formatado (ex: Engenharia de Software)",
                "descricao": "Uma descrição profissional e clara sobre a rotina dessa profissão (máx 4 linhas).",
                "resumo_pratico": "Como se fosse um 'shorts' ou tiktok bem dinâmico e simples, explique em 2 ou 3 parágrafos curtos O QUE ESTA PROFISSÃO FAZ NA PRÁTICA todos os dias, de uma forma muito fácil de entender para um leigo.",
                "tempo_formacao": "Duração exata do curso no Brasil em anos e semestres (ex: '4 anos (8 semestres)' ou '5 anos (10 semestres)'). Seja direto.",
                "niveis_atuacao": ["Júnior", "Pleno", "Sênior", "Especialista/Gestão"],
                "salario_medio": "Faixa salarial REAL do mercado brasileiro atual (ex: R$ 3.500 a R$ 15.000)",
                "custo_curso": "Estimativa EXATA da mensalidade em faculdades privadas no Brasil (ex: R$ 800 a R$ 1.500 / mês) e se é comum em federais.",
                "areas": [
                    {{"nome": "Nome da Área de atuação 1", "desc": "Breve descrição profissional e objetiva."}},
                    {{"nome": "Nome da Área de atuação 2", "desc": "..."}},
                    {{"nome": "Nome da Área de atuação 3", "desc": "..."}}
                ]
            }}
            """
            response = model.generate_content(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            dados_gerados = json.loads(text)
            
            # Garantir que todos os campos existem
            for key in dados.keys():
                if key in dados_gerados:
                    dados[key] = dados_gerados[key]
                    
        except Exception as e:
            print("Gemini fallback detalhe_profissao due to:", e)
            
    youtube_id = search_youtube_video(f"O que faz um {dados['nome']} mercado de trabalho")
            
    complete_mission(request.user, f'explored_{nome.lower()}', 150)
    return render(request, 'profissao_detalhe.html', {'dados': dados, 'profissao_original': nome, 'youtube_id': youtube_id})

from django.http import JsonResponse

def get_category_by_name(nome):
    nome_lower = nome.lower()
    health_keywords = ['medicina', 'enfermagem', 'fisioterapia', 'nutrição', 'nutricao', 'odonto', 'biomedicina', 'farmácia', 'farmacia']
    human_keywords = ['direito', 'psicologia', 'marketing', 'publicidade', 'relações', 'relacoes', 'administração', 'administracao', 'letras', 'história', 'historia', 'design', 'arte']
    nature_keywords = ['agronomia', 'ambiental', 'ecologia', 'zootecnia', 'biologia', 'geografia', 'veterinária', 'veterinaria']
    
    if any(k in nome_lower for k in health_keywords): return 'health'
    if any(k in nome_lower for k in human_keywords): return 'human'
    if any(k in nome_lower for k in nature_keywords): return 'nature'
    return 'tech'

@login_required
def gerar_video_ia(request):
    nome = request.GET.get('nome', '')
    
    cat_fallback = get_category_by_name(nome)
    
    # Base fallback
    cenas = [
        {'titulo': f'{nome} na Prática', 'texto': 'O profissional resolve problemas estratégicos no seu setor.'},
        {'titulo': 'A Rotina', 'texto': 'Atua com ferramentas dinâmicas para organizar e projetar novas soluções.'},
        {'titulo': 'O Impacto', 'texto': 'O resultado afeta diretamente o desenvolvimento da sociedade como um todo.'}
    ]
    
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    bg_url = f'/static/images/{cat_fallback}_bg.png'
    print(f"DEBUG: HAS_GEMINI={HAS_GEMINI}, API_KEY_LENGTH={len(api_key)}")
    
    if HAS_GEMINI and api_key and nome:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 0.8})
            prompt = f'''
            Gere um roteiro de "Vídeo Curto Animado" (estilo Reels/Shorts) de exatamente 3 cenas sobre a profissão de {nome}.
            A linguagem deve ser empolgante, porém ALTAMENTE TÉCNICA E PRECISA. Baseie-se em dados reais do mercado de trabalho atual.
            
            Retorne ESTRITAMENTE em formato JSON, sem marcações markdown, assim:
            {{
                "categoria_imagem": "responda com apenas uma destas opções: tech, health, human, nature",
                "cenas": [
                    {{"titulo": "A Missão", "texto": "Objetivo técnico no mercado..."}},
                    {{"titulo": "Na Prática", "texto": "Ferramentas reais e dia a dia prático..."}},
                    {{"titulo": "O Impacto", "texto": "Relevância econômica e social..."}}
                ]
            }}
            '''
            response = model.generate_content(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            import json
            dados = json.loads(text)
            if 'cenas' in dados:
                cenas = dados['cenas']
            
            cat = dados.get('categoria_imagem', 'tech')
            if cat not in ['tech', 'health', 'human', 'nature']:
                cat = 'tech'
            bg_url = f'/static/images/{cat}_bg.png'
            
        except Exception as e:
            print("Gemini API Error for Video Modal:", e)
            bg_url = f'/static/images/{cat_fallback}_bg.png'
            
    complete_mission(request.user, 'watched_ai_video', 200)
    return JsonResponse({"cenas": cenas, "bg_url": bg_url})

@login_required
def meu_progresso(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    # Generic streak update just in case they just open this page
    complete_mission(request.user, None, 0)
    
    completed_missions = set(UserMission.objects.filter(user=request.user).values_list('mission_code', flat=True))
    
    titles = ['Novato', 'Aprendiz', 'Explorador Curioso', 'Visionário', 'Mestre das Carreiras']
    level_title = titles[profile.level - 1] if profile.level <= len(titles) else 'Lenda Viva'
    next_level_xp = profile.level * 1000

    recent_missions = [
        {'title': 'O Despertar (Perfil)', 'status': 'completed' if 'profile_completed' in completed_missions else 'active', 'xp': 500, 'icon': 'user', 'url': 'profile'},
        {'title': 'Teste Vocacional', 'status': 'completed' if 'test_vocational' in completed_missions else 'active', 'xp': 1000, 'icon': 'award', 'url': 'iniciar_teste'},
        {'title': 'Visão do Futuro (IA)', 'status': 'completed' if 'watched_youtube_video' in completed_missions else 'active', 'xp': 200, 'icon': 'play-circle', 'url': 'explorar_profissoes'},
        {'title': 'Voz da Comunidade (Feedback)', 'status': 'completed' if 'feedback_completed' in completed_missions else 'active', 'xp': 300, 'icon': 'message-square', 'url': 'feedback'},
    ]
    
    # Fazer as missões sumirem (estilo Duolingo daily quests) quando completadas
    recent_missions = [m for m in recent_missions if m['status'] == 'active']
    
    context = {
        'total_xp': profile.total_xp,
        'gems': profile.gems,
        'level': profile.level,
        'level_title': level_title,
        'next_level_xp': next_level_xp,
        'streak_days': profile.streak_days,
        'recent_missions': recent_missions
    }
    return render(request, 'progresso.html', context)


@login_required
def localiza_futuro(request):
    return render(request, 'localiza_futuro.html')


@login_required
def guia_carreiras(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'guia_carreiras.html', {'profile': profile})


@login_required
def feedback_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    complete_mission(request.user, None, 0)
    
    user_feedback = Feedback.objects.filter(user=request.user).first()
    is_completed = UserMission.objects.filter(user=request.user, mission_code='feedback_completed').exists()
    
    total_feedbacks = Feedback.objects.count()
    if total_feedbacks > 0:
        from django.db.models import Avg
        avg_stats = Feedback.objects.aggregate(
            avg_overall=Avg('overall_rating'),
            avg_design=Avg('rating_design'),
            avg_usability=Avg('rating_usability'),
            avg_test=Avg('rating_vocational_test')
        )
        avg_overall = round(avg_stats['avg_overall'] or 4.9, 1)
        avg_design = round(avg_stats['avg_design'] or 4.8, 1)
        avg_usability = round(avg_stats['avg_usability'] or 4.9, 1)
    else:
        avg_overall = 4.9
        avg_design = 4.8
        avg_usability = 4.9
        total_feedbacks = 128

    if request.method == 'POST':
        try:
            rating_design = int(request.POST.get('rating_design', 5))
            rating_colors = int(request.POST.get('rating_colors', 5))
            rating_typography = int(request.POST.get('rating_typography', 5))
            rating_usability = int(request.POST.get('rating_usability', 5))
            rating_vocational_test = int(request.POST.get('rating_vocational_test', 5))
            rating_responsiveness = int(request.POST.get('rating_responsiveness', 5))
            overall_rating = int(request.POST.get('overall_rating', 5))
        except (ValueError, TypeError):
            rating_design = 5
            rating_colors = 5
            rating_typography = 5
            rating_usability = 5
            rating_vocational_test = 5
            rating_responsiveness = 5
            overall_rating = 5

        favorite_feature = request.POST.get('favorite_feature', '').strip()
        suggestions = request.POST.get('suggestions', '').strip()
        
        age_str = request.POST.get('age', '').strip()
        age = int(age_str) if age_str.isdigit() else None
        is_working = request.POST.get('is_working', '').strip()
        work_experience_time = request.POST.get('work_experience_time', '').strip()
        
        if user_feedback:
            user_feedback.rating_design = rating_design
            user_feedback.rating_colors = rating_colors
            user_feedback.rating_typography = rating_typography
            user_feedback.rating_usability = rating_usability
            user_feedback.rating_vocational_test = rating_vocational_test
            user_feedback.rating_responsiveness = rating_responsiveness
            user_feedback.overall_rating = overall_rating
            user_feedback.favorite_feature = favorite_feature
            user_feedback.suggestions = suggestions
            user_feedback.age = age
            user_feedback.is_working = is_working
            user_feedback.work_experience_time = work_experience_time
            user_feedback.save()
        else:
            user_feedback = Feedback.objects.create(
                user=request.user,
                rating_design=rating_design,
                rating_colors=rating_colors,
                rating_typography=rating_typography,
                rating_usability=rating_usability,
                rating_vocational_test=rating_vocational_test,
                rating_responsiveness=rating_responsiveness,
                overall_rating=overall_rating,
                favorite_feature=favorite_feature,
                suggestions=suggestions,
                age=age,
                is_working=is_working,
                work_experience_time=work_experience_time
            )
            
        xp_awarded = 300
        gems_awarded = 30
        newly_completed = complete_mission(request.user, 'feedback_completed', xp_awarded)
        if newly_completed:
            profile.gems += gems_awarded
            profile.save()
            reward_granted = True
        else:
            reward_granted = False
            
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
            return JsonResponse({
                'success': True,
                'reward_granted': reward_granted,
                'xp': xp_awarded,
                'gems': gems_awarded,
                'total_xp': profile.total_xp,
                'total_gems': profile.gems,
                'level': profile.level,
                'message': 'Feedback enviado com sucesso! Recompensa resgatada com sucesso!'
            })
        
        return render(request, 'feedback.html', {
            'profile': profile,
            'feedback': user_feedback,
            'is_completed': True,
            'reward_granted': reward_granted,
            'xp_awarded': xp_awarded,
            'gems_awarded': gems_awarded,
            'avg_overall': avg_overall,
            'avg_design': avg_design,
            'avg_usability': avg_usability,
            'total_feedbacks': total_feedbacks,
            'success_modal': True
        })

    return render(request, 'feedback.html', {
        'profile': profile,
        'feedback': user_feedback,
        'is_completed': is_completed,
        'avg_overall': avg_overall,
        'avg_design': avg_design,
        'avg_usability': avg_usability,
        'total_feedbacks': total_feedbacks,
    })


from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q

@login_required
def admin_feedbacks_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('home')

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    query = request.GET.get('q', '').strip()
    rating_filter = request.GET.get('rating', '')
    feature_filter = request.GET.get('feature', '')

    feedbacks_qs = Feedback.objects.select_related('user', 'user__profile').all()

    if query:
        feedbacks_qs = feedbacks_qs.filter(
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(suggestions__icontains=query) |
            Q(favorite_feature__icontains=query)
        )

    if rating_filter:
        try:
            feedbacks_qs = feedbacks_qs.filter(overall_rating=int(rating_filter))
        except ValueError:
            pass

    if feature_filter:
        feedbacks_qs = feedbacks_qs.filter(favorite_feature=feature_filter)

    total_feedbacks = Feedback.objects.count()
    total_users = User.objects.count()

    stats = Feedback.objects.aggregate(
        avg_overall=Avg('overall_rating'),
        avg_design=Avg('rating_design'),
        avg_colors=Avg('rating_colors'),
        avg_typography=Avg('rating_typography'),
        avg_usability=Avg('rating_usability'),
        avg_vocational=Avg('rating_vocational_test'),
        avg_responsiveness=Avg('rating_responsiveness'),
    )

    avg_overall = round(stats['avg_overall'] or 0, 1)
    avg_design = round(stats['avg_design'] or 0, 1)
    avg_colors = round(stats['avg_colors'] or 0, 1)
    avg_typography = round(stats['avg_typography'] or 0, 1)
    avg_usability = round(stats['avg_usability'] or 0, 1)
    avg_vocational = round(stats['avg_vocational'] or 0, 1)
    avg_responsiveness = round(stats['avg_responsiveness'] or 0, 1)

    # Calculate star distribution percentages
    rating_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for row in Feedback.objects.values('overall_rating').annotate(c=Count('id')):
        r = row['overall_rating']
        if r in rating_counts:
            rating_counts[r] = row['c']

    rating_distribution = []
    for star in [5, 4, 3, 2, 1]:
        cnt = rating_counts[star]
        pct = int((cnt / total_feedbacks * 100)) if total_feedbacks > 0 else 0
        rating_distribution.append({'stars': star, 'count': cnt, 'percent': pct})

    # Top favorite features
    top_features = Feedback.objects.exclude(favorite_feature__isnull=True).exclude(favorite_feature='').values('favorite_feature').annotate(total=Count('id')).order_by('-total')[:5]

    context = {
        'profile': profile,
        'feedbacks': feedbacks_qs,
        'total_feedbacks': total_feedbacks,
        'total_users': total_users,
        'avg_overall': avg_overall,
        'avg_design': avg_design,
        'avg_colors': avg_colors,
        'avg_typography': avg_typography,
        'avg_usability': avg_usability,
        'avg_vocational': avg_vocational,
        'avg_responsiveness': avg_responsiveness,
        'rating_distribution': rating_distribution,
        'top_features': top_features,
        'query': query,
        'rating_filter': rating_filter,
        'feature_filter': feature_filter,
    }

    return render(request, 'admin_feedbacks.html', context)

@login_required
def my_feedbacks_view(request):
    """Mostra os feedbacks do usuário logado de forma simples."""
    feedbacks = Feedback.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_feedbacks.html', {'feedbacks': feedbacks})


@login_required
def user_feedbacks_view(request, username):
    """Display feedbacks for a specific user (admin can view any)."""
    # Admin can view any user's feedbacks; regular users only their own
    if request.user.is_staff or request.user.is_superuser:
        target_user = User.objects.filter(username=username).first()
    else:
        target_user = request.user
    if not target_user:
        return redirect('list_users')
    feedbacks = Feedback.objects.filter(user=target_user).order_by('-created_at')
    return render(request, 'user_feedbacks.html', {'feedbacks': feedbacks, 'target_user': target_user})
