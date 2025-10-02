import tkinter as tk
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


class Transicao:
    def __init__(self, origem, destino, canvas, simbolo="ε"):
        self.origem = origem
        self.destino = destino
        self.canvas = canvas
        self.simbolo = simbolo

        self.id_linha = canvas.create_line(
            origem.x, origem.y, destino.x, destino.y,
            arrow=tk.LAST, fill="black", width=2, tags="transicao"
        )
        self.id_texto = canvas.create_text(
            (origem.x + destino.x) / 2,
            (origem.y + destino.y) / 2 - 10,
            text=simbolo, font=("Arial", 10, "italic"),
            tags="rotulo"
        )

    def atualizar_posicao(self):
        # Atualiza as coordenadas da linha (a seta)
        self.canvas.coords(self.id_linha, self.origem.x, self.origem.y, self.destino.x, self.destino.y)
        # Atualiza as coordenadas do texto (o símbolo)
        self.canvas.coords(self.id_texto, 
                           (self.origem.x + self.destino.x) / 2, 
                           (self.origem.y + self.destino.y) / 2 - 10)   


# --- Variáveis Globais ---
contador_estados = 0
estados = {}
transicoes = []
objeto_arrastado = {"id": None, "x_inicial": 0, "y_inicial": 0}
modo_atual = "arrastar"
transicao_info = {"origem": None}


# --- Funções ---
def iniciar_movimento(event):
    global modo_atual
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
    global transicao_info

    itens = canvas.find_closest(event.x, event.y)
    if not itens:
        transicao_info["origem"] = None
        return

    id_item = itens[0]
    tags = canvas.gettags(id_item)
    tag_estado = None
    for t in tags:
        if t.startswith("q"):
            tag_estado = t
            break

    if tag_estado is None:
        return

    estado = estados[tag_estado]

    if transicao_info["origem"] is None:
        transicao_info["origem"] = estado
        instrucoes.config(text=f"Origem: {estado.nome}. Agora clique no destino.")
    else:
        simbolo = input_entry.get() or "ε"
        nova_transicao = Transicao(transicao_info["origem"], estado, canvas, simbolo)
        transicoes.append(nova_transicao)
        instrucoes.config(text="Transição criada!")
        transicao_info["origem"] = None

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
    global modo_atual
    if modo_atual == "arrastar":
        modo_atual = "transicao"
        botao_modo.config(text="Modo Atual: Criar Transição")
        instrucoes.config(text="Clique no estado de origem e depois no destino. Digite símbolo no campo abaixo.")
    else:
        modo_atual = "arrastar"
        botao_modo.config(text="Modo Atual: Criar/Arrastar Estado")
        instrucoes.config(text="Clique para criar ou arrastar estados.")


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


def simular_palavra():
    palavra = input_entry.get()
    estado_atual = None
    for est in estados.values():
        if est.inicial:
            estado_atual = est
            break

    for simbolo in palavra:
        proximo = None
        for t in transicoes:
            if t.origem == estado_atual and t.simbolo == simbolo:
                proximo = t.destino
                break
        if not proximo:
            resultado.config(text="Palavra rejeitada ❌", fg="red")
            return
        estado_atual = proximo

    if estado_atual.aceitacao:
        resultado.config(text="Palavra aceita ✅", fg="green")
    else:
        resultado.config(text="Palavra rejeitada ❌", fg="red")


# --- Janela ---
janela = tk.Tk()
janela.title("Mini-JFLAP em Python")
janela.geometry("900x700")

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

