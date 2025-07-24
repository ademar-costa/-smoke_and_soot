import math
from flask import Flask, render_template, abort, request 
from datetime import datetime, timezone
import os # Para interagir com o sistema de arquivos
import frontmatter # Para ler o frontmatter dos arquivos .md
from markdown import markdown # Para converter Markdown para HTML
# Suas outras importações (Flask, render_template, abort, request, datetime, timezone) continuam aqui

app = Flask(__name__)
PASTA_POSTS = 'meus_posts' # Define o nome da pasta dos posts
ARTIGOS_POR_PAGINA = 5 # Defina quantos artigos você quer por página

def carregar_artigos():
    lista_de_artigos = []
    arquivos_md = [f for f in os.listdir(PASTA_POSTS) if f.endswith('.md')]

    for nome_arquivo in arquivos_md:
        caminho_completo = os.path.join(PASTA_POSTS, nome_arquivo)
        artigo_fm = frontmatter.load(caminho_completo) # Carrega frontmatter e conteúdo

        # Converte a string da data do frontmatter para um objeto datetime
        # Isso é importante para ordenação e formatação consistente
        try:
            data_obj = datetime.strptime(str(artigo_fm['date']), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            # Se a data estiver em outro formato ou ausente, use uma data padrão ou pule o artigo
            # Por simplicidade, vamos usar a data atual se houver erro
            print(f"Aviso: Data inválida ou ausente no arquivo {nome_arquivo}. Usando data atual.")
            data_obj = datetime.now(timezone.utc)

        artigo_data = {
            'slug': artigo_fm.get('slug', os.path.splitext(nome_arquivo)[0]), # Usa slug do frontmatter ou nome do arquivo
            'title': artigo_fm.get('title', 'Sem Título'),
            'date': data_obj,
            'category': artigo_fm.get('category', 'Sem Categoria'),
            'resumo': artigo_fm.get('resumo', ''),
            'content_md': artigo_fm.content, # Conteúdo em Markdown puro
            'content_html': markdown(artigo_fm.content) # Conteúdo convertido para HTML
        }
        lista_de_artigos.append(artigo_data)

    # Ordena os artigos pela data de publicação, dos mais recentes para os mais antigos
    lista_de_artigos.sort(key=lambda item: item['date'], reverse=True)
    return lista_de_artigos

@app.route('/')
def pagina_inicial():
    # Pega o número da página da URL (ex: /?page=2). Padrão é 1.
    pagina = request.args.get('page', 1, type=int)

    artigos_carregados = carregar_artigos() # Carrega os artigos dinamicamente

    # Lógica de paginação
    total_artigos = len(artigos_carregados)
    inicio = (pagina - 1) * ARTIGOS_POR_PAGINA
    fim = inicio + ARTIGOS_POR_PAGINA
    artigos_para_pagina = artigos_carregados[inicio:fim] # Fatiando a lista de artigos
    total_paginas = math.ceil(total_artigos / ARTIGOS_POR_PAGINA)
    # Vamos criar algumas variáveis para enviar ao template
    titulo_da_pagina = "Smoke and Stack"

    return render_template('index.html',
                           titulo_customizado=titulo_da_pagina, 
                           artigos=artigos_carregados, # Enviando os artigos
                           now=datetime.now(timezone.utc), # Passe o datetime atual
                           pagina_atual=pagina, # Passa o número da página atual
                           total_paginas=total_paginas) # Passa o total de páginas

# Nova rota para a página "Sobre Mim"
@app.route('/sobre')
def sobre():
    titulo_da_pagina = "Sobre Mim"
    return render_template('sobre.html',
                            titulo_customizado=titulo_da_pagina, 
                            now=datetime.now(timezone.utc))

@app.route('/artigo/<string:slug_artigo>') # Mudou de <int:artigo_id> para <string:slug_artigo>
def exibir_artigo(slug_artigo):
    artigos_carregados = carregar_artigos()
    artigo_encontrado = None
    for artigo_da_lista in artigos_carregados:
        if artigo_da_lista['slug'] == slug_artigo: # Compara com o slug
            artigo_encontrado = artigo_da_lista
            break

    if artigo_encontrado:
        return render_template('artigo_completo.html',
                               titulo_customizado=artigo_encontrado['title'],
                               artigo=artigo_encontrado,
                               now=datetime.now(timezone.utc))
    else:
        abort(404)

@app.route('/categoria/<string:nome_categoria>')
def exibir_categoria(nome_categoria):
    pagina = request.args.get('page', 1, type=int)

    artigos_carregados = carregar_artigos()
    artigos_da_categoria_todos = [
        artigo for artigo in artigos_carregados if artigo['category'].lower() == nome_categoria.lower()
    ]

    # Lógica de paginação aplicada à lista filtrada
    total_artigos = len(artigos_da_categoria_todos)
    inicio = (pagina - 1) * ARTIGOS_POR_PAGINA
    fim = inicio + ARTIGOS_POR_PAGINA
    artigos_para_pagina = artigos_da_categoria_todos[inicio:fim]
    total_paginas = math.ceil(total_artigos / ARTIGOS_POR_PAGINA)

    return render_template('categoria_artigos.html',
                           titulo_customizado=f"Categoria: {nome_categoria.capitalize()}",
                           categoria_atual=nome_categoria,
                           artigos=artigos_para_pagina, # Lista fatiada
                           now=datetime.now(timezone.utc),
                           pagina_atual=pagina, # Página atual
                           total_paginas=total_paginas) # Total de páginas

@app.route('/contato', methods=['GET', 'POST'])
def contato():
    mensagem_status = None # Para feedback ao usuário
    if request.method == 'POST':
        # Processar os dados do formulário
        nome = request.form.get('nome')
        email = request.form.get('email')
        assunto = request.form.get('assunto')
        mensagem_texto = request.form.get('mensagem')

        # Por enquanto, apenas imprimimos no console do Flask
        print("----- Nova Mensagem de Contato -----")
        print(f"Nome: {nome}")
        print(f"Email: {email}")
        print(f"Assunto: {assunto}")
        print(f"Mensagem: {mensagem_texto}")
        print("------------------------------------")

        mensagem_status = "Obrigado! Sua mensagem foi recebida."
        # Idealmente, aqui você enviaria o email ou salvaria no banco.
        # E depois redirecionaria para evitar reenvio ao atualizar (Post/Redirect/Get pattern)
        # Mas por agora, vamos apenas renderizar o template com a mensagem.

        # Retornamos o mesmo template, mas com a mensagem de sucesso.
        # Poderíamos também limpar os campos ou redirecionar para uma página de "obrigado".
        return render_template('contato.html',
                               titulo_customizado="Contato",
                               now=datetime.now(timezone.utc),
                               mensagem_enviada=True) # Sinaliza que a mensagem foi "enviada"

    # Se for um método GET, apenas exibe o formulário
    return render_template('contato.html',
                           titulo_customizado="Contato",
                           now=datetime.now(timezone.utc),
                           mensagem_enviada=False) # Formulário ainda não foi enviado

# Função para lidar com erros 404 (opcional, mas bom para personalizar a página)
@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template('404.html', now=datetime.now(timezone.utc)), 404


if __name__ == '__main__':
    app.run(debug=True)