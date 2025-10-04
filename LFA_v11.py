#nessa versão adicionamos a compatibilidade de arquivos com jflap

import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, colorchooser
from PIL import Image, ImageTk
import json
import math
import xml.etree.ElementTree as ET # <-- NOVA IMPORTAÇÃO
from xml.dom import minidom        # <-- NOVA IMPORTAÇÃO

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
        self.simbolo_saida = "" # <-- NOVA LINHA
        self.id_circulo = canvas.create_oval(
            x - self.raio, y - self.raio, x + self.raio, y + self.raio,
            fill="lightblue", outline="black", width=2, tags=("estado", nome)
        )
        self.id_texto = canvas.create_text(
            x, y, text=nome, font=("Arial", 12, "bold"), tags=("texto", nome)
        )

    def mover(self, dx, dy):
        self.canvas.move(self.nome, dx, dy)
        self.x += dx
        self.y += dy

    def set_inicial(self):
        self.inicial = True
        self.canvas.create_line(
            self.x - 50, self.y, self.x - self.raio, self.y,
            arrow=tk.LAST, width=2, fill="green", tags=("seta_inicial", self.nome)
        )

    def set_aceitacao(self, eh_aceitacao):
        if self.aceitacao == eh_aceitacao: return
        self.aceitacao = eh_aceitacao
        for item in self.canvas.find_withtag("aceitacao"):
            if self.nome in self.canvas.gettags(item):
                self.canvas.delete(item)
        if self.aceitacao:
            self.canvas.create_oval(
                self.x - self.raio + 5, self.y - self.raio + 5,
                self.x + self.raio - 5, self.y + self.raio - 5,
                outline="black", width=2, tags=("aceitacao", self.nome)
            )

    def toggle_aceitacao(self):
        self.set_aceitacao(not self.aceitacao)

    def destruir(self):
        self.canvas.delete(self.nome)

    # Dentro da class Estado
    def atualizar_texto(self):
        """Atualiza o texto do estado no canvas para incluir a saída (se aplicável)."""
        texto_display = self.nome
        # Em modo Moore, se houver símbolo de saída, exibe "nome/saida"
        if tipo_automato_atual == "Moore" and self.simbolo_saida:
            texto_display = f"{self.nome}/{self.simbolo_saida}"
        self.canvas.itemconfig(self.id_texto, text=texto_display)

class Transicao:
    def __init__(self, origem, destino, canvas, simbolos_entrada="ε", simbolo_saida="", offset_x=0, offset_y=0):
        self.origem = origem
        self.destino = destino
        self.canvas = canvas
        if isinstance(simbolos_entrada, str):
            self.simbolos_entrada = [s.strip() for s in simbolos_entrada.split(',')]
        else:
            self.simbolos_entrada = simbolos_entrada
        self.simbolo_saida = simbolo_saida
        self.tag_unica = f"trans_{id(self)}"
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.is_loop = (self.origem == self.destino)
        self.atualizar_posicao()

    def _get_rotulo_texto(self):
        global tipo_automato_atual
        texto_entrada = ",".join(self.simbolos_entrada)
        if tipo_automato_atual == "Mealy" and self.simbolo_saida:
            return f"{texto_entrada}/{self.simbolo_saida}"
        return texto_entrada

    def atualizar_posicao(self):
        self.canvas.delete(self.tag_unica)
        if self.is_loop:
            self._desenhar_loop()
        else:
            self._desenhar_linha_reta()
        self.canvas.tag_raise("estado")
        self.canvas.tag_raise("texto")
        self.canvas.tag_raise("aceitacao")

    def _desenhar_linha_reta(self):
        x_o, y_o, x_d, y_d = self.origem.x, self.origem.y, self.destino.x, self.destino.y
        raio = self.origem.raio
        dist = math.dist((x_o, y_o), (x_d, y_d))
        if dist == 0: return
        vetor_x, vetor_y = (x_d - x_o) / dist, (y_d - y_o) / dist
        p_ini_x, p_ini_y = x_o + vetor_x * raio, y_o + vetor_y * raio
        p_fim_x, p_fim_y = x_d - vetor_x * raio, y_d - vetor_y * raio
        coords_linha = (p_ini_x + self.offset_x, p_ini_y + self.offset_y, p_fim_x + self.offset_x, p_fim_y + self.offset_y)
        coords_texto = (((x_o + x_d) / 2) + self.offset_x, ((y_o + y_d) / 2 - 15) + self.offset_y)
        self.canvas.create_line(coords_linha, arrow=tk.LAST, fill="black", width=2, tags=(self.tag_unica, "transicao"))
        self.canvas.create_text(coords_texto, text=self._get_rotulo_texto(), font=("Arial", 10, "italic"), tags=(self.tag_unica, "rotulo"))

    def _desenhar_loop(self):
        x, y = self.origem.x, self.origem.y
        raio_estado, raio_loop = self.origem.raio, 20
        bounding_box = (x - raio_loop, y - (2 * raio_estado), x + raio_loop, y)
        self.canvas.create_arc(bounding_box, start=210, extent=-240, style=tk.ARC, outline="black", width=2, tags=(self.tag_unica, "transicao"))
        angulo_final_rad = math.radians(-30)
        centro_arco_x, centro_arco_y = x, y - raio_estado
        ponta_x = centro_arco_x + raio_loop * math.cos(angulo_final_rad)
        ponta_y = centro_arco_y - raio_loop * math.sin(angulo_final_rad)
        ponta1, ponta2, ponta3 = (ponta_x, ponta_y), (ponta_x - 10, ponta_y - 2), (ponta_x - 2, ponta_y + 8)
        self.canvas.create_polygon(ponta1, ponta2, ponta3, fill="black", tags=(self.tag_unica, "transicao"))
        coords_texto = (x, y - raio_estado - raio_loop - 20)
        self.canvas.create_text(coords_texto, text=self._get_rotulo_texto(), font=("Arial", 10, "italic"), tags=(self.tag_unica, "rotulo"))

    def atualizar_simbolo(self, novo_rotulo_completo):
        partes = novo_rotulo_completo.split('/', 1)
        simbolos_entrada_str = partes[0].strip()
        self.simbolo_saida = partes[1].strip() if len(partes) > 1 else ""
        if not simbolos_entrada_str or simbolos_entrada_str.lower() == "ε":
            self.simbolos_entrada = ["ε"]
        else:
            self.simbolos_entrada = [s.strip() for s in simbolos_entrada_str.split(',')]
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
caminho_arquivo_atual = None
tipo_automato_atual = "AFNe"

# --- Funções "Detetive" ---
def encontrar_estado_clicado(event):
    itens_proximos = canvas.find_closest(event.x, event.y)
    if not itens_proximos: return None
    tags_do_item = canvas.gettags(itens_proximos[0])
    tags_de_sistema = {"estado", "texto", "seta_inicial", "aceitacao"}
    tag_nome = next((tag for tag in tags_do_item if tag not in tags_de_sistema), None)
    return estados.get(tag_nome)

# --- Funções de Interação e UI ---
def iniciar_movimento(event):
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
    estado_clicado = encontrar_estado_clicado(event)
    if estado_clicado:
        dist = math.dist((event.x, event.y), (estado_clicado.x, estado_clicado.y))
        if dist <= estado_clicado.raio:
            objeto_arrastado["id"] = estado_clicado
            objeto_arrastado["x_inicial"], objeto_arrastado["y_inicial"] = event.x, event.y
            return
    criar_novo_estado(event.x, event.y)

def gerenciar_clique_transicao(event):
    global transicao_info
    estado_clicado = encontrar_estado_clicado(event)
    if not estado_clicado:
        if transicao_info["origem"]:
            canvas.itemconfig(transicao_info["origem"].id_circulo, fill="lightblue")
        transicao_info["origem"] = None
        status_acao.config(text="Ação cancelada. Clique no estado de origem.")
        return
    if transicao_info["origem"] is None:
        transicao_info["origem"] = estado_clicado
        canvas.itemconfig(estado_clicado.id_circulo, fill="yellow")
        status_acao.config(text=f"Origem: {estado_clicado.nome}. Clique no destino.")
    else:
        estado_origem = transicao_info["origem"]
        estado_destino = estado_clicado
        transicao_gemea = next((t for t in transicoes if t.origem == estado_destino and t.destino == estado_origem), None)
        nova_transicao = Transicao(estado_origem, estado_destino, canvas)
        transicoes.append(nova_transicao)
        if transicao_gemea:
            dist = math.dist((estado_origem.x, estado_origem.y), (estado_destino.x, estado_destino.y))
            if dist == 0: dist = 1
            vetor_x, vetor_y = (estado_destino.x - estado_origem.x) / dist, (estado_destino.y - estado_origem.y) / dist
            vetor_perp_x, vetor_perp_y = -vetor_y, vetor_x
            offset_dist = 15 # Distância do desvio
            nova_transicao.offset_x, nova_transicao.offset_y = vetor_perp_x * offset_dist, vetor_perp_y * offset_dist
            nova_transicao.atualizar_posicao()
            transicao_gemea.offset_x, transicao_gemea.offset_y = -vetor_perp_x * offset_dist, -vetor_perp_y * offset_dist
            transicao_gemea.atualizar_posicao()
        canvas.itemconfig(estado_origem.id_circulo, fill="lightblue")
        transicao_info["origem"] = None
        status_acao.config(text="Transição criada! Clique nela para editar o símbolo.")

def editar_rotulo_transicao(id_item_clicado):
    """
    Abre uma caixa de diálogo CONTEXTUAL para editar o símbolo da transição,
    aplicando as regras do tipo de autômato atual.
    """
    tags_do_item = canvas.gettags(id_item_clicado)
    tag_alvo = next((tag for tag in tags_do_item if tag.startswith("trans_")), None) # Identifica a transição
    if not tag_alvo: return
    transicao_alvo = next((t for t in transicoes if t.tag_unica == tag_alvo), None) # Encontra o objeto Transicao
    if not transicao_alvo: return

    # --- LÓGICA CONTEXTUAL COMPLETA ---
    # Se o tipo for AFD, AFN ou AFNe, usamos a mesma caixa de diálogo
    if tipo_automato_atual in ["AFD", "AFN", "AFNe", "Moore"]:
        valor_inicial = ",".join(transicao_alvo.simbolos_entrada)
        novo_rotulo = simpledialog.askstring(
            f"Editar Símbolos ({tipo_automato_atual})",
            "Digite o(s) símbolo(s) de entrada, separados por vírgula:",
            initialvalue=valor_inicial
        )
        
        if novo_rotulo is not None:
            # Pega a nova lista de símbolos que o usuário digitou
            simbolos_novos = [s.strip() for s in novo_rotulo.split(',') if s.strip()]
            if not simbolos_novos: simbolos_novos = ["ε"]

            # === INÍCIO DO CHECKLIST DE REGRAS ===

            # REGRA 1: Proibir transições épsilon para AFD e AFN
            if tipo_automato_atual in ["AFD", "AFN"] and "ε" in simbolos_novos:
                messagebox.showerror(f"Regra de {tipo_automato_atual} Violada", f"Um {tipo_automato_atual} não pode conter transições épsilon (ε).")
                return # Aborta a edição

            # REGRA 2: Proibir não-determinismo APENAS para AFD
            if tipo_automato_atual == "AFD":
                for simbolo in simbolos_novos:
                    for outra_t in transicoes:
                        # Pula a verificação da própria transição que estamos editando
                        if outra_t == transicao_alvo:
                            continue
                        # Se encontrar outra transição que sai da mesma origem e usa o mesmo símbolo, é um erro.
                        if outra_t.origem == transicao_alvo.origem and simbolo in outra_t.simbolos_entrada:
                            messagebox.showerror("Regra de AFD Violada", 
                                f"Não-determinismo detectado!\nO estado '{transicao_alvo.origem.nome}' já tem uma transição para o símbolo '{simbolo}'.")
                            return # Aborta a edição

            # === FIM DO CHECKLIST DE REGRAS ===
            
            # Se passou por todas as regras, a atualização é permitida
            transicao_alvo.atualizar_simbolo(novo_rotulo)

    # Se o tipo for Mealy, usamos a outra caixa de diálogo
    elif tipo_automato_atual == "Mealy":
        valor_inicial = transicao_alvo._get_rotulo_texto()
        novo_rotulo_completo = simpledialog.askstring(
            "Editar Transição (Mealy)",
            "Formato: entrada / saida (ex: a/1)",
            initialvalue=valor_inicial
        )
        if novo_rotulo_completo is not None:
            transicao_alvo.atualizar_simbolo(novo_rotulo_completo)

def gerenciar_clique_apagar(event):
    """Gerencia cliques no modo apagar, delegando a tarefa para a função apropriada."""
    # Tenta apagar um estado primeiro
    estado_clicado = encontrar_estado_clicado(event)
    if estado_clicado:
        apagar_estado(estado_clicado)
        return

    # Se não clicou em um estado, tenta apagar uma transição
    itens_proximos = canvas.find_closest(event.x, event.y)
    if not itens_proximos: return
    id_item_clicado = itens_proximos[0]
    tags = canvas.gettags(id_item_clicado)
    
    tag_alvo = next((t for t in tags if t.startswith("trans_")), None)
    if tag_alvo:
        transicao_para_apagar = next((t for t in transicoes if t.tag_unica == tag_alvo), None)
        if transicao_para_apagar:
            transicao_para_apagar.destruir()
            transicoes.remove(transicao_para_apagar)
            status_acao.config(text="Transição apagada com sucesso.")

def arrastar_objeto(event):
    if objeto_arrastado["id"]:
        estado = objeto_arrastado["id"]
        dx, dy = event.x - objeto_arrastado["x_inicial"], event.y - objeto_arrastado["y_inicial"]
        estado.mover(dx, dy)
        objeto_arrastado["x_inicial"], objeto_arrastado["y_inicial"] = event.x, event.y
        atualizar_transicoes_conectadas(estado)

def finalizar_arraste(event):
    objeto_arrastado["id"] = None

def criar_novo_estado(x, y):
    global contador_estados
    nome_estado = f"q{contador_estados}"
    estado = Estado(nome_estado, x, y, canvas)
    estados[nome_estado] = estado
    if not any(est.inicial for est in estados.values() if est != estado):
        estado.set_inicial()
    contador_estados += 1

def toggle_aceitacao_event(event):
    # Se estamos no meio da criação de uma transição, ignora o clique duplo
    # Impede a ação se estivermos no modo Mealy
    if tipo_automato_atual == "Mealy":
        return
    
    estado_clicado = encontrar_estado_clicado(event)
    if estado_clicado:
        estado_clicado.toggle_aceitacao()

def atualizar_transicoes_conectadas(estado_movido):
    for transicao in transicoes:
        if transicao.origem == estado_movido or transicao.destino == estado_movido:
            transicao.atualizar_posicao()

def mostrar_menu_contexto(event):
    """Exibe o menu de contexto apropriado para o modo e o item clicado."""
    estado_clicado = encontrar_estado_clicado(event)
    
    if estado_clicado:
        menu_contexto = tk.Menu(janela, tearoff=0)
        
        # --- LÓGICA CONTEXTUAL ---
        # Só adiciona a opção de "Aceitação" se NÃO estivermos no modo Mealy
        if tipo_automato_atual not in ["Mealy","Moore"]:
            menu_contexto.add_command(
                label="Marcar/Desmarcar como Aceitação", command=estado_clicado.toggle_aceitacao
            )

        # --- NOVIDADE AQUI ---
        # Opção de Saída do Estado (apenas para Moore)
        if tipo_automato_atual == "Moore":
            menu_contexto.add_command(label="Definir Saída do Estado...", command=lambda: definir_saida_estado(estado_clicado))
        
        # As outras opções aparecem em todos os modos
        menu_contexto.add_command(
            label="Renomear Estado...",
            command=lambda: renomear_estado(estado_clicado)
        )
        menu_contexto.add_command(
            label="Alterar Cor...",
            command=lambda: mudar_cor_estado(estado_clicado)
        )
        menu_contexto.add_separator()
        menu_contexto.add_command(
            label="Apagar Estado",
            command=lambda: apagar_estado(estado_clicado)
        )
        
        menu_contexto.post(event.x_root, event.y_root)

def atualizar_status_modo():
    """Atualiza o texto do painel de status da esquerda com o modo e tipo atuais."""
    # Capitalize() deixa a primeira letra maiúscula (ex: 'arrastar' -> 'Arrastar')
    texto_modo = modo_atual.capitalize().replace("Arrastar", "Criar/Arrastar")
    status_modo.config(text=f"Tipo: {tipo_automato_atual}  |  Modo: {texto_modo}")

def mudar_cor_estado(estado):
    nova_cor = colorchooser.askcolor(title=f"Escolha a cor para {estado.nome}")
    if nova_cor and nova_cor[1]:
        canvas.itemconfig(estado.id_circulo, fill=nova_cor[1])

def renomear_estado(estado):
    novo_nome = simpledialog.askstring("Renomear Estado", f"Digite o novo nome para '{estado.nome}':", initialvalue=estado.nome)
    if novo_nome and novo_nome not in estados:
        nome_antigo = estado.nome
        ids_componentes = canvas.find_withtag(nome_antigo)
        for item_id in ids_componentes:
            tags_atuais = list(canvas.gettags(item_id))
            novas_tags = [novo_nome if t == nome_antigo else t for t in tags_atuais]
            canvas.itemconfig(item_id, tags=tuple(novas_tags))
        canvas.itemconfig(estado.id_texto, text=novo_nome)
        estado.nome = novo_nome
        estados[novo_nome] = estados.pop(nome_antigo)
    elif novo_nome:
        messagebox.showwarning("Erro", "O nome inserido já existe ou é inválido.")

def apagar_estado(estado_para_apagar):
    """
    Função dedicada para apagar um estado e suas transições,
    com diálogo de confirmação.
    """
    if not estado_para_apagar: return

    confirmar = messagebox.askyesno(
        "Apagar Estado",
        f"Tem certeza que deseja apagar o estado '{estado_para_apagar.nome}'?\n"
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
        nome_estado = estado_para_apagar.nome
        estado_para_apagar.destruir()
        del estados[nome_estado]
        status_acao.config(text=f"Estado {nome_estado} apagado.")
    else:
        status_acao.config(text="Ação de apagar cancelada.")

def cancelar_criacao_transicao(event):
    """
    Cancela a criação de uma transição que está em andamento.
    Chamada pelo clique do botão do meio do mouse.
    """
    global transicao_info
    # Verifica se há um estado de origem já selecionado
    if transicao_info["origem"]:
        # Restaura a cor original do estado de origem
        canvas.itemconfig(transicao_info["origem"].id_circulo, fill="lightblue")
        
        # Limpa a variável de controle, efetivamente cancelando a ação
        transicao_info["origem"] = None
        
        # Atualiza a interface para informar o usuário
        status_acao.config(text="Criação de transição cancelada.")
        print("Criação de transição cancelada.")

def gerenciar_atalhos_teclado(event):
    """Gerencia os atalhos de teclado para ações rápidas."""
    # event.keysym nos dá o nome da tecla que foi pressionada
    if event.keysym == "F1":
        ativar_modo_arrastar()
    elif event.keysym == "F2":
        ativar_modo_transicao()
    elif event.keysym == "F3":
        ativar_modo_apagar()

def gerenciar_clique_duplo(event):
    """
    Gerencia o evento de clique duplo. Cria um laço se estiver no modo de transição,
    ou alterna o estado de aceitação nos outros modos.
    """
    # Se estamos no modo de transição, a prioridade é criar um laço
    if modo_atual == "transicao":
        estado_clicado = encontrar_estado_clicado(event)
        if estado_clicado:
            # Cria uma nova transição onde a origem e o destino são o mesmo estado
            nova_transicao = Transicao(estado_clicado, estado_clicado, canvas)
            transicoes.append(nova_transicao)
            
            # Limpa a seleção de origem, caso o usuário tenha clicado em outro estado antes
            if transicao_info["origem"]:
                canvas.itemconfig(transicao_info["origem"].id_circulo, fill="lightblue")
                transicao_info["origem"] = None

            status_acao.config(text=f"Laço criado para o estado {estado_clicado.nome}.")
            
    # Para qualquer outro modo, o clique duplo alterna o estado de aceitação
    else:
        toggle_aceitacao_event(event)



# --- Funções de Modo e Tipo ---
def ativar_modo_arrastar():
    global modo_atual
    modo_atual = "arrastar"
    atualizar_status_modo() # <-- USA A NOVA FUNÇÃO
    print("Modo alterado para: arrastar")

def ativar_modo_transicao():
    global modo_atual
    modo_atual = "transicao"
    atualizar_status_modo() # <-- USA A NOVA FUNÇÃO
    print("Modo alterado para: transicao")

def ativar_modo_apagar():
    global modo_atual
    modo_atual = "apagar"
    atualizar_status_modo() # <-- USA A NOVA FUNÇÃO
    print("Modo alterado para: apagar")

def definir_tipo_automato(novo_tipo):
    global tipo_automato_atual
    confirmar = messagebox.askyesno(
        "Mudar Tipo de Autômato",
        f"Você tem certeza que deseja mudar para {novo_tipo}?\n"
        "Todo o trabalho não salvo no autômato atual será perdido."
    )
    if confirmar:
        novo_automato()
        tipo_automato_atual = novo_tipo
        atualizar_status_modo() # <-- USA A NOVA FUNÇÃO
        status_acao.config(text=f"Tipo alterado para {novo_tipo}.") # Mensagem de ação
        print(f"Tipo de autômato definido para: {tipo_automato_atual}")

def definir_saida_estado(estado):
    """Abre uma caixa de diálogo para definir o símbolo de saída de um estado (Moore)."""
    nova_saida = simpledialog.askstring(
        "Definir Saída de Estado (Moore)",
        f"Digite o símbolo de saída para o estado '{estado.nome}':",
        initialvalue=estado.simbolo_saida
    )
    if nova_saida is not None: # Permite definir uma saída vazia
        estado.simbolo_saida = nova_saida
        estado.atualizar_texto() # Chama o novo método para atualizar a tela



# --- Funções de Animação e Simulação ---
def animar_token(token_id, origem, destino, callback_ao_finalizar, passo_atual=0, total_passos=30):
    coords_origem = canvas.coords(origem.id_circulo)
    x_o, y_o = (coords_origem[0] + coords_origem[2]) / 2, (coords_origem[1] + coords_origem[3]) / 2
    coords_destino = canvas.coords(destino.id_circulo)
    x_d, y_d = (coords_destino[0] + coords_destino[2]) / 2, (coords_destino[1] + coords_destino[3]) / 2
    deslocamento_x, deslocamento_y = x_d - x_o, y_d - y_o
    pos_x = x_o + (deslocamento_x * passo_atual) / total_passos
    pos_y = y_o + (deslocamento_y * passo_atual) / total_passos
    raio_token = 5
    canvas.coords(token_id, pos_x - raio_token, pos_y - raio_token, pos_x + raio_token, pos_y + raio_token)
    if passo_atual < total_passos:
        canvas.after(20, animar_token, token_id, origem, destino, callback_ao_finalizar, passo_atual + 1, total_passos)
    else:
        canvas.delete(token_id)
        if callback_ao_finalizar:
            callback_ao_finalizar()

def calcular_fecho_epsilon(estados_origem):
    fecho = set(estados_origem)
    pilha = list(estados_origem)
    while pilha:
        estado_atual = pilha.pop()
        for t in transicoes:
            if t.origem == estado_atual and "ε" in t.simbolos_entrada:
                if t.destino not in fecho:
                    fecho.add(t.destino)
                    pilha.append(t.destino)
    return fecho

def validar_automato_como_AFD():
    for estado in estados.values():
        simbolos_vistos = set()
        for t in transicoes:
            if t.origem == estado:
                if "ε" in t.simbolos_entrada:
                    return (False, f"O estado '{estado.nome}' possui uma transição épsilon (ε).")
                interseccao = simbolos_vistos.intersection(t.simbolos_entrada)
                if interseccao:
                    return (False, f"Não-determinismo no estado '{estado.nome}' para o símbolo '{list(interseccao)[0]}'.")
                simbolos_vistos.update(t.simbolos_entrada)
    return (True, "")

def simular_palavra():
    global tipo_automato_atual
    palavra = input_entry.get()
    resultado.config(text="Simulando...")
    sequencia_saida.config(text="Saída: ")
    
    estado_inicial = next((est for est in estados.values() if est.inicial), None)
    if not estado_inicial:
        resultado.config(text="Erro: Nenhum estado inicial definido!", fg="orange")
        return
        
    if tipo_automato_atual == "AFD":
        is_valido, msg_erro = validar_automato_como_AFD()
        if not is_valido:
            messagebox.showerror("Autômato Inválido", f"Este não é um AFD válido.\n\nMotivo: {msg_erro}")
            resultado.config(text="")
            return
        simular_passo_a_passo_AFD(palavra, estado_inicial)

    elif tipo_automato_atual in ["AFNe", "AFN"]: # <-- AGRUPAMOS OS DOIS AQUI
        estados_atuais = calcular_fecho_epsilon({estado_inicial})
        simular_passo_a_passo_AFNe(palavra, estados_atuais, "")
        
    elif tipo_automato_atual == "Mealy":
        # Inicia o motor de simulação de Mealy
        simular_passo_a_passo_Mealy(palavra, estado_inicial, "")

    elif tipo_automato_atual == "Moore":
        # Lógica inicial para Moore: a primeira saída é a do estado inicial
        saida_inicial = estado_inicial.simbolo_saida
        sequencia_saida.config(text=f"Saída: {saida_inicial}")
        simular_passo_a_passo_Moore(palavra, estado_inicial, saida_inicial)

def simular_passo_a_passo_AFD(palavra_restante, estado_atual):
    canvas.itemconfig(estado_atual.id_circulo, outline="blue", width=3)
    if not palavra_restante:
        aceita = estado_atual.aceitacao
        resultado.config(text="Palavra aceita ✅" if aceita else "Palavra rejeitada ❌", fg="green" if aceita else "red")
        janela.after(2000, lambda: canvas.itemconfig(estado_atual.id_circulo, outline="black", width=2))
        return
    simbolo_atual, proxima_palavra = palavra_restante[0], palavra_restante[1:]
    transicao_encontrada = next((t for t in transicoes if t.origem == estado_atual and simbolo_atual in t.simbolos_entrada), None)
    if not transicao_encontrada:
        resultado.config(text=f"Rejeitada ❌ (preso no símbolo '{simbolo_atual}')", fg="red")
        janela.after(2000, lambda: canvas.itemconfig(estado_atual.id_circulo, outline="black", width=2))
        return
    estado_destino = transicao_encontrada.destino
    raio_token = 5
    token = canvas.create_oval(estado_atual.x - raio_token, estado_atual.y - raio_token, estado_atual.x + raio_token, estado_atual.y + raio_token, fill="red", outline="black")
    proximo_passo = lambda: simular_passo_a_passo_AFD(proxima_palavra, estado_destino)
    animar_token(token, estado_atual, estado_destino, proximo_passo)

def simular_passo_a_passo_AFNe(palavra_restante, estados_atuais, saida_acumulada):
    for estado in estados.values(): canvas.itemconfig(estado.id_circulo, outline="black", width=2)
    for estado in estados_atuais: canvas.itemconfig(estado.id_circulo, outline="blue", width=3)
    if not palavra_restante:
        aceita = any(estado.aceitacao for estado in estados_atuais)
        resultado.config(text="Palavra aceita ✅" if aceita else "Palavra rejeitada ❌", fg="green" if aceita else "red")
        sequencia_saida.config(text=f"Saída Final: {saida_acumulada}")
        janela.after(1000, lambda: [canvas.itemconfig(e.id_circulo, outline="black", width=2) for e in estados.values()])
        return
    simbolo_atual, proxima_palavra = palavra_restante[0], palavra_restante[1:]
    proximos_estados_brutos, saida_passo = set(), ""
    transicoes_usadas = []
    for estado_origem in estados_atuais:
        for t in transicoes:
            if t.origem == estado_origem and simbolo_atual in t.simbolos_entrada:
                proximos_estados_brutos.add(t.destino)
                if t.simbolo_saida: saida_passo += t.simbolo_saida
                if t not in transicoes_usadas: transicoes_usadas.append(t)
    if not proximos_estados_brutos:
        resultado.config(text=f"Rejeitada ❌ (preso no símbolo '{simbolo_atual}')", fg="red")
        janela.after(1000, lambda: [canvas.itemconfig(e.id_circulo, outline="black", width=2) for e in estados.values()])
        return
    proximos_estados_finais = calcular_fecho_epsilon(proximos_estados_brutos)
    nova_saida_acumulada = saida_acumulada + saida_passo
    for t in transicoes_usadas: canvas.itemconfig(t.tag_unica, fill="red")
    nomes_atuais = ", ".join(sorted([e.nome for e in proximos_estados_finais]))
    status_acao.config(text=f"Lendo '{simbolo_atual}'... Próximos estados: [{nomes_atuais}]")
    sequencia_saida.config(text=f"Saída: {nova_saida_acumulada}")
    def ir_para_proximo_passo():
        for t in transicoes_usadas: canvas.itemconfig(t.tag_unica, fill="black")
        simular_passo_a_passo_AFNe(proxima_palavra, proximos_estados_finais, nova_saida_acumulada)
    janela.after(700, ir_para_proximo_passo)

def simular_passo_a_passo_Mealy(palavra_restante, estado_atual, saida_acumulada):
    """
    Motor de simulação para Máquinas de Mealy, com realce de estados e transições.
    (Versão sem o token animado).
    """
    # Limpa realces anteriores e realça o estado atual
    for est in estados.values(): canvas.itemconfig(est.id_circulo, outline="black", width=2)
    canvas.itemconfig(estado_atual.id_circulo, outline="blue", width=3)

    # Função de limpeza robusta para o final da simulação
    def limpar_realces_finais():
        for est in estados.values():
            canvas.itemconfig(est.id_circulo, outline="black", width=2)

    # Fim da palavra, a simulação termina
    if not palavra_restante:
        resultado.config(text="Simulação concluída!", fg="blue")
        sequencia_saida.config(text=f"Saída Final: {saida_acumulada}")
        janela.after(2000, limpar_realces_finais) # Limpa TUDO após 2s
        return

    simbolo_atual = palavra_restante[0]
    proxima_palavra = palavra_restante[1:]
    
    transicao_encontrada = next((t for t in transicoes if t.origem == estado_atual and simbolo_atual in t.simbolos_entrada), None)
            
    if not transicao_encontrada:
        resultado.config(text=f"Rejeitada ❌ (transição inválida para '{simbolo_atual}')", fg="red")
        janela.after(2000, limpar_realces_finais) # Limpa TUDO após 2s
        return

    estado_destino = transicao_encontrada.destino
    nova_saida_acumulada = saida_acumulada + transicao_encontrada.simbolo_saida
    
    # Realça a transição que está sendo usada
    canvas.itemconfig(transicao_encontrada.tag_unica, fill="red")
    
    # Atualiza a UI
    status_acao.config(text=f"Lendo '{simbolo_atual}', gerando '{transicao_encontrada.simbolo_saida}'...")
    sequencia_saida.config(text=f"Saída: {nova_saida_acumulada}")
    
    def ir_para_proximo_passo():
        # Restaura a cor da transição
        canvas.itemconfig(transicao_encontrada.tag_unica, fill="black")
        # Chama a si mesma para o próximo passo
        simular_passo_a_passo_Mealy(proxima_palavra, estado_destino, nova_saida_acumulada)

    # Pausa para o usuário ver o que aconteceu antes do próximo passo
    janela.after(800, ir_para_proximo_passo)

def simular_passo_a_passo_Moore(palavra_restante, estado_atual, saida_acumulada):
    """Motor de simulação para Moore, com realce de estados e transições (SEM token)."""
    # Limpa realces anteriores e realça o estado atual em azul
    for est in estados.values():
        canvas.itemconfig(est.id_circulo, outline="black", width=2)
    canvas.itemconfig(estado_atual.id_circulo, outline="blue", width=3)
    status_acao.config(text=f"No estado '{estado_atual.nome}', gerando saída '{estado_atual.simbolo_saida}'")

    # Função de limpeza robusta para garantir que tudo volte ao normal no final
    def limpar_realces_finais():
        for est in estados.values():
            canvas.itemconfig(est.id_circulo, outline="black", width=2)

    # Se a palavra acabou, finaliza a simulação
    if not palavra_restante:
        resultado.config(text="Simulação concluída!", fg="blue")
        sequencia_saida.config(text=f"Saída Final: {saida_acumulada}")
        janela.after(2000, limpar_realces_finais)
        return

    simbolo_atual = palavra_restante[0]
    proxima_palavra = palavra_restante[1:]

    transicao_encontrada = next((t for t in transicoes if t.origem == estado_atual and simbolo_atual in t.simbolos_entrada), None)

    if not transicao_encontrada:
        resultado.config(text=f"Rejeitada ❌ (transição inválida para '{simbolo_atual}')", fg="red")
        janela.after(2000, limpar_realces_finais)
        return

    # Realça em vermelho a transição que será usada
    canvas.itemconfig(transicao_encontrada.tag_unica, fill="red")
    
    estado_destino = transicao_encontrada.destino
    nova_saida_acumulada = saida_acumulada + estado_destino.simbolo_saida
    
    # Prepara a chamada para o próximo passo
    def ir_para_proximo_passo():
        # Restaura a cor da transição
        canvas.itemconfig(transicao_encontrada.tag_unica, fill="black")
        # Chama a si mesma recursivamente
        simular_passo_a_passo_Moore(proxima_palavra, estado_destino, nova_saida_acumulada)

    # Usa janela.after para criar uma pausa, em vez de animar o token
    janela.after(800, ir_para_proximo_passo)



# --- Funções de Arquivo ---
def novo_automato():
    global estados, transicoes, contador_estados, caminho_arquivo_atual
    canvas.delete("all")
    estados, transicoes = {}, []
    contador_estados = 0
    caminho_arquivo_atual = None
    resultado.config(text="")
    status_acao.config(text="Novo autômato criado. Clique no canvas para começar.")

def _salvar_dados_no_arquivo(caminho):
    dados = {
        "estados": [{"nome": e.nome, "x": e.x, "y": e.y, "inicial": e.inicial, "aceitacao": e.aceitacao, "simbolo_saida": e.simbolo_saida} for e in estados.values()],
        "transicoes": [{"origem": t.origem.nome, "destino": t.destino.nome, "simbolos_entrada": t.simbolos_entrada,
                        "simbolo_saida": t.simbolo_saida, "offset_x": t.offset_x, "offset_y": t.offset_y} for t in transicoes]
    }
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)
    status_acao.config(text=f"Autômato salvo em {caminho.split('/')[-1]}")

def salvar():
    if caminho_arquivo_atual:
        _salvar_dados_no_arquivo(caminho_arquivo_atual)
    else:
        salvar_como()

def salvar_como():
    global caminho_arquivo_atual
    arquivo = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("JFLAP files", "*.jff")])
    if arquivo:
        caminho_arquivo_atual = arquivo
        _salvar_dados_no_arquivo(caminho_arquivo_atual)
    if caminho_arquivo_atual.lower().endswith('.jff'):
            exportar_para_jflap_xml(caminho_arquivo_atual)
    else: 
            _salvar_dados_no_arquivo(caminho_arquivo_atual)

#--------------------------------------------------------

def exportar_para_jflap_xml(caminho_arquivo):
    
    raiz = ET.Element('structure')
    ET.SubElement(raiz, 'type').text = "fa"
    automato = ET.SubElement(raiz, 'automaton')
    estado_para_id = {estado: i for i, estado in enumerate(estados.values())}
    for i, estado in enumerate(estados.values()):
        e_xml = ET.SubElement(automato, 'state', id=str(i), name=estado.nome)
        ET.SubElement(e_xml, 'x').text = str(float(estado.x))
        ET.SubElement(e_xml, 'y').text = str(float(estado.y))
        
        if estado.inicial:
            ET.SubElement(e_xml, 'initial')
        if estado.aceitacao:
            ET.SubElement(e_xml, 'final')

    for transicao in transicoes:
        t_xml = ET.SubElement(automato, 'transition')
        
        origem_id = estado_para_id.get(transicao.origem)
        destino_id = estado_para_id.get(transicao.destino)
        
        if origem_id is None or destino_id is None: continue 
        
        ET.SubElement(t_xml, 'from').text = str(origem_id)
        ET.SubElement(t_xml, 'to').text = str(destino_id)
        
        simbolo = transicao.simbolos_entrada[0] 
        
        read_tag = ET.SubElement(t_xml, 'read')
        if simbolo.lower() != "ε":
             read_tag.text = simbolo

    xml_string = ET.tostring(raiz, encoding='utf-8')
    reparsed = minidom.parseString(xml_string) 
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(reparsed.toprettyxml(indent="  "))
  
    status_acao.config(text=f"Exportado para JFLAP XML (JFF) em: {caminho_arquivo.split('/')[-1]}")
#----------------------------------------------------

def atalho_salvar(event):
    """Função adaptadora para o atalho Ctrl+S. Ignora o evento e chama a função salvar."""
    # O 'event' é recebido mas não precisamos usá-lo aqui.
    salvar()
    print("Atalho Ctrl+S acionado: arquivo salvo.")

def abrir_automato():
    global caminho_arquivo_atual
    
    # Aumentei a lista de filtros para ser mais robusta
    arquivo = filedialog.askopenfilename(
        filetypes=[
            ("Todos os Arquivos de Autômato", "*.jff;*.json"),
            ("JFLAP files", "*.jff"),
            ("JSON files", "*.json")
        ]
    )
    
    if not arquivo: return
    
    caminho_arquivo_atual = arquivo
    
    # --- NOVO FLUXO: Decide O QUE chamar com base na extensão ---
    if caminho_arquivo_atual.lower().endswith('.jff'):
        # CHAMA O IMPORTADOR XML
        if importar_de_jflap_xml(caminho_arquivo_atual):
            status_acao.config(text=f"Autômato JFLAP carregado de {arquivo.split('/')[-1]}")
    
    elif caminho_arquivo_atual.lower().endswith('.json'):
        # CHAMA O IMPORTADOR JSON
        _carregar_dados_json(caminho_arquivo_atual)
        status_acao.config(text=f"Autômato JSON carregado de {arquivo.split('/')[-1]}")

    else:
        messagebox.showwarning("Erro de Formato", "Formato de arquivo não reconhecido. Tente .jff ou .json.")
    corrigir_desvios_carregados()
    status_acao.config(text=f"Autômato carregado de {arquivo.split('/')[-1]}")

#-----------------------------------------------

def _carregar_dados_json(arquivo):
    global estados, transicoes, contador_estados, caminho_arquivo_atual
    
    # O conteúdo que estava dentro de 'abrir_automato' para JSON deve vir para cá
    with open(arquivo, "r", encoding="utf-8") as f:
        dados = json.load(f)
    
    # Limpa e carrega como antes
    novo_automato() 
    
    # Recria Estados (como você já faz)
    for e_data in dados["estados"]:
        estado = Estado(e_data["nome"], e_data["x"], e_data["y"], canvas)
        estados[e_data["nome"]] = estado
        if e_data.get("inicial"): estado.set_inicial()
        if e_data.get("aceitacao"): estado.set_aceitacao(True)
    
    # Atualiza o contador (como você já faz)
    if estados:
        maior_num_estado = max([int(nome.replace('q', '')) for nome in estados.keys() if nome.startswith('q') and nome[1:].isdigit()]) + 1
        contador_estados = maior_num_estado
        
    # Recria Transições (como você já faz)
    for t_data in dados["transicoes"]:
        origem, destino = estados.get(t_data["origem"]), estados.get(t_data["destino"])
        if not origem or not destino: continue
        transicoes.append(Transicao(origem, destino, canvas, 
                                    t_data.get("simbolos_entrada", ["ε"]), 
                                    t_data.get("simbolo_saida", ""), 
                                    t_data.get("offset_x", 0), 
                                    t_data.get("offset_y", 0)))
        
    corrigir_desvios_carregados()

#--------------------------------------------------------------

#--------------------------------------------------------------------------
def importar_de_jflap_xml(caminho_arquivo):
    global estados, transicoes, contador_estados
    
    try:
        tree = ET.parse(caminho_arquivo)
        raiz = tree.getroot()
        
        # Limpa o autômato atual
        novo_automato() 

        # 1. Mapeia ID (do XML) para Nome de Estado (para conexão de transição)
        mapa_id_nome = {}
        
        # 2. Processa os Estados
        for e_xml in raiz.findall('./automaton/state'):
            e_id = e_xml.get('id')
            nome = e_xml.get('name')
            
            x = int(float(e_xml.find('x').text)) if e_xml.find('x') is not None else 50
            y = int(float(e_xml.find('y').text)) if e_xml.find('y') is not None else 50
            
            estado = Estado(nome, x, y, canvas) 
            estados[nome] = estado
            mapa_id_nome[e_id] = nome 
            
            if e_xml.find('initial') is not None:
                estado.set_inicial()
            if e_xml.find('final') is not None:
                estado.set_aceitacao(True)
                
        # Atualiza o contador de estados
        if estados:
            max_num = max([int(n.replace('q', '')) for n in estados.keys() if n.startswith('q') and n[1:].isdigit()])
            contador_estados = max_num + 1

        # 3. Processa as Transições
        for t_xml in raiz.findall('./automaton/transition'):
            origem_id = t_xml.find('from').text
            destino_id = t_xml.find('to').text
            
            origem_nome = mapa_id_nome.get(origem_id)
            destino_nome = mapa_id_nome.get(destino_id)
            
            origem = estados.get(origem_nome)
            destino = estados.get(destino_nome)
            
            # Símbolo: se a tag <read> tiver texto, é o símbolo. Senão, é epsilon ('ε').
            read_element = t_xml.find('read')
            simbolo = read_element.text if read_element is not None and read_element.text else 'ε'
            
            if origem and destino:
                transicoes.append(Transicao(origem, destino, canvas, simbolos_entrada=simbolo))

        # Corrige o desenho de transições reversas que se sobrepõem
        corrigir_desvios_carregados()
        
        return True

    except Exception as e:
        messagebox.showerror("Erro de Importação JFLAP", f"Erro ao carregar o arquivo JFLAP: {e}")
        return False
    
#----------------------------------------------------------

def corrigir_desvios_carregados():
    pares_verificados = set()
    for t1 in transicoes:
        for t2 in transicoes:
            if t1 == t2 or tuple(sorted((id(t1), id(t2)))) in pares_verificados: continue
            if t1.origem == t2.destino and t1.destino == t2.origem:
                if t1.offset_x == 0 and t2.offset_x == 0: # Apenas corrige se ambos estiverem sem desvio
                    estado_origem, estado_destino = t1.origem, t1.destino
                    dist = math.dist((estado_origem.x, estado_origem.y), (estado_destino.x, estado_destino.y))
                    if dist == 0: dist = 1
                    vetor_x, vetor_y = (estado_destino.x - estado_origem.x) / dist, (estado_destino.y - estado_origem.y) / dist
                    vetor_perp_x, vetor_perp_y = -vetor_y, vetor_x
                    offset_dist = 15 # Distância do desvio
                    t1.offset_x, t1.offset_y = vetor_perp_x * offset_dist, vetor_perp_y * offset_dist
                    t1.atualizar_posicao()
                    t2.offset_x, t2.offset_y = -vetor_perp_x * offset_dist, -vetor_perp_y * offset_dist
                    t2.atualizar_posicao()
                pares_verificados.add(tuple(sorted((id(t1), id(t2))))) # Marca como verificado 


# --- UI Setup ---
janela = tk.Tk()
janela.title("Mini-JFLAP em Python v10")
janela.geometry("900x700")


# --- Menu ---
menu_bar = tk.Menu(janela)
menu_arquivo = tk.Menu(menu_bar, tearoff=0)
menu_arquivo.add_command(label="Novo", command=novo_automato)
menu_arquivo.add_command(label="Abrir", command=abrir_automato)
menu_arquivo.add_command(label="Salvar", command=salvar)
menu_arquivo.add_command(label="Salvar como...", command=salvar_como)
menu_arquivo.add_separator()
menu_arquivo.add_command(label="Sair", command=janela.quit)
menu_bar.add_cascade(label="Arquivo", menu=menu_arquivo)
# --- NOVO: Menu Tipo de Autômato ---
menu_tipo = tk.Menu(menu_bar, tearoff=0)
menu_tipo.add_command(label="Autômato Finito Determinístico (AFD)", command=lambda: definir_tipo_automato("AFD"))
menu_tipo.add_command(label="Autômato Finito Não Determinístico (AFN)", command=lambda: definir_tipo_automato("AFN")) # <-- NOVA OPÇÃO
menu_tipo.add_command(label="Autômato Finito Não Determinístico com ε (AFNe)", command=lambda: definir_tipo_automato("AFNe")) # <-- NOME MAIS CLARO
menu_tipo.add_separator() # Separador visual
menu_tipo.add_command(label="Máquina de Mealy", command=lambda: definir_tipo_automato("Mealy")) # Habilitado
menu_tipo.add_command(label="Máquina de Moore", command=lambda: definir_tipo_automato("Moore")) # <-- NOVA OPÇÃO
menu_tipo.add_separator() # Separador visual
menu_tipo.add_command(label="Autômato com Pilha [EM BREVE]", state="disabled")
menu_bar.add_cascade(label="Tipo de Autômato", menu=menu_tipo)
janela.config(menu=menu_bar)



# --- Toolbar ---
toolbar = tk.Frame(janela, bd=1, relief=tk.RAISED)
toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
icones = {}
try:
    nomes_icones = ["estado", "transicao", "apagar", "salvar"]
    for nome in nomes_icones:
        icones[nome] = ImageTk.PhotoImage(Image.open(f"icones/{nome}.png").resize((24, 24)))
    usar_icones = True
except Exception as e:
    print(f"Aviso: Ícones não carregados. Usando texto. (Erro: {e})")
    usar_icones = False

def criar_botao_toolbar(parent, nome_icone, texto, comando):
    icone = icones.get(nome_icone)
    if usar_icones and icone:
        btn = tk.Button(parent, image=icone, relief=tk.FLAT, command=comando, width=30, height=30)
    else:
        btn = tk.Button(parent, text=texto, relief=tk.FLAT, command=comando)
    btn.pack(side=tk.LEFT, padx=2, pady=2)
    return btn

btn_estado = criar_botao_toolbar(toolbar, "estado", "Estado", ativar_modo_arrastar)
btn_transicao = criar_botao_toolbar(toolbar, "transicao", "Transição", ativar_modo_transicao)
btn_apagar = criar_botao_toolbar(toolbar, "apagar", "Apagar", ativar_modo_apagar)
tk.Frame(toolbar, height=30, width=2, bg="grey").pack(side=tk.LEFT, padx=5, pady=2)
btn_salvar = criar_botao_toolbar(toolbar, "salvar", "Salvar", salvar)


# --- Canvas ---
canvas = tk.Canvas(janela, bg="white", highlightthickness=1, highlightbackground="black") # Borda preta
canvas.pack(fill="both", expand=True, padx=10, pady=10) # Expande para preencher o espaço disponível
canvas.bind("<ButtonPress-1>", iniciar_movimento) # Clique com o botão esquerdo
canvas.bind("<Double-Button-1>", gerenciar_clique_duplo) # Duplo clique com o botão esquerdo
canvas.bind("<B1-Motion>", arrastar_objeto) # Arrasta com o botão esquerdo
canvas.bind("<ButtonRelease-1>", finalizar_arraste) # Solta o botão esquerdo
canvas.bind("<Button-2>", cancelar_criacao_transicao)  # Botão do meio para cancelar transição
canvas.bind("<Button-3>", mostrar_menu_contexto) # Botão direito para menu de contexto
janela.bind("<Key>", gerenciar_atalhos_teclado) # Atalhos de teclado
janela.bind("<Control-s>", atalho_salvar) # Atalho Ctrl+S para salvar


# --- Painel Inferior (Status Bar) ---
status_bar = tk.Frame(janela, bd=1, relief=tk.SUNKEN)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)
# NOVO: Label da esquerda para o status permanente (modo e tipo)
status_modo = tk.Label(status_bar, text="", bd=1, relief=tk.FLAT, anchor=tk.W)
status_modo.pack(side=tk.LEFT, padx=5, pady=2)
# NOVO: Label da direita para as ações temporárias
status_acao = tk.Label(status_bar, text="Bem-vindo!", bd=1, relief=tk.FLAT, anchor=tk.E)
status_acao.pack(side=tk.RIGHT, padx=5, pady=2)

# --- Painel de Simulação ---
painel_simulacao = tk.Frame(janela)
painel_simulacao.pack(side=tk.BOTTOM, fill="x", padx=10, pady=5)
tk.Label(painel_simulacao, text="Palavra:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
input_entry = tk.Entry(painel_simulacao, width=40)
input_entry.pack(side=tk.LEFT, padx=5)
botao_simular = tk.Button(painel_simulacao, text="Simular", command=simular_palavra)
botao_simular.pack(side=tk.LEFT, padx=5)
resultado = tk.Label(painel_simulacao, text="", font=("Arial", 12, "bold"))
resultado.pack(side=tk.LEFT, padx=10)
sequencia_saida = tk.Label(painel_simulacao, text="Saída: ", font=("Arial", 12))  
sequencia_saida.pack(side=tk.LEFT, padx=10)

ativar_modo_arrastar()
janela.mainloop() # Inicia o loop principal da interface gráfica