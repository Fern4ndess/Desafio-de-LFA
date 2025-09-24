import tkinter as tk
import math

# --- Variáveis Globais ---
contador_estados = 0
objeto_arrastado = {"id": None, "x_inicial": 0, "y_inicial": 0} #dicionário
# Nova variável para controlar o modo de operação
modo_atual = "arrastar"
# Nova variável para guardar o estado de origem da transição
transicao_info = {"origem_id": None, "origem_coords": None}
# Nova lista para guardar um registro de todas as transições
lista_transicoes = []

# --- Funções de Eventos do Mouse ---

def iniciar_movimento(event):
    """
    Função "gerente" que é chamada em qualquer clique.
    Ela decide qual especialista chamar com base no modo atual.
    """
    global modo_atual
    if modo_atual == "arrastar":
        gerenciar_clique_arrastar(event)
    elif modo_atual == "transicao":
        gerenciar_clique_transicao(event)

# VERSÃO CORRETA E FINAL DA FUNÇÃO
def gerenciar_clique_arrastar(event):
    """
    Versão final e à prova de falhas da função de clique.
    Resolve o problema de arrastar pelo texto e os erros de índice.
    """
    itens_proximos = canvas.find_closest(event.x, event.y)

    # CASO 1: Canvas está vazio.
    if not itens_proximos:
        criar_novo_estado(event.x, event.y)
        return

    id_item_clicado = itens_proximos[0]
    tags_do_item = canvas.gettags(id_item_clicado)

    tag_unica_estado = None
    for t in tags_do_item:
        if t.startswith('q'):
            tag_unica_estado = t
            break

    # CASO 2: Clicamos em algo que não faz parte de um estado.
    if tag_unica_estado is None:
        criar_novo_estado(event.x, event.y)
        return
        
    # LÓGICA À PROVA DE FALHAS (SEM O "AND")
    # 1. Encontramos TODOS os componentes do estado usando a tag única.
    ids_do_grupo = canvas.find_withtag(tag_unica_estado)
    
    # 2. Iteramos no grupo para encontrar o ID específico do CÍRCULO.
    id_circulo = None
    for item_id in ids_do_grupo:
        if "estado" in canvas.gettags(item_id):
            id_circulo = item_id
            break
            
    # Se, por um acaso MUITO estranho, o círculo não for encontrado, saímos.
    if id_circulo is None:
        return 

    coords = canvas.coords(id_circulo)
    centro_x = (coords[0] + coords[2]) / 2
    centro_y = (coords[1] + coords[3]) / 2
    distancia = math.sqrt((event.x - centro_x)**2 + (event.y - centro_y)**2)
    raio = 30

    # CASO 3: Clique dentro do raio do estado -> ARRASTAR
    if distancia <= raio:
        objeto_arrastado["id"] = id_circulo
        objeto_arrastado["x_inicial"] = event.x
        objeto_arrastado["y_inicial"] = event.y
    # CASO 4: Clique fora do raio do estado -> CRIAR NOVO
    else:
        criar_novo_estado(event.x, event.y)

def gerenciar_clique_transicao(event):
    """
    Gerencia os cliques quando estamos no modo de criação de transição.
    """
    global transicao_info
    
    # Primeiro, verificamos se o usuário clicou em um estado
    itens_proximos = canvas.find_closest(event.x, event.y)
    if not itens_proximos:
        # Se clicou no fundo, cancelamos qualquer seleção de transição
        if transicao_info["origem_id"]:
            canvas.itemconfig(transicao_info["origem_id"], fill="lightblue") # Restaura a cor
        transicao_info["origem_id"] = None
        instrucoes.config(text="Ação cancelada. Clique no estado de origem.")
        return

    id_item_clicado = itens_proximos[0]
    
    # Apenas continuamos se o item clicado for um estado (círculo)
    if "estado" in canvas.gettags(id_item_clicado):
        
        # Se NENHUM estado de origem foi escolhido ainda (primeiro clique)
        if transicao_info["origem_id"] is None:
            transicao_info["origem_id"] = id_item_clicado
            canvas.itemconfig(id_item_clicado, fill="yellow") # Muda a cor para dar feedback
            instrucoes.config(text=f"Estado de origem selecionado. Clique no estado de destino.")
            
        # Se um estado de origem JÁ foi escolhido (segundo clique)
        else:
            id_origem = transicao_info["origem_id"]
            id_destino = id_item_clicado
            
            # Desenha a seta!
            criar_seta_transicao(id_origem, id_destino)
            
            # Limpa tudo para a próxima transição
            canvas.itemconfig(id_origem, fill="lightblue") # Restaura a cor
            transicao_info["origem_id"] = None
            instrucoes.config(text="Transição criada! Clique no próximo estado de origem.")


def criar_seta_transicao(id_origem, id_destino):
    """
    Desenha uma linha com uma seta e REGISTRA a transição na lista de memória.
    """
    coords_origem = canvas.coords(id_origem)
    x_origem = (coords_origem[0] + coords_origem[2]) / 2
    y_origem = (coords_origem[1] + coords_origem[3]) / 2
    
    coords_destino = canvas.coords(id_destino)
    x_destino = (coords_destino[0] + coords_destino[2]) / 2
    y_destino = (coords_destino[1] + coords_destino[3]) / 2

    # Cria a seta e guarda o ID dela
    id_seta = canvas.create_line(
        x_origem, y_origem, x_destino, y_destino,
        arrow=tk.LAST, fill="black", width=2, tags="transicao"
    )
    
    # --- A PARTE NOVA E IMPORTANTE ---
    # Registra a nova transição na nossa lista de memória
    nova_transicao = {
        "id_seta": id_seta,
        "origem": id_origem,
        "destino": id_destino
    }
    lista_transicoes.append(nova_transicao)
    print(f"Nova transição registrada: {nova_transicao}")

    canvas.tag_raise("estado")
    canvas.tag_raise("texto")

def atualizar_setas_conectadas(id_estado_movido):
    """
    Verifica a lista de transições e atualiza as coordenadas de todas as
    setas conectadas ao estado que foi movido.
    """
    # Pega as novas coordenadas do centro do estado que se moveu
    coords_movido = canvas.coords(id_estado_movido)
    novo_x = (coords_movido[0] + coords_movido[2]) / 2
    novo_y = (coords_movido[1] + coords_movido[3]) / 2

    # Percorre a nossa lista de memória de transições
    for transicao in lista_transicoes:
        # Se o estado movido for a ORIGEM desta transição
        if transicao["origem"] == id_estado_movido:
            # Mantém as coordenadas do destino e atualiza só as da origem
            coords_destino_antigo = canvas.coords(transicao["destino"])
            x_destino = (coords_destino_antigo[0] + coords_destino_antigo[2]) / 2
            y_destino = (coords_destino_antigo[1] + coords_destino_antigo[3]) / 2
            canvas.coords(transicao["id_seta"], novo_x, novo_y, x_destino, y_destino)

        # Se o estado movido for o DESTINO desta transição
        if transicao["destino"] == id_estado_movido:
            # Mantém as coordenadas da origem e atualiza só as do destino
            coords_origem_antigo = canvas.coords(transicao["origem"])
            x_origem = (coords_origem_antigo[0] + coords_origem_antigo[2]) / 2
            y_origem = (coords_origem_antigo[1] + coords_origem_antigo[3]) / 2
            canvas.coords(transicao["id_seta"], x_origem, y_origem, novo_x, novo_y)

def alternar_modo():
    """
    Alterna entre o modo de arrastar/criar estados e o modo de criar transições.
    """
    global modo_atual
    if modo_atual == "arrastar":
        modo_atual = "transicao"
        # Atualiza o texto do botão e do rótulo de instruções
        botao_modo.config(text="Modo Atual: Criar Transição")
        instrucoes.config(text="Clique em um estado de origem e depois em um de destino.")
    else:
        modo_atual = "arrastar"
        botao_modo.config(text="Modo Atual: Criar/Arrastar Estado")
        instrucoes.config(text="Clique na tela para criar um estado. Clique e arraste um estado para movê-lo.")
    print(f"Modo alterado para: {modo_atual}")

def arrastar_objeto(event):
    """
    Chamada quando o mouse é movido com o botão pressionado.
    Move o estado selecionado E ATUALIZA AS SETAS.
    """
    if objeto_arrastado["id"] is not None:
        dx = event.x - objeto_arrastado["x_inicial"]
        dy = event.y - objeto_arrastado["y_inicial"]
        
        tags = canvas.gettags(objeto_arrastado["id"])
        tag_unica = [t for t in tags if t.startswith('q')][0]
        
        canvas.move(tag_unica, dx, dy)
        
        objeto_arrastado["x_inicial"] = event.x
        objeto_arrastado["y_inicial"] = event.y

        # --- LINHA ADICIONADA ---
        # "Avisa" o sistema para atualizar as setas conectadas a este estado
        atualizar_setas_conectadas(objeto_arrastado["id"])

def finalizar_arraste(event):
    """
    Chamada quando o botão do mouse é solto.
    Finaliza o modo de arraste.
    """
    if objeto_arrastado["id"] is not None:
        print(f"Finalizando arraste.")
        # "Limpa" nosso dicionário de controle, indicando que nada está sendo arrastado.
        objeto_arrastado["id"] = None
        objeto_arrastado["x_inicial"] = 0
        objeto_arrastado["y_inicial"] = 0

# --- Função de Criação de Elementos ---

def criar_novo_estado(x, y):
    """
    Desenha um novo estado (círculo e texto) no canvas na posição (x, y).
    """
    global contador_estados
    raio = 30
    nome_estado = f"q{contador_estados}"
    
    # Desenha o círculo
    canvas.create_oval(
        x - raio, y - raio, x + raio, y + raio,
        fill="lightblue", outline="black", width=2,
        tags=("estado", nome_estado) # Adiciona duas tags: uma geral e uma única
    )
    
    # Desenha o texto
    canvas.create_text(
        x, y, text=nome_estado, font=("Arial", 12, "bold"),
        tags=("texto", nome_estado) # Adiciona duas tags: uma geral e uma única
    )
    
    contador_estados += 1

# --- Configuração da Janela e Canvas ---
janela = tk.Tk()
janela.title("JFLAP 2 - Editor e Simulador de Autômatos (v0.3)")
janela.geometry("800x600")
janela.configure(bg="#f0f0f0")

canvas = tk.Canvas(janela, bg="white", highlightthickness=1, highlightbackground="black")
canvas.pack(fill="both", expand=True, padx=10, pady=10)

# --- Mapeamento de Eventos (Bindings) ---
# Substituímos o antigo bind por estes três novos
canvas.bind("<ButtonPress-1>", iniciar_movimento)
canvas.bind("<B1-Motion>", arrastar_objeto)
canvas.bind("<ButtonRelease-1>", finalizar_arraste)

instrucoes = tk.Label(janela, text="Clique na tela para criar um estado. Clique e arraste um estado para movê-lo.", bg="#f0f0f0", font=("Arial", 10))
instrucoes.pack(pady=5)

# --- Botões e Widgets Finais ---
# Cria um Frame (container) para o botão, para melhor organização
frame_botoes = tk.Frame(janela, bg="#f0f0f0")
frame_botoes.pack(fill="x", padx=10)

# Botão para alternar o modo
botao_modo = tk.Button(frame_botoes, text="Modo Atual: Criar/Arrastar Estado", command=alternar_modo, width=30)
botao_modo.pack(pady=5)

# O rótulo de instruções que já tínhamos, vamos movê-lo para o frame também
instrucoes.pack_forget() # Remove o pack antigo
instrucoes.pack(in_=frame_botoes) # Adiciona ao novo frame

# --- Loop Principal da Aplicação ---
janela.mainloop()