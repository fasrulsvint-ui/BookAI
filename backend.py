from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai.errors import APIError 
import os

# --- 1. Configuração Inicial ---
# O cliente busca a chave da variável de ambiente GEMINI_API_KEY no Render.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

app = Flask(__name__)
CORS(app) 

# Inicializa o cliente Gemini
try:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não está configurada nas variáveis de ambiente.")
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"ERRO CRÍTICO ao inicializar a API: {e}")
    client = None


# --- 2. Rota Raiz (Para Teste de Status) ---
@app.route('/', methods=['GET'])
def home():
    """Retorna um status simples para confirmar que o servidor está vivo."""
    if client is None:
        return jsonify({
            'status': 'Servidor BookAI Online, mas API Gemini Inoperante',
            'message': 'Verifique se a GEMINI_API_KEY está correta no ambiente do Render.',
        }), 503
        
    return jsonify({
        'status': 'Servidor BookAI Online e API Gemini Ativa',
        'message': 'A API está ativa. Use a rota /generate_ebook com método POST.',
        'version': '3.0 (Somente Geração de Texto)'
    })


# --- 3. Rota Principal de Geração de Conteúdo ---
@app.route('/generate_ebook', methods=['POST'])
def generate_ebook():
    """
    Recebe as configurações do livro do frontend e chama o Gemini para gerar 
    o conteúdo e o prompt da capa (como texto).
    """
    if client is None:
        return jsonify({'success': False, 'message': 'Cliente API não inicializado. Chave ausente ou inválida.'}), 500

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

            [CAPA_PROMPT]: Um robô detetive no estilo noir, iluminado pela chuva...
            ---
            [CONTEUDO_INICIO]:
            ...
            """
        
        # 2. Chama a API do Gemini
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
        )
        
        # 3. Processar a Resposta do Gemini
        aiResponseText = response.text
        
        # 4. Extrai o prompt de capa para retornar separadamente (para o frontend usar)
        capa_prompt = ""
        if "[CAPA_PROMPT]:" in aiResponseText:
            capa_prompt = aiResponseText.split('---')[0].replace('[CAPA_PROMPT]:', '').strip()

        # 5. Retorna o texto gerado e um campo de imagem simulado/vazio
        return jsonify({
            'success': True,
            'ai_response_text': aiResponseText,
            # Campo de imagem simulado ou vazio
            'image_url': '/placeholder.jpg' 
        })

    except APIError as e:
        return jsonify({
            'success': False,
            'message': f"Erro na API Gemini (Texto): {e.message}"
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Erro interno do servidor: {str(e)}"
        }), 500


# A rota /generate_cover FOI REMOVIDA.

if __name__ == '__main__':
    app.run(debug=True)