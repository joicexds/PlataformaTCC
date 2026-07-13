from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from .forms import RegisterForm

@login_required
def home(request):
    return render(request, 'home.html')

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


from .models import UserProfile
from .forms import UserProfileForm

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
                model = genai.GenerativeModel("gemini-2.5-flash", generation_config={"temperature": 0.9})
                prompt = f"""
                ATENÇÃO: Gere perguntas INÉDITAS, CRIATIVAS e diferentes a cada execução. Não repita formatos padrões.
                Gere um teste vocacional rápido com exatamente 5 perguntas personalizadas de múltipla escolha.
                O perfil de preferências do usuário é:
                - Matéria que mais gosta: {materia}
                - Atividade de tempo livre: {hobby}
                - Habilidade principal: {habilidade}
                - Grande objetivo: {objetivo}

                Crie 5 perguntas que ajudem a diferenciar este perfil específico entre as áreas de: Humanas, Exatas, Saude ou Natureza.
                Cada pergunta deve conter exatamente 4 alternativas (A, B, C, D) com textos envolventes, curtos e dinâmicos.
                Cada alternativa deve ter mapeada uma categoria correspondente entre: 'Humanas', 'Exatas', 'Saude' ou 'Natureza'.
                Retorne a resposta estritamente no formato JSON estruturado abaixo, sem qualquer marcação markdown (como ```json ou ```):
                {{
                  "perguntas": [
                    {{
                      "id": 1,
                      "enunciado": "Qual...",
                      "image_prompt": "A short english prompt to generate a picture related to the question (max 6 words, ex: futuristic tech laboratory)",
                      "alternativas": [
                        {{"letra": "A", "texto": "...", "categoria": "Humanas"}},
                        {{"letra": "B", "texto": "...", "categoria": "Exatas"}},
                        {{"letra": "C", "texto": "...", "categoria": "Saude"}},
                        {{"letra": "D", "texto": "...", "categoria": "Natureza"}}
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
                model = genai.GenerativeModel("gemini-2.5-flash", generation_config={"temperature": 0.8})
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
            
        return render(request, 'teste_resultado.html', {'resultado': resultado, 'winner': winner})
        
    return redirect('iniciar_teste')


@login_required
def detalhe_profissao(request, nome):
    # Base fallback structure
    dados = {
        'nome': nome.title(),
        'descricao': f'A profissão de {nome.title()} é fundamental para o desenvolvimento e funcionamento da sociedade atual. Os profissionais dessa área lidam com desafios dinâmicos e possuem um amplo campo de oportunidades.',
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
            model = genai.GenerativeModel("gemini-2.5-flash", generation_config={"temperature": 0.5})
            prompt = f"""
            Você é um especialista em carreiras e mercado de trabalho no Brasil. O usuário quer saber detalhes reais e extremamente precisos sobre a profissão: "{nome}".
            Por favor, pesquise os DADOS REAIS E ATUAIS (2025/2026) dessa profissão no Brasil. O foco é fornecer valores exatos de mensalidade de faculdades e tempo exato de duração dos cursos.
            Gere um retorno ESTRITAMENTE em formato JSON, sem marcações markdown:
            {{
                "nome": "Nome oficial da profissão formatado (ex: Engenharia de Software)",
                "descricao": "Uma descrição profissional e clara sobre a rotina dessa profissão (máx 4 linhas).",
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
            
    return render(request, 'profissao_detalhe.html', {'dados': dados, 'profissao_original': nome})
