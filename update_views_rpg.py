import re

path = r'c:\Users\Joice\PlataformaTcc\visualizar\views.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_prompt_pattern = r'prompt = f"""\s*ATENÇÃO: Gere perguntas INÉDITAS.*?\"\"\"'

new_prompt = '''prompt = f"""
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
                """'''

content = re.sub(old_prompt_pattern, new_prompt, content, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated views.py prompt successfully!")
