from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
import os

# 🚨 SUA CHAVE DE API AQUI 🚨
# Esta chave estará segura no seu servidor Render e não será exposta ao usuário.
GEMINI_API_KEY = "AIzaSyCVTtjwILegv32mCGP05PntO9wMpB5Gnhc" 

# Configuração do App Flask
app = Flask(__name__)
# O CORS é ESSENCIAL para permitir que o seu HTML (em um domínio diferente)
# converse com o seu servidor Render.
CORS(app) 

# Inicializa o cliente Gemini
try:
    # O Render usará esta chave para se comunicar com a API do Google.
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Erro ao inicializar o cliente Gemini: {e}")
    
# --- Rota Principal de Geração de Texto/Conteúdo ---
@app.route('/generate_ebook', methods=['POST'])
def generate_ebook():
    """
    Recebe as configurações do livro do frontend, chama o Gemini para gerar 
    o conteúdo e o prompt da capa.
    """
    try:
        data = request.json
        
        # 1. Monta o Prompt completo
        full_prompt = f"""
            Aja como um gerador de conteúdo para Ebooks e um assistente de design.
            Gere o conteúdo COMPLETO de um ebook de {data.get('pages', 5)} páginas.

            **FORMATO ESTRUTURAL OBRIGATÓRIO:**
            1. A primeira linha deve ser o prompt de imagem para a capa. Use o formato: [CAPA_PROMPT]: (descrição).
            2. Use o separador "---" para dividir a capa do conteúdo.
            3. O conteúdo deve ser em **Markdown** ou HTML e usar marcações **PÁGINA X:**.
            4. O título é **{data.get('title', 'Título Desconhecido')}** e o autor **{data.get('author', 'Autor Desconhecido')}**.
            5. O estilo da escrita deve ser {data.get('genre', 'Geral')}.

            **SINOPSE:** {data.get('synopsis', 'Nenhuma sinopse fornecida.')}

            **EXEMPLO DE INÍCIO DA RESPOSTA:**

            [CAPA_PROMPT]: Um detetive robô...
            ---
            [CONTEUDO_INICIO]:
            # {data.get('title')}
            ## Por {data.get('author')}
            
            **SUMÁRIO:**
            ...
            
            **PÁGINA 1:** (Conteúdo da primeira página...)
            ...
            [CONTEUDO_FIM]
            """
        
        # 2. Chama a API do Gemini
        # Usamos generate_content para o texto longo.
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
        )
        
        # 3. Retorna o texto gerado pela IA para o frontend
        return jsonify({
            'success': True,
            'ai_response_text': response.text
        })

    except Exception as e:
        print(f"Erro na comunicação com a API Gemini: {e}")
        return jsonify({
            'success': False,
            'message': f"Erro no servidor ao chamar a IA: {str(e)}. Verifique se a chave de API está correta e ativa."
        }), 500

# --- Rota para Geração de Imagem (Simulação para Simplificar) ---
@app.route('/generate_cover', methods=['POST'])
def generate_cover():
    """
    Simula o retorno de uma URL de imagem para a capa.
    Em produção, esta rota chamaria a API Imagen ou DALL-E e faria o upload.
    """
    try:
        data = request.json
        cover_prompt = data.get('cover_prompt')
        
        # SIMULAÇÃO DA URL DA IMAGEM
        # Esta URL é um placeholder que mostra a proporção da capa.
        # A URL real viria de um servidor de hospedagem após a geração pela IA de Imagem.
        simulated_image_url = f"https://via.placeholder.com/400x600?text=Capa+Gerada+Pela+IA+Baseada+Em:{cover_prompt[:25]}..."
        
        return jsonify({
            'success': True,
            'image_url': simulated_image_url
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Erro no servidor ao gerar a imagem: {str(e)}"
        }), 500

# O Gunicorn usará este objeto 'app' para rodar o servidor.
# O bloco abaixo é desnecessário no Render, mas útil para testes locais.
# if __name__ == '__main__':
#     app.run(port=5000)