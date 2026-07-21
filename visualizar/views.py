from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from .forms import RegisterForm

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
    ]
    
    # Conquista Recente
    conquista_recente = None
    if 'watched_youtube_video' in completed_missions:
        conquista_recente = {'title': 'Cinéfilo das Carreiras', 'desc': 'Você assistiu ao seu primeiro vídeo de profissão!', 'icon': 'film', 'xp_bonus': 200}
    elif profile.streak_days >= 3:
        conquista_recente = {'title': 'Semana Impecável', 'desc': '3 dias de ofensiva mantida.', 'icon': 'flame', 'xp_bonus': 500}
    elif 'profile_completed' in completed_missions:
        conquista_recente = {'title': 'Primeiros Passos', 'desc': 'Completou seu perfil inicial!', 'icon': 'zap', 'xp_bonus': 100}

    context = {
        'profile': profile,
        'xp_percent': xp_percent,
        'etapas': etapas,
        'etapas_completas': etapas_completas,
        'missoes_recentes': missoes_recentes,
        'conquista_recente': conquista_recente
    }
    
    return render(request, 'home.html', context)

class CustomLoginView(LoginView):
    template_name = 'login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
        return super().dispatch(request, *args, **kwargs)

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required
def explorar_profissoes(request):
    return render(request, 'explorar_profissoes.html')


from .models import UserProfile, UserMission
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
            "enunciado": "Se você pudesse resolver um grande problema do mundo, qual seria?",
            "image_prompt": "global world healing and diverse people",
            "alternativas": [
                {"letra": "A", "texto": "Combater a desigualdade social e defender direitos humanos.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Desenvolver uma nova tecnologia limpa ou inteligência artificial.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Encontrar a cura para doenças graves ou melhorar hospitais.", "categoria": "Saude"},
                {"letra": "D", "texto": "Preservar a fauna, flora e reverter o aquecimento global.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 2,
            "enunciado": "Qual tipo de projeto acadêmico ou escolar você prefere integrar?",
            "image_prompt": "students working together on science project",
            "alternativas": [
                {"letra": "A", "texto": "Produção de redações, debates sociais ou apresentações de teatro.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Criação de robôs, planilhas financeiras ou desenvolvimento de sistemas.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Pesquisa sobre corpo humano, primeiros socorros ou nutrição.", "categoria": "Saude"},
                {"letra": "D", "texto": "Experimentos químicos, coleta de solo ou observação biológica.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 3,
            "enunciado": "Como você se descreve ao tomar decisões importantes?",
            "image_prompt": "brain and heart glowing neon futuristic",
            "alternativas": [
                {"letra": "A", "texto": "Empático, considerando o impacto emocional nas outras pessoas.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Racional, analisando estatísticas, gráficos e dados numéricos.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Cuidadoso, priorizando o bem-estar físico e a segurança dos outros.", "categoria": "Saude"},
                {"letra": "D", "texto": "Observador, analisando o funcionamento dos sistemas e ambientes naturais.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 4,
            "enunciado": "Se você estivesse em uma empresa, qual cargo chamaria mais sua atenção?",
            "image_prompt": "modern corporate office teamwork futuristic",
            "alternativas": [
                {"letra": "A", "texto": "Gerente de Recursos Humanos ou Diretor de Comunicação.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Engenheiro de Software, Analista de Dados ou Diretor Financeiro.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Médico do Trabalho ou Coordenador de Segurança e Saúde.", "categoria": "Saude"},
                {"letra": "D", "texto": "Gestor Ambiental ou Consultor de Sustentabilidade.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 5,
            "enunciado": "No seu tempo livre, qual destas atividades mais te relaxa?",
            "image_prompt": "person relaxing with books and plants",
            "alternativas": [
                {"letra": "A", "texto": "Escrever, desenhar, tocar música ou conversar sobre diversos temas.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Jogar videogame de estratégia, xadrez ou programar.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Praticar atividades físicas, cozinhar receitas saudáveis ou ler sobre saúde.", "categoria": "Saude"},
                {"letra": "D", "texto": "Cuidar de plantas, passear com animais de estimação ou caminhar ao ar livre.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 6,
            "enunciado": "Quando assiste a um documentário, qual tema prende mais sua atenção?",
            "image_prompt": "documentary themes nature tech history",
            "alternativas": [
                {"letra": "A", "texto": "História das civilizações, cultura pop ou movimentos artísticos.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Como as máquinas funcionam, viagens espaciais ou megaconstruções.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Corpo humano, mistérios da mente ou evolução da medicina.", "categoria": "Saude"},
                {"letra": "D", "texto": "Vida selvagem, oceanos inexplorados ou sustentabilidade do planeta.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 7,
            "enunciado": "Se você criasse um aplicativo, para que ele serviria?",
            "image_prompt": "smartphone glowing app interface",
            "alternativas": [
                {"letra": "A", "texto": "Uma rede social para conectar artistas, escritores e debater ideias.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Um sistema financeiro focado em investimentos e segurança de dados.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Um app de telemedicina para ajudar pessoas com rotinas de bem-estar.", "categoria": "Saude"},
                {"letra": "D", "texto": "Um mapeamento interativo para preservação de espécies e doação para ONGs ecológicas.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 8,
            "enunciado": "Qual dessas feiras ou eventos você mais gostaria de visitar?",
            "image_prompt": "event conference expo festival",
            "alternativas": [
                {"letra": "A", "texto": "Bienal do Livro ou Exposição de Arte Moderna.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Feira Internacional de Robótica ou Summit de Tecnologia.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Congresso de Biomedicina ou Feira de Inovação em Saúde.", "categoria": "Saude"},
                {"letra": "D", "texto": "Simpósio Internacional de Ecologia e Proteção Ambiental.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 9,
            "enunciado": "No trabalho em equipe, qual é geralmente a sua função natural?",
            "image_prompt": "teamwork collaboration modern office",
            "alternativas": [
                {"letra": "A", "texto": "O comunicador: responsável por mediar conflitos e apresentar as ideias do grupo.", "categoria": "Humanas"},
                {"letra": "B", "texto": "O estrategista: organiza os dados, planilhas e pensa na execução lógica.", "categoria": "Exatas"},
                {"letra": "C", "texto": "O cuidador: garante que o ambiente seja seguro, positivo e todos estejam bem.", "categoria": "Saude"},
                {"letra": "D", "texto": "O observador: foca em como o projeto interage com o meio ambiente e as regras naturais.", "categoria": "Natureza"}
            ]
        },
        {
            "id": 10,
            "enunciado": "Em um cenário de crise global, o que você tentaria fazer primeiro?",
            "image_prompt": "global crisis planning future",
            "alternativas": [
                {"letra": "A", "texto": "Organizar as pessoas e criar campanhas de comunicação eficientes.", "categoria": "Humanas"},
                {"letra": "B", "texto": "Construir uma infraestrutura tecnológica que garantisse a logística necessária.", "categoria": "Exatas"},
                {"letra": "C", "texto": "Montar equipes de resgate, primeiros socorros e triagem médica.", "categoria": "Saude"},
                {"letra": "D", "texto": "Mapear o impacto ambiental e proteger recursos hídricos e naturais críticos.", "categoria": "Natureza"}
            ]
        }
    ]
}

@login_required
def iniciar_teste(request):
    if request.method == 'POST':
        materia = request.POST.get('materia', '')
        hobby = request.POST.get('hobby', '')
        habilidade = request.POST.get('habilidade', '')
        objetivo = request.POST.get('objetivo', '')
        
        # Save to session for personalized result later
        request.session['user_preferences'] = {
            'materia': materia,
            'hobby': hobby,
            'habilidade': habilidade,
            'objetivo': objetivo
        }
        
        # Call Gemini if API Key is configured
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        questions_data = None
        
        if HAS_GEMINI and api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 0.9})
                prompt = f"""
                ATENÇÃO: VOCÊ É UM MESTRE DE RPG (GAME MASTER). O usuário quer uma experiência de jogo interativo e não um teste convencional.
                Gere exatamente 5 perguntas em formato de CENÁRIOS DE MISSÃO (ex: "Você caiu numa ilha deserta...", "Uma invasão alienígena começou...", "Você é um detetive num caso impossível...").
                Mude os temas (Espaço, Fantasia, Mistério, Sobrevivência, Cyberpunk, Apocalipse Zumbi) ALEATORIAMENTE a cada execução para que a aventura NUNCA se repita.
                O perfil do jogador é:
                - Matéria que mais gosta: {materia}
                - Atividade de tempo livre: {hobby}
                - Habilidade principal: {habilidade}
                - Grande objetivo: {objetivo}

                Crie 5 cenários desafiadores. As 4 alternativas (A, B, C, D) de cada cenário devem ser AÇÕES DIRETAS que o jogador pode tomar para resolver o problema.
                Cada ação deve refletir uma vocação diferente: 'Humanas', 'Exatas', 'Saude' ou 'Natureza'.
                Retorne a resposta estritamente no formato JSON estruturado abaixo, sem marcação markdown (nem ```json):
                {{
                  "perguntas": [
                    {{
                      "id": 1,
                      "enunciado": "Cenário 1: Você está preso em uma nave espacial com problemas nos motores em rota de colisão. O que você faz primeiro?",
                      "image_prompt": "futuristic spaceship interior crisis alarm",
                      "alternativas": [
                        {{"letra": "A", "texto": "Pego o rádio para acalmar a tripulação e organizar uma evacuação segura.", "categoria": "Humanas"}},
                        {{"letra": "B", "texto": "Acesso o terminal central e uso código para tentar hackear e reiniciar os propulsores.", "categoria": "Exatas"}},
                        {{"letra": "C", "texto": "Corro para a enfermaria para separar kits de primeiros socorros e checar sinais vitais.", "categoria": "Saude"}},
                        {{"letra": "D", "texto": "Analiso a física da gravidade do planeta abaixo para planejar um pouso forçado usando a atmosfera.", "categoria": "Natureza"}}
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

        # Base parameters
        prefs = request.session.get('user_preferences', {})
        winner = max(category_counts, key=category_counts.get) if category_counts else 'Exatas'
        
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        resultado = None
        
        if HAS_GEMINI and api_key and user_answers:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 0.8})
                prompt = f"""
                Gere um resultado de teste vocacional altamente personalizado para um usuário que tem maior afinidade com a área de: {winner}.
                As respostas dele no teste foram:
                {json.dumps(user_answers, ensure_ascii=False, indent=2)}
                E suas preferências iniciais:
                Matéria: {prefs.get('materia', '')}, Hobby: {prefs.get('hobby', '')}, Habilidade: {prefs.get('habilidade', '')}, Objetivo: {prefs.get('objetivo', '')}
                
                Crie um perfil vocacional engajador e preciso. Retorne ESTRITAMENTE em formato JSON, sem marcações markdown:
                {{
                    "titulo": "Título criativo do perfil (ex: Explorador da Lógica e Exatas)",
                    "descricao": "Uma descrição envolvente de até 3 linhas sobre as características vocacionais do usuário.",
                    "carreiras": [
                        {{"nome": "Nome da Profissão", "salario": "R$ X.XXX", "icone": "um icone da biblioteca lucide-icons (ex: code, heart, leaf, briefcase, globe, etc)"}},
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
            # Fallback Profiles mapping
            profiles = {
                'Exatas': {
                    'titulo': 'Explorador da Lógica e Exatas',
                    'descricao': 'Você é movido por dados, lógica, equações e tecnologia. Gosta de estruturar ideias e foca na resolução objetiva de problemas complexos.',
                    'carreiras': [
                        {'nome': 'Engenharia de Software', 'salario': 'R$ 8.500', 'icone': 'code'},
                        {'nome': 'Ciência de Dados', 'salario': 'R$ 9.000', 'icone': 'database'},
                        {'nome': 'Engenharia de Produção', 'salario': 'R$ 7.200', 'icone': 'settings'},
                        {'nome': 'Economia e Finanças', 'salario': 'R$ 6.800', 'icone': 'trending-up'}
                    ]
                },
                'Humanas': {
                    'titulo': 'Pensador e Comunicador de Humanas',
                    'descricao': 'Você valoriza a história, dinâmicas sociais, linguagem e conexões humanas. Empatia e comunicação são as suas maiores forças profissionais.',
                    'carreiras': [
                        {'nome': 'Direito', 'salario': 'R$ 7.800', 'icone': 'briefcase'},
                        {'nome': 'Psicologia', 'salario': 'R$ 4.500', 'icone': 'users'},
                        {'nome': 'Marketing e Publicidade', 'salario': 'R$ 5.200', 'icone': 'megaphone'},
                        {'nome': 'Relações Internacionais', 'salario': 'R$ 6.000', 'icone': 'globe'}
                    ]
                },
                'Saude': {
                    'titulo': 'Protetor do Cuidado e Saúde',
                    'descricao': 'Seu foco principal está na promoção do bem-estar físico e mental das pessoas. Você demonstra profundo zelo e sensibilidade para com o próximo.',
                    'carreiras': [
                        {'nome': 'Medicina', 'salario': 'R$ 15.000', 'icone': 'heart'},
                        {'nome': 'Enfermagem', 'salario': 'R$ 5.500', 'icone': 'activity'},
                        {'nome': 'Fisioterapia', 'salario': 'R$ 4.200', 'icone': 'shield-alert'},
                        {'nome': 'Nutrição', 'salario': 'R$ 4.000', 'icone': 'apple'}
                    ]
                },
                'Natureza': {
                    'titulo': 'Cientista e Protetor da Natureza',
                    'descricao': 'Você possui uma conexão natural com o meio ambiente, com a fauna, a flora e com o estudo das leis da biologia e ciências da terra.',
                    'carreiras': [
                        {'nome': 'Biotecnologia / Biologia', 'salario': 'R$ 5.200', 'icone': 'flask'},
                        {'nome': 'Engenharia Ambiental', 'salario': 'R$ 7.000', 'icone': 'leaf'},
                        {'nome': 'Medicina Veterinária', 'salario': 'R$ 5.000', 'icone': 'dog'},
                        {'nome': 'Agronomia', 'salario': 'R$ 6.800', 'icone': 'sprout'}
                    ]
                }
            }
            resultado = profiles.get(winner, profiles['Exatas'])
            
        complete_mission(request.user, 'test_vocational', 1000)
        return render(request, 'teste_resultado.html', {'resultado': resultado, 'winner': winner})
        
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
def registrar_bonus_video(request):
    """View para registrar a conquista de assistir ao vídeo."""
    if request.method == 'POST':
        concluiu_agora = complete_mission(request.user, 'watched_youtube_video', 200)
        return JsonResponse({'success': True, 'xp_ganho': 200, 'novo': concluiu_agora})
    return JsonResponse({'success': False})

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
        'recent_missions': recent_missions,
        'achievements': [
            {'title': 'Primeiro Login', 'desc': 'Você deu o primeiro passo!', 'icon': 'zap', 'xp_bonus': 100, 'unlocked': True},
            {'title': 'Semana Impecável', 'desc': '3 dias de ofensiva mantida.', 'icon': 'flame', 'xp_bonus': 500, 'unlocked': profile.streak_days >= 3},
            {'title': 'Cinéfilo das Carreiras', 'desc': 'Você assistiu ao seu primeiro vídeo de profissão!', 'icon': 'film', 'xp_bonus': 200, 'unlocked': 'watched_youtube_video' in completed_missions},
        ]
    }
    return render(request, 'progresso.html', context)
