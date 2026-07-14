import sys

file_path = r'c:\Users\Joice\PlataformaTcc\visualizar\views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

bad_content = """    cenas = [
    return JsonResponse({"cenas": cenas})"""

good_content = """    cenas = [
        {'titulo': f'{nome} na Prática', 'texto': 'O profissional resolve problemas estratégicos no seu setor.'},
        {'titulo': 'A Rotina', 'texto': 'Atua com ferramentas dinâmicas para organizar e projetar novas soluções.'},
        {'titulo': 'O Impacto', 'texto': 'O resultado afeta diretamente o desenvolvimento da sociedade como um todo.'}
    ]
    
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    bg_url = '/static/images/tech_bg.png'
    
    if HAS_GEMINI and api_key and nome:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash", generation_config={"temperature": 0.8})
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
            bg_url = '/static/images/tech_bg.png'
            
    return JsonResponse({"cenas": cenas, "bg_url": bg_url})"""

content = content.replace(bad_content, good_content)
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed!')
