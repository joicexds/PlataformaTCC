from django.test import TestCase, Client
from django.contrib.auth.models import User
from visualizar.views import (
    BACKUP_TEST,
    extract_preference_scores,
    calculate_vocational_diagnosis,
)

class VocationalTestDiagnosisTestCase(TestCase):
    def test_backup_test_structure_and_balance(self):
        """Garante que todas as perguntas do backup têm as 4 áreas equilibradas."""
        self.assertGreaterEqual(len(BACKUP_TEST['perguntas']), 10)
        expected_categories = {'Humanas', 'Exatas', 'Saude', 'Natureza'}
        for q in BACKUP_TEST['perguntas']:
            self.assertIn('enunciado', q)
            self.assertIn('alternativas', q)
            self.assertEqual(len(q['alternativas']), 4)
            cats = {alt['categoria'] for alt in q['alternativas']}
            self.assertEqual(cats, expected_categories, f"Pergunta {q['id']} não possui as 4 áreas.")

    def test_extract_preference_scores(self):
        """Verifica se o extrator pontua corretamente sem favorecer Exatas."""
        humanas_prefs = {
            'materia': 'Ciências Humanas: História Geral, Filosofia',
            'hobby': 'Socialização Profunda: Conversas filosóficas/pessoais',
            'habilidade': 'Análise Comportamental (Empatia)',
            'objetivo': 'Equidade Social e Justiça'
        }
        scores_h = extract_preference_scores(humanas_prefs)
        self.assertGreater(scores_h['Humanas'], scores_h['Exatas'])
        self.assertGreater(scores_h['Humanas'], scores_h['Saude'])

        saude_prefs = {
            'materia': 'Ciências Biológicas: Biologia Humana, Anatomia',
            'hobby': 'Prática Física ou Natureza: Atividades esportivas',
            'habilidade': 'Análise Comportamental (Empatia)',
            'objetivo': 'Saúde e Bem-estar Humano: Contribuição ativa'
        }
        scores_s = extract_preference_scores(saude_prefs)
        self.assertGreater(scores_s['Saude'], scores_s['Exatas'])

        natureza_prefs = {
            'materia': 'Ciências Biológicas: Ciências da Vida',
            'hobby': 'Natureza: exploração de ambientes externos e animais',
            'habilidade': 'Meticulosidade e Foco Prático',
            'objetivo': 'Conservação Biológica: Proteção à biodiversidade'
        }
        scores_n = extract_preference_scores(natureza_prefs)
        self.assertGreater(scores_n['Natureza'], scores_n['Exatas'])

    def test_calculate_diagnosis_winners(self):
        """Garante que o perfil vencedor corresponde às respostas do usuário."""
        # Usuário respondendo Humanas
        counts_h = {'Humanas': 4, 'Saude': 1}
        winner_h, sec_h, pcts_h, _ = calculate_vocational_diagnosis(counts_h, {})
        self.assertEqual(winner_h, 'Humanas')
        self.assertEqual(sum(pcts_h.values()), 100)

        # Usuário respondendo Saúde
        counts_s = {'Saude': 5}
        winner_s, sec_s, pcts_s, _ = calculate_vocational_diagnosis(counts_s, {})
        self.assertEqual(winner_s, 'Saude')
        self.assertEqual(sum(pcts_s.values()), 100)

        # Usuário respondendo Natureza
        counts_n = {'Natureza': 4, 'Humanas': 1}
        winner_n, sec_n, pcts_n, _ = calculate_vocational_diagnosis(counts_n, {})
        self.assertEqual(winner_n, 'Natureza')
        self.assertEqual(sum(pcts_n.values()), 100)

        # Usuário respondendo Exatas
        counts_e = {'Exatas': 4, 'Natureza': 1}
        winner_e, sec_e, pcts_e, _ = calculate_vocational_diagnosis(counts_e, {})
        self.assertEqual(winner_e, 'Exatas')
        self.assertEqual(sum(pcts_e.values()), 100)

    def test_tie_breaking_respects_user_preferences(self):
        """Em caso de empate nas respostas, o desempate segue a preferência declarada."""
        # Empate 2 Humanas vs 2 Saude
        tied_counts = {'Humanas': 2, 'Saude': 2}
        prefs_saude = {
            'materia': 'Ciências Biológicas',
            'hobby': 'Prática Física',
            'habilidade': 'Análise Comportamental',
            'objetivo': 'Saúde e Bem-estar Humano'
        }
        winner, _, _, _ = calculate_vocational_diagnosis(tied_counts, prefs_saude)
        self.assertEqual(winner, 'Saude')

    def test_flow_client_e2e_vocational_test(self):
        """Testa o fluxo completo HTTP: iniciar -> responder -> resultado."""
        user = User.objects.create_user(username='testuser@example.com', password='password123')
        client = Client()
        client.login(username='testuser@example.com', password='password123')

        # 1. Iniciar teste
        resp_init = client.post('/teste/iniciar/', {
            'materia': 'Ciências Humanas: História Geral, Filosofia',
            'hobby': 'Socialização Profunda: Conversas filosóficas',
            'habilidade': 'Análise Comportamental (Empatia)',
            'objetivo': 'Equidade Social e Justiça'
        })
        self.assertEqual(resp_init.status_code, 302)
        self.assertEqual(resp_init.url, '/teste/responder/')

        # 2. Responder teste
        resp_resp = client.get('/teste/responder/')
        self.assertEqual(resp_resp.status_code, 200)

        # 3. Enviar resultado com respostas de Humanas
        post_data = {
            'pergunta_1': 'Humanas',
            'pergunta_2': 'Humanas',
            'pergunta_3': 'Humanas',
            'pergunta_4': 'Saude',
            'pergunta_5': 'Natureza'
        }
        resp_result = client.post('/teste/resultado/', post_data)
        self.assertEqual(resp_result.status_code, 200)
        self.assertEqual(resp_result.context['winner'], 'Humanas')
        self.assertIn('percentages', resp_result.context)
        self.assertGreater(resp_result.context['percentages']['Humanas'], resp_result.context['percentages']['Exatas'])

    def test_guia_carreiras_view_and_return_to_dashboard(self):
        """Verifica se a página Guia de Carreiras carrega com sucesso e oferece a opção de voltar ao Dashboard."""
        user = User.objects.create_user(username='guia_user@example.com', password='password123')
        client = Client()
        client.login(username='guia_user@example.com', password='password123')

        resp = client.get('/guia-carreiras/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Voltar para o Dashboard')
        self.assertContains(resp, 'Pesquisar no Google')

