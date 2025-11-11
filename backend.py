from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai.errors import APIError # Importa erros de API para melhor tratamento
import os

# --- 1. Configuração Inicial ---
# O cliente busca a chave da variável de ambiente GEMINI_API_KEY no Render.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

app = Flask(__name__)
# O CORS é ESSENCIAL
CORS(app) 

# Inicializa o cliente Gemini
try:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não está configurada nas variáveis de ambiente.")
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    # Se a chave for inválida ou o cliente falhar ao inicializar, 
    # é melhor registrar e deixar o erro Bad Gateway (502) ocorrer no Render.
    print(f"ERRO CRÍTICO ao inicializar a API: {e}")
    client = None # Define como None para evitar chamadas futuras falhas


# --- 2. Rota Raiz (Para Teste de Status) ---
@app.route('/', methods=['GET'])
def home():
    """Retorna um status simples para confirmar que o servidor está vivo."""
    if client is None:
        return jsonify({
            'status': 'Servidor BookAI Online, mas API Gemini/Imagen Inoperante',
            'message': 'Verifique se a GEMINI_API_KEY está correta no ambiente do Render.',
        }), 503
        
    return jsonify({
        'status': 'Servidor BookAI Online e API Gemini/Imagen Ativa',
        'message': 'A API está ativa. Use as rotas /generate_ebook e /generate_cover com método POST.',
        'version': '2.0 (Com Geração de Imagem Real)'
    })


# --- 3. Rota Principal de Geração de Texto/Conteúdo ---
@app.route('/generate_ebook', methods=['POST'])
def generate_ebook():
    """
    Recebe as configurações do livro do frontend e chama o Gemini para gerar 
    o conteúdo e o prompt da capa.
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
        
        # 3. Retorna o texto gerado pela IA para o frontend
        return jsonify({
            'success': True,
            'ai_response_text': response.text
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


# --- 4. Rota para Geração de Imagem (Real) ---
@app.route('/generate_cover', methods=['POST'])
def generate_cover():
    """
    Chama a API Imagen para gerar a imagem da capa e retorna a imagem em Base64.
    """
    if client is None:
        return jsonify({'success': False, 'message': 'Cliente API não inicializado. Chave ausente ou inválida.'}), 500
        
    try:
        data = request.json
        cover_prompt = data.get('cover_prompt')
        
        if not cover_prompt:
            return jsonify({'success': False, 'message': 'Prompt da capa ausente.'}), 400

        # 1. Chama a API Imagen para gerar a imagem
        print(f"Gerando imagem com prompt: {cover_prompt}")
        
        image_result = client.models.generate_images(
            model='imagen-3.0-generate-002', # Modelo avançado para alta qualidade
            prompt=cover_prompt,
            config=dict(
                number_of_images=1,
                output_mime_type="image/jpeg",
                # Proporção ideal para capa de livro (Vertical)
                aspect_ratio='3:4' 
            )
        )

        # 2. Extrai a imagem em Base64
        if not image_result.generated_images:
             raise Exception("A API Imagen não retornou nenhuma imagem.")

        # O SDK retorna a imagem como bytes no campo image.image_bytes
        # O Base64 é necessário para a transmissão JSON e exibição no HTML
        base64_image = image_result.generated_images[0].image.image_bytes.decode('utf-8')
        
        # 3. Retorna a Base64 para o frontend
        return jsonify({
            'success': True,
            # Inclui o prefixo Base64 para o HTML
            'image_url': f"data:image/jpeg;base64,{base64_image}" 
        })

    except APIError as e:
        # Erros de API (ex: prompt inseguro, limite de uso, erro de autenticação)
        return jsonify({
            'success': False,
            'message': f"Erro na API Imagen (Imagem): {e.message}. Tente refrasear o prompt."
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Erro interno do servidor na geração da imagem: {str(e)}"
        }), 500


# O Gunicorn usará este objeto 'app' para rodar o servidor.
# if __name__ == '__main__': ...