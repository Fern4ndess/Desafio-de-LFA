import tkinter as tk
from tkinter import messagebox # <-- NOVA LINHA
from tkinter import simpledialog # <-- NOVA LINHA
import math

# --- Classes ---
class Estado:
    def __init__(self, nome, x, y, canvas):
        self.nome = nome
        self.x = x
        self.y = y
        self.raio = 30
        self.canvas = canvas
        self.inicial = False
        self.aceitacao = False

        # Desenha o círculo
        self.id_circulo = canvas.create_oval(
            x - self.raio, y - self.raio, x + self.raio, y + self.raio,
            fill="lightblue", outline="black", width=2,
            tags=("estado", nome)
        )
        # Nome do estado
        self.id_texto = canvas.create_text(
            x, y, text=nome, font=("Arial", 12, "bold"),
            tags=("texto", nome)
        )

    def mover(self, dx, dy):
        self.canvas.move(self.nome, dx, dy)
        self.x += dx
        self.y += dy

    def set_inicial(self):
        self.inicial = True
        # seta indicando inicial
        self.canvas.create_line(
            self.x - 50, self.y, self.x - self.raio, self.y,
            arrow=tk.LAST, width=2, fill="green", tags=("seta_inicial", self.nome)
        )

    def toggle_aceitacao(self):
        self.aceitacao = not self.aceitacao
        if self.aceitacao:
            # círculo extra
            self.canvas.create_oval(
                self.x - self.raio + 5, self.y - self.raio + 5,
                self.x + self.raio - 5, self.y + self.raio - 5,
                outline="black", width=2, tags=("aceitacao", self.nome)
            )
        else:
            # remove o círculo duplo
            for item in self.canvas.find_withtag("aceitacao"):
                if self.nome in self.canvas.gettags(item):
                    self.canvas.delete(item)

    # --- MÉTODO NOVO A SER ADICIONADO ---
    def destruir(self):
        """
        Apaga todos os elementos visuais associados a este estado.
        Graças às tags únicas, podemos apagar tudo de uma vez.
        """
        # A tag self.nome (ex: "q0") foi adicionada a todos os componentes
        # visuais deste estado (círculo, texto, seta inicial, anel de aceitação).
        # Este único comando apaga todos eles do canvas.
        self.canvas.delete(self.nome)


class Transicao:
    def __init__(self, origem, destino, canvas, simbolo="ε"):
        self.origem = origem
        self.destino = destino
        self.canvas = canvas
        self.simbolo = simbolo
        self.tag_unica = f"trans_{id(self)}"
        self.offset_x = 0
        self.offset_y = 0
        self.is_loop = (self.origem == self.destino)
        self.atualizar_posicao()

    def atualizar_posicao(self):
        self.canvas.delete(self.tag_unica)
        if self.is_loop:
            self._desenhar_loop()
        else:
            self._desenhar_linha_reta()
        self.canvas.tag_raise("estado")
        self.canvas.tag_raise("texto")

    def _desenhar_linha_reta(self):
        # ... (este método pode continuar como está no seu código, ele já funciona bem)
        x_o, y_o = self.origem.x, self.origem.y
        x_d, y_d = self.destino.x, self.destino.y
        raio = self.origem.raio
        dist = math.dist((x_o, y_o), (x_d, y_d))
        if dist == 0: return
        vetor_x, vetor_y = (x_d - x_o) / dist, (y_d - y_o) / dist
        p_ini_x, p_ini_y = x_o + vetor_x * raio, y_o + vetor_y * raio
        p_fim_x, p_fim_y = x_d - vetor_x * raio, y_d - vetor_y * raio
        coords_linha = (p_ini_x + self.offset_x, p_ini_y + self.offset_y, p_fim_x + self.offset_x, p_fim_y + self.offset_y)
        coords_texto = (((x_o + x_d) / 2) + self.offset_x, ((y_o + y_d) / 2 - 15) + self.offset_y)
        self.canvas.create_line(coords_linha, arrow=tk.LAST, fill="black", width=2, tags=(self.tag_unica, "transicao"))
        self.canvas.create_text(coords_texto, text=self.simbolo, font=("Arial", 10, "italic"), tags=(self.tag_unica, "rotulo"))

    def _desenhar_loop(self):
        x, y = self.origem.x, self.origem.y
        raio_estado = self.origem.raio
        raio_loop = 20
        bounding_box = (x - raio_loop, y - (2 * raio_estado), x + raio_loop, y)
        self.canvas.create_arc(
            bounding_box, start=210, extent=-240, style=tk.ARC,
            outline="black", width=2, tags=(self.tag_unica, "transicao")
        )
        angulo_final_rad = math.radians(-30)
        centro_arco_x, centro_arco_y = x, y - raio_estado
        ponta_x = centro_arco_x + raio_loop * math.cos(angulo_final_rad)
        ponta_y = centro_arco_y - raio_loop * math.sin(angulo_final_rad)
        ponta1, ponta2, ponta3 = (ponta_x, ponta_y), (ponta_x - 10, ponta_y - 2), (ponta_x - 2, ponta_y + 8)
        self.canvas.create_polygon(ponta1, ponta2, ponta3, fill="black", tags=(self.tag_unica, "transicao"))
        coords_texto = (x, y - raio_estado - raio_loop - 8)
        self.canvas.create_text(coords_texto, text=self.simbolo, font=("Arial", 10, "italic"), tags=(self.tag_unica, "rotulo"))
        
    def atualizar_simbolo(self, novo_simbolo):
        self.simbolo = novo_simbolo
        self.atualizar_posicao()

    def destruir(self):
        self.canvas.delete(self.tag_unica)


# --- Variáveis Globais ---
contador_estados = 0
estados = {}
transicoes = []
objeto_arrastado = {"id": None, "x_inicial": 0, "y_inicial": 0}
modo_atual = "arrastar"
transicao_info = {"origem": None}


# --- Funções ---
def iniciar_movimento(event):
    """
    Função gerente final. Verifica primeiro se um rótulo de transição foi
    clicado, antes de verificar os modos de operação.
    """
    if modo_atual == "apagar":
        gerenciar_clique_apagar(event)
        return

    itens_proximos = canvas.find_closest(event.x, event.y)
    if itens_proximos:
        id_item_clicado = itens_proximos[0]
        tags = canvas.gettags(id_item_clicado)
        if "transicao" in tags or "rotulo" in tags:
            editar_rotulo_transicao(id_item_clicado)
            return

    if modo_atual == "arrastar":
        gerenciar_clique_arrastar(event)
    elif modo_atual == "transicao":
        gerenciar_clique_transicao(event)


def gerenciar_clique_arrastar(event):
    global contador_estados
    itens = canvas.find_closest(event.x, event.y)

    if not itens:
        criar_novo_estado(event.x, event.y)
        return

    id_item = itens[0]
    tags = canvas.gettags(id_item)

    tag_estado = None
    for t in tags:
        if t.startswith("q"):
            tag_estado = t
            break

    if tag_estado is None:
        criar_novo_estado(event.x, event.y)
        return

    estado = estados[tag_estado]
    dist = math.dist((event.x, event.y), (estado.x, estado.y))

    if dist <= estado.raio:
        objeto_arrastado["id"] = estado
        objeto_arrastado["x_inicial"] = event.x
        objeto_arrastado["y_inicial"] = event.y
    else:
        criar_novo_estado(event.x, event.y)


def gerenciar_clique_transicao(event):
    """
    Lógica de criação de transição que não depende mais do input_entry.
    """
    global transicao_info, estados, transicoes

    itens = canvas.find_closest(event.x, event.y)
    if not itens:
        if transicao_info["origem"]:
            canvas.itemconfig(transicao_info["origem"].id_circulo, fill="lightblue")
        transicao_info["origem"] = None
        instrucoes.config(text="Ação cancelada. Clique no estado de origem.")
        return

    tag_estado = None
    for t in canvas.gettags(itens[0]):
        if t.startswith("q"):
            tag_estado = t
            break

    if not tag_estado: return

    estado_clicado = estados[tag_estado]

    if transicao_info["origem"] is None:
        transicao_info["origem"] = estado_clicado
        canvas.itemconfig(estado_clicado.id_circulo, fill="yellow")
        instrucoes.config(text=f"Origem: {estado_clicado.nome}. Agora clique no destino.")
    else:
        estado_origem = transicao_info["origem"]
        estado_destino = estado_clicado

        transicao_gemea = None
        for t in transicoes:
            if t.origem == estado_destino and t.destino == estado_origem:
                transicao_gemea = t
                break

        # Cria a transição com o símbolo padrão "ε"
        nova_transicao = Transicao(estado_origem, estado_destino, canvas)
        transicoes.append(nova_transicao)

        # Lógica para desvio de setas gêmeas
        if transicao_gemea:
            dist = math.dist((estado_origem.x, estado_origem.y), (estado_destino.x, estado_destino.y))
            if dist == 0: dist = 1
            vetor_x = (estado_destino.x - estado_origem.x) / dist
            vetor_y = (estado_destino.y - estado_origem.y) / dist
            vetor_perp_x, vetor_perp_y = -vetor_y, vetor_x
            offset_dist = 10
            
            nova_transicao.offset_x = vetor_perp_x * offset_dist
            nova_transicao.offset_y = vetor_perp_y * offset_dist
            nova_transicao.atualizar_posicao()

            transicao_gemea.offset_x = -vetor_perp_x * offset_dist
            transicao_gemea.offset_y = -vetor_perp_y * offset_dist
            transicao_gemea.atualizar_posicao()

        canvas.itemconfig(estado_origem.id_circulo, fill="lightblue")
        transicao_info["origem"] = None
        instrucoes.config(text="Transição criada! Clique nela para editar o símbolo.")


def editar_rotulo_transicao(id_item_clicado):
    """
    Encontra a transição clicada pelo ID de um de seus componentes
    e abre uma caixa de diálogo para editar seu símbolo.
    """
    # Pega todas as tags do item que foi clicado
    tags_do_item = canvas.gettags(id_item_clicado)
    
    tag_alvo = None
    # Procura pela tag única da transição (ex: "trans_12345")
    for tag in tags_do_item:
        if tag.startswith("trans_"):
            tag_alvo = tag
            break
            
    if tag_alvo:
        transicao_alvo = None
        # Procura na nossa memória qual objeto Transicao tem essa tag
        for t in transicoes:
            if t.tag_unica == tag_alvo:
                transicao_alvo = t
                break
        
        if transicao_alvo:
            novo_simbolo = simpledialog.askstring(
                "Editar Símbolo",
                "Digite o novo símbolo para a transição:",
                initialvalue=transicao_alvo.simbolo
            )
            if novo_simbolo is not None: # Permite símbolos vazios, mas não cancelamento
                transicao_alvo.atualizar_simbolo(novo_simbolo)


def gerenciar_clique_apagar(event):
    """
    Gerencia os cliques no modo apagar.
    Agora apaga tanto estados (com suas transições) quanto transições individuais.
    """
    itens_proximos = canvas.find_closest(event.x, event.y)
    if not itens_proximos: return

    id_item_clicado = itens_proximos[0]
    tags_do_item = canvas.gettags(id_item_clicado)

    nome_estado = None
    for t in tags_do_item:
        if t.startswith('q'):
            nome_estado = t
            break

    # --- LÓGICA PARA APAGAR ESTADO (NOVA) ---
    if nome_estado:
        estado_para_apagar = estados.get(nome_estado)
        if not estado_para_apagar: return

        # Pergunta ao usuário se ele tem certeza
        confirmar = messagebox.askyesno(
            "Apagar Estado",
            f"Tem certeza que deseja apagar o estado '{nome_estado}'?\n"
            f"Todas as transições conectadas a ele também serão apagadas."
        )

        if confirmar:
            # 1. Encontra e apaga as transições conectadas
            transicoes_a_remover = [
                t for t in transicoes 
                if t.origem == estado_para_apagar or t.destino == estado_para_apagar
            ]
            
            for t in transicoes_a_remover:
                t.destruir()
                transicoes.remove(t)

            # 2. Apaga o estado em si
            estado_para_apagar.destruir()
            del estados[nome_estado]
            instrucoes.config(text=f"Estado {nome_estado} apagado.")
            print(f"Estado {nome_estado} e suas transições foram apagados.")
        else:
            instrucoes.config(text="Ação de apagar cancelada.")
        
        return # Termina a função aqui após tratar o clique no estado

    # --- LÓGICA PARA APAGAR TRANSIÇÃO (CORRIGIDA) ---
    tags_do_item = canvas.gettags(id_item_clicado)
    if "transicao" in tags_do_item or "rotulo" in tags_do_item:
        
        tag_alvo = None
        for tag in tags_do_item:
            if tag.startswith("trans_"):
                tag_alvo = tag
                break
        
        if tag_alvo:
            transicao_para_apagar = None
            for t in transicoes:
                if t.tag_unica == tag_alvo:
                    transicao_para_apagar = t
                    break
            
            if transicao_para_apagar:
                transicao_para_apagar.destruir()
                transicoes.remove(transicao_para_apagar)
                instrucoes.config(text="Transição apagada com sucesso.")

def atualizar_transicoes_conectadas(estado_movido):
    """
    Percorre a lista de transições e atualiza todas que estão
    conectadas ao estado que acabou de se mover.
    """
    # A lista agora se chama 'transicoes' e contém objetos Transicao
    for transicao in transicoes:
        # Verificamos se o estado movido é a origem OU o destino da transicao
        if transicao.origem == estado_movido or transicao.destino == estado_movido:
            # Mandamos a própria transição se redesenhar
            transicao.atualizar_posicao()

def arrastar_objeto(event):
    if objeto_arrastado["id"] is not None:
        dx = event.x - objeto_arrastado["x_inicial"]
        dy = event.y - objeto_arrastado["y_inicial"]

        estado = objeto_arrastado["id"]
        estado.mover(dx, dy)

        objeto_arrastado["x_inicial"] = event.x
        objeto_arrastado["y_inicial"] = event.y

        # --- LINHA ADICIONADA: A CONEXÃO FINAL ---
        # "Avisa" o sistema para atualizar as transições deste estado
        atualizar_transicoes_conectadas(estado)


def finalizar_arraste(event):
    if objeto_arrastado["id"] is not None:
        objeto_arrastado["id"] = None


def alternar_modo():
    """
    Alterna entre os três modos de operação: arrastar, transição e apagar.
    """
    global modo_atual
    if modo_atual == "arrastar":
        modo_atual = "transicao"
        botao_modo.config(text="Modo Atual: Criar Transição")
        instrucoes.config(text="Clique em um estado de origem e depois no destino.")
    elif modo_atual == "transicao":
        modo_atual = "apagar"
        botao_modo.config(text="Modo Atual: APAGAR")
        instrucoes.config(text="CUIDADO: Clique em um estado ou transição para apagar.")
    else: # modo_atual == "apagar"
        modo_atual = "arrastar"
        botao_modo.config(text="Modo Atual: Criar/Arrastar Estado")
        instrucoes.config(text="Clique para criar ou arrastar estados.")
    print(f"Modo alterado para: {modo_atual}")


def criar_novo_estado(x, y):
    global contador_estados
    nome_estado = f"q{contador_estados}"
    estado = Estado(nome_estado, x, y, canvas)
    estados[nome_estado] = estado

    if contador_estados == 0:
        estado.set_inicial()

    contador_estados += 1


def toggle_aceitacao_event(event):
    itens = canvas.find_closest(event.x, event.y)
    if not itens:
        return
    id_item = itens[0]
    tags = canvas.gettags(id_item)
    tag_estado = None
    for t in tags:
        if t.startswith("q"):
            tag_estado = t
            break
    if tag_estado:
        estados[tag_estado].toggle_aceitacao()

def animar_token(token_id, origem, destino, callback_ao_finalizar, passo_atual=0, total_passos=30):
    """
    Anima o movimento de um 'token' e executa uma função de callback ao finalizar.
    """
    coords_origem = canvas.coords(origem.id_circulo)
    x_o, y_o = (coords_origem[0] + coords_origem[2]) / 2, (coords_origem[1] + coords_origem[3]) / 2
    
    coords_destino = canvas.coords(destino.id_circulo)
    x_d, y_d = (coords_destino[0] + coords_destino[2]) / 2, (coords_destino[1] + coords_destino[3]) / 2

    deslocamento_x = x_d - x_o
    deslocamento_y = y_d - y_o

    pos_x = x_o + (deslocamento_x * passo_atual) / total_passos
    pos_y = y_o + (deslocamento_y * passo_atual) / total_passos
    
    raio_token = 5
    canvas.coords(token_id, pos_x - raio_token, pos_y - raio_token, pos_x + raio_token, pos_y + raio_token)

    if passo_atual < total_passos:
        canvas.after(20, animar_token, token_id, origem, destino, callback_ao_finalizar, passo_atual + 1, total_passos)
    else:
        # Animação terminou
        canvas.delete(token_id) # Apaga o token
        # --- PARTE NOVA E IMPORTANTE ---
        if callback_ao_finalizar:
            callback_ao_finalizar() # Executa a função que foi passada como 'próximo passo'

def simular_palavra():
    """
    Função inicial chamada pelo botão. Prepara o ambiente e
    dá início ao primeiro passo da simulação animada.
    """
    palavra = input_entry.get()
    resultado.config(text="") # Limpa o resultado anterior

    # Encontra o estado inicial
    estado_atual = None
    for est in estados.values():
        if est.inicial:
            estado_atual = est
            break
    
    if not estado_atual:
        resultado.config(text="Erro: Nenhum estado inicial definido!", fg="orange")
        return
    
    # Inicia a simulação passo a passo
    simular_passo_a_passo(palavra, estado_atual)


def simular_passo_a_passo(palavra_restante, estado_atual):
    """
    Executa um passo da simulação. Anima a transição e agenda
    a si mesma para o próximo passo.
    """
    # CASO 1: A palavra terminou. Verificamos se o estado é de aceitação.
    if not palavra_restante:
        if estado_atual.aceitacao:
            resultado.config(text="Palavra aceita ✅", fg="green")
        else:
            resultado.config(text="Palavra rejeitada ❌", fg="red")
        return

    simbolo_atual = palavra_restante[0]
    proxima_palavra = palavra_restante[1:]
    
    # Procura a próxima transição
    transicao_encontrada = None
    for t in transicoes:
        if t.origem == estado_atual and t.simbolo == simbolo_atual:
            transicao_encontrada = t
            break
    
    # CASO 2: Não há transição para o símbolo. Palavra rejeitada.
    if not transicao_encontrada:
        resultado.config(text="Palavra rejeitada ❌ (transição não encontrada)", fg="red")
        return

    # CASO 3: Encontramos uma transição. Iniciamos a animação.
    estado_destino = transicao_encontrada.destino
    
    # Cria o "token" na posição do estado atual
    raio_token = 5
    token = canvas.create_oval(
        estado_atual.x - raio_token, estado_atual.y - raio_token,
        estado_atual.x + raio_token, estado_atual.y + raio_token,
        fill="red", outline="black"
    )
    
    # Define o que deve acontecer QUANDO a animação terminar:
    # Chamar esta mesma função para o resto da palavra e o novo estado.
    proximo_passo = lambda: simular_passo_a_passo(proxima_palavra, estado_destino)
    
    # Inicia a animação, passando a função "proximo_passo" como callback
    animar_token(token, estado_atual, estado_destino, proximo_passo)


# --- NOVO: Função para calcular o fecho-ε ---
def fecho_epsilon(estados_iniciais):
    """
    Retorna o fecho-ε de um conjunto de estados.
    (todos os estados alcançáveis a partir de epsilon-transições)
    """
    visitados = set(estados_iniciais)
    pilha = list(estados_iniciais)

    while pilha:
        estado = pilha.pop()
        for t in transicoes:
            if t.origem == estado and t.simbolo == "ε":
                if t.destino not in visitados:
                    visitados.add(t.destino)
                    pilha.append(t.destino)
    return visitados


# --- NOVO: simular AFNe --------------------------------------------------------------


def simular_palavra_afne():
    """
    Simula a palavra considerando AFNe (ε-transições e não-determinismo).
    """
    palavra = input_entry.get()
    resultado.config(text="")  # limpa resultado anterior

    # Estado(s) inicial(is)
    estados_iniciais = [e for e in estados.values() if e.inicial]
    if not estados_iniciais:
        resultado.config(text="Erro: Nenhum estado inicial definido!", fg="orange")
        return

    # --- NOVO: começa com o fecho-ε do inicial ---
    estados_atuais = fecho_epsilon(estados_iniciais)

    # Processar cada símbolo
    for simbolo in palavra:
        proximos_estados = set()
        for estado in estados_atuais:
            for t in transicoes:
                if t.origem == estado and t.simbolo == simbolo:
                    proximos_estados.add(t.destino)

        # --- NOVO: expandir fecho-ε dos próximos estados ---
        estados_atuais = fecho_epsilon(proximos_estados)

    # Verifica aceitação
    if any(e.aceitacao for e in estados_atuais):
        resultado.config(text="Palavra aceita ✅", fg="green")
    else:
        resultado.config(text="Palavra rejeitada ❌", fg="red")


#TESTE AFN--------------------------

def simular_palavra_afn():
    """
    Simula uma palavra em um AFN puro (sem ε-transições).
    Mantém todo o seu código original intacto.
    """
    palavra = input_entry.get()
    resultado.config(text="")  # limpa resultado anterior

    # Conjunto de estados iniciais
    estados_atuais = set()
    for est in estados.values():
        if est.inicial:
            estados_atuais.add(est)

    if not estados_atuais:
        resultado.config(text="Erro: Nenhum estado inicial definido!", fg="orange")
        return

    simular_passos_afn(palavra, estados_atuais)

def simular_passos_afn(palavra_restante, estados_atuais):
    """
    Executa um passo da simulação AFN.
    palavra_restante: string com os símbolos restantes
    estados_atuais: conjunto de objetos Estado
    """
    if not palavra_restante:
        # palavra terminou, verifica aceitação
        if any(e.aceitacao for e in estados_atuais):
            resultado.config(text="Palavra aceita ✅", fg="green")
        else:
            resultado.config(text="Palavra rejeitada ❌", fg="red")
        return

    simbolo_atual = palavra_restante[0]
    proxima_palavra = palavra_restante[1:]

    # Conjunto de próximos estados possíveis
    proximos_estados = set()
    for est in estados_atuais:
        for t in transicoes:
            if t.origem == est and t.simbolo == simbolo_atual:
                proximos_estados.add(t.destino)

    if not proximos_estados:
        resultado.config(text="Palavra rejeitada ❌ (transição não encontrada)", fg="red")
        return

    # Para animação, podemos apenas pegar um token do primeiro estado para o primeiro destino
    estado_origem = next(iter(estados_atuais))
    estado_destino = next(iter(proximos_estados))
    raio_token = 5
    token = canvas.create_oval(
        estado_origem.x - raio_token, estado_origem.y - raio_token,
        estado_origem.x + raio_token, estado_origem.y + raio_token,
        fill="red", outline="black"
    )

    # Callback continua para o próximo passo
    callback = lambda: simular_passos_afn(proxima_palavra, proximos_estados)

    animar_token(token, estado_origem, estado_destino, callback)




#-------------------------- mudei até aqui ------------------------------

# --- Janela ---
janela = tk.Tk()
janela.title("Mini-JFLAP em Python")
janela.geometry("800x700")

canvas = tk.Canvas(janela, bg="white", highlightthickness=1, highlightbackground="black")
canvas.pack(fill="both", expand=True, padx=10, pady=10)

canvas.bind("<ButtonPress-1>", iniciar_movimento)
canvas.bind("<B1-Motion>", arrastar_objeto)
canvas.bind("<ButtonRelease-1>", finalizar_arraste)
canvas.bind("<ButtonPress-3>", toggle_aceitacao_event)  # botão direito alterna aceitação

frame_botoes = tk.Frame(janela, bg="#f0f0f0")
frame_botoes.pack(fill="x", padx=10, pady=5)

botao_modo = tk.Button(frame_botoes, text="Modo Atual: Criar/Arrastar Estado", command=alternar_modo, width=30)
botao_modo.pack(side="left", padx=5)

instrucoes = tk.Label(frame_botoes, text="Clique para criar ou arrastar estados.", bg="#f0f0f0", font=("Arial", 10))
instrucoes.pack(side="left", padx=10)

# Campo para digitar símbolos/transições e palavras
input_entry = tk.Entry(janela, width=30)
input_entry.pack(pady=5)

botao_simular = tk.Button(janela, text="Simular Palavra", command=simular_palavra)
botao_simular.pack(pady=5)

resultado = tk.Label(janela, text="", font=("Arial", 12, "bold"))
resultado.pack(pady=5)

janela.mainloop()
