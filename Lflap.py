import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, colorchooser
from PIL import Image, ImageTk
import json
import math
import xml.etree.ElementTree as ET 
from xml.dom import minidom 
import csv 
import sys
import os

# --- Constante Global ---
SIMBOLO_BRANCO = "B" # Define o símbolo "branco" da fita de Turing


# --- FUNÇÃO HELPER PARA PYINSTALLER ---
def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, funciona para dev e para PyInstaller """
    try:
        # PyInstaller cria uma pasta temporária e guarda o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Se não estiver "congelado", o caminho é o do script
        base_path = os.path.abspath(os.path.dirname(__file__))

    return os.path.join(base_path, relative_path)
# --- FIM DA FUNÇÃO HELPER ---


# --- Classes ---
class Estado:
    # (Classe Estado permanece inalterada)
    def __init__(self, nome, x, y, canvas):
        self.nome = nome
        self.x = x
        self.y = y
        self.raio = 30
        self.canvas = canvas
        self.inicial = False
        self.aceitacao = False 
        self.simbolo_saida = "" 
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

    def atualizar_texto(self):
        texto_display = self.nome
        if tipo_automato_atual == "Moore" and self.simbolo_saida:
            texto_display = f"{self.nome}/{self.simbolo_saida}"
        self.canvas.itemconfig(self.id_texto, text=texto_display)

    def selecionar(self):
        self.canvas.itemconfig(self.id_circulo, outline="green", width=3)
    def desselecionar(self):
        self.canvas.itemconfig(self.id_circulo, outline="black", width=2)


class Transicao:
    # --- MODIFICADO (v16): Padrões da MT corrigidos para SIMBOLO_BRANCO ---
    # --- MODIFICADO (v16): Padrões da MT corrigidos para SIMBOLO_BRANCO ---
    def __init__(self, origem, destino, canvas, simbolos_entrada="ε", simbolo_saida="", 
                 simbolo_pop="ε", string_push="ε", 
                 simbolo_leitura=SIMBOLO_BRANCO, simbolo_escrita=SIMBOLO_BRANCO, movimento_cabecote="S", 
                 offset_x=0, offset_y=0):
        self.origem = origem
        self.destino = destino
        self.canvas = canvas
        
        if isinstance(simbolos_entrada, str):
            self.simbolos_entrada = [s.strip() for s in simbolos_entrada.split(',')]
        else:
            self.simbolos_entrada = simbolos_entrada
        self.simbolo_saida = simbolo_saida
        
        self.simbolo_pop = simbolo_pop
        self.string_push = string_push
        
        self.simbolo_leitura = simbolo_leitura
        self.simbolo_escrita = simbolo_escrita
        self.movimento_cabecote = movimento_cabecote
        
        self.tag_unica = f"trans_{id(self)}"
        self.offset_x = offset_x
        self.offset_y = offset_y 
        self.is_loop = (self.origem == self.destino)
        self.atualizar_posicao()

    def _get_rotulo_texto(self):
        # (Função _get_rotulo_texto da v14, já estava correta)
        global tipo_automato_atual
        texto_entrada = ",".join(self.simbolos_entrada)

        if tipo_automato_atual == "Mealy" and self.simbolo_saida:
            return f"{texto_entrada}/{self.simbolo_saida}"
        
        if tipo_automato_atual == "AP":
            pop_val = self.simbolo_pop if self.simbolo_pop else "ε"
            push_val = self.string_push if self.string_push else "ε"
            return f"{texto_entrada}, {pop_val} ; {push_val}"
            
        if tipo_automato_atual == "MT":
            read_val = self.simbolo_leitura if self.simbolo_leitura else SIMBOLO_BRANCO
            write_val = self.simbolo_escrita if self.simbolo_escrita else SIMBOLO_BRANCO
            move_val = self.movimento_cabecote if self.movimento_cabecote else "S"
            return f"{read_val} ; {write_val}, {move_val}"
            
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
        offset_x_aplicado = self.offset_x
        offset_y_aplicado = self.offset_y

        # 🔍 Verifica se já existe outro loop no mesmo estado
        loops_mesmo_estado = [
            t for t in transicoes
            if t.origem == self.origem and t.destino == self.destino and t.is_loop
        ]

        # --- LINHA ADICIONADA (v17): Ordena os loops para estabilidade ---
        # A lista DEVE ser ordenada para que o 'indice_loop' seja estável
        loops_mesmo_estado.sort(key=lambda t: t.tag_unica)
        # --- FIM DA LINHA ADICIONADA ---

        indice_loop = loops_mesmo_estado.index(self) if self in loops_mesmo_estado else 0

        # ✅ Se for o primeiro loop, desenha o arco e a seta
        if indice_loop == 0:
            bounding_box = (
                x - raio_loop + offset_x_aplicado,
                y - (2 * raio_estado) + offset_y_aplicado,
                x + raio_loop + offset_x_aplicado,
                y + offset_y_aplicado,
            )
            self.canvas.create_arc(
                bounding_box, start=210, extent=-240, style=tk.ARC,
                outline="black", width=2, tags=(self.tag_unica, "transicao")
            )

            angulo_final_rad = math.radians(-30)
            centro_arco_x = x + offset_x_aplicado
            centro_arco_y = y - raio_estado + offset_y_aplicado
            ponta_x = centro_arco_x + raio_loop * math.cos(angulo_final_rad)
            ponta_y = centro_arco_y - raio_loop * math.sin(angulo_final_rad)
            ponta1, ponta2, ponta3 = (
                (ponta_x, ponta_y),
                (ponta_x - 10, ponta_y - 2),
                (ponta_x - 2, ponta_y + 8),
            )
            self.canvas.create_polygon(
                ponta1, ponta2, ponta3,
                fill="black", tags=(self.tag_unica, "transicao")
            )

        # 🧩 Empilha os textos acima do arco único
        espacamento = 11  # distância vertical entre rótulos
        base_y = y - raio_estado - raio_loop - 20 + offset_y_aplicado
        coords_texto = (
            x + offset_x_aplicado,
            base_y + indice_loop * espacamento,  # empilha "pra baixo", mais próximo
        )


        self.canvas.create_text(
            coords_texto,
            text=self._get_rotulo_texto(),
            font=("Arial", 10, "italic"),
            tags=(self.tag_unica, "rotulo")
        )


    def atualizar_simbolo(self, novo_rotulo_completo):
        # (Função atualizar_simbolo da v14, já estava correta)
        global tipo_automato_atual

        if tipo_automato_atual == "MT":
            try:
                partes_ponto_virgula = novo_rotulo_completo.split(';', 1)
                self.simbolo_leitura = partes_ponto_virgula[0].strip()
                parte_direita = partes_ponto_virgula[1].strip()
                partes_virgula = parte_direita.split(',', 1)
                self.simbolo_escrita = partes_virgula[0].strip()
                self.movimento_cabecote = partes_virgula[1].strip().upper()
                if not self.simbolo_leitura: self.simbolo_leitura = SIMBOLO_BRANCO
                if not self.simbolo_escrita: self.simbolo_escrita = SIMBOLO_BRANCO
                if self.movimento_cabecote not in ["R", "L", "S"]:
                    self.movimento_cabecote = "S"
            except Exception as e:
                messagebox.showerror("Erro de Formato", "Formato inválido. Use: leitura ; escrita, movimento (R/L/S)")
                return

        elif tipo_automato_atual == "AP":
            try:
                partes_ponto_virgula = novo_rotulo_completo.split(';', 1)
                parte_esquerda = partes_ponto_virgula[0].strip()
                self.string_push = partes_ponto_virgula[1].strip() if len(partes_ponto_virgula) > 1 else "ε"
                partes_virgula = parte_esquerda.split(',', 1)
                simbolo_entrada = partes_virgula[0].strip() if partes_virgula[0].strip() else "ε"
                self.simbolos_entrada = [simbolo_entrada] 
                self.simbolo_pop = partes_virgula[1].strip() if len(partes_virgula) > 1 else "ε"
                if not self.simbolos_entrada[0]: self.simbolos_entrada = ["ε"]
                if not self.simbolo_pop: self.simbolo_pop = "ε"
                if not self.string_push: self.string_push = "ε"
            except Exception as e:
                messagebox.showerror("Erro de Formato", "Formato inválido. Use: entrada, pop ; push")
                return 

        elif tipo_automato_atual == "Mealy":
            partes = novo_rotulo_completo.split('/', 1)
            simbolos_entrada_str = partes[0].strip()
            self.simbolo_saida = partes[1].strip() if len(partes) > 1 else ""
            if not simbolos_entrada_str or simbolos_entrada_str.lower() == "ε":
                self.simbolos_entrada = ["ε"]
            else:
                self.simbolos_entrada = [s.strip() for s in simbolos_entrada_str.split(',')]
        
        else:
            partes = novo_rotulo_completo.split('/', 1) 
            simbolos_entrada_str = partes[0].strip()
            self.simbolo_saida = "" 
            if not simbolos_entrada_str or simbolos_entrada_str.lower() == "ε":
                self.simbolos_entrada = ["ε"]
            else:
                self.simbolos_entrada = [s.strip() for s in simbolos_entrada_str.split(',')]

        self.atualizar_posicao()

    def destruir(self):
        self.canvas.delete(self.tag_unica)

    def selecionar(self):
        self.canvas.itemconfig(self.tag_unica, fill="green")
    def desselecionar(self):
        self.atualizar_posicao()


# --- Variáveis Globais ---
contador_estados = 0
estados = {}
transicoes = []
objeto_arrastado = {"id": None, "x_inicial": 0, "y_inicial": 0}
modo_atual = "arrastar"
transicao_info = {"origem": None}
caminho_arquivo_atual = None
tipo_automato_atual = "AFNe"
itens_selecionados = set()
caixa_selecao = None
fita_atual = {} 
posicao_cabecote_atual = 0
celulas_fita_ids = [] 
simulacao_mt_rodando = False
estado_mt_atual = None
historico_passos_mt = [] 
modo_atual = "AFNe"  # valor inicial padrão


# --- FUNÇÃO HELPER (Correção v17) ---
def recalcular_offsets_loops(estado):
    """Pega todos os loops de um estado e FORÇA ELES A SE REDESENHAREM."""
    if not estado: return
    
    # 1. Encontra todos os loops para este estado
    loops_do_estado = [t for t in transicoes if t.is_loop and t.origem == estado]
    
    # 2. Ordena os loops (pela sua tag única) para ter uma ordem consistente
    loops_do_estado.sort(key=lambda t: t.tag_unica) 
    
    # 3. Força o redesenho (resetando os offsets para 0)
    for i, t_loop in enumerate(loops_do_estado):
        t_loop.offset_y = -i * 30
        t_loop.offset_x = 0 # Garante que não há desvio lateral
        t_loop.atualizar_posicao() # Força o redesenho
# --- FIM DA FUNÇÃO ---


# --- Funções "Detetive" ---
def encontrar_estado_clicado(event):
    # (Esta função permanece inalterada)
    itens_proximos = canvas.find_closest(event.x, event.y)
    if not itens_proximos: return None
    tags_do_item = canvas.gettags(itens_proximos[0])
    tags_de_sistema = {"estado", "texto", "seta_inicial", "aceitacao"}
    tag_nome = next((tag for tag in tags_do_item if tag not in tags_de_sistema), None)
    return estados.get(tag_nome)


# --- Funções de Interação e UI ---
def iniciar_movimento(event):
    global caixa_selecao
    
    if modo_atual == "apagar":
        gerenciar_clique_apagar(event)
        return

    itens_proximos = canvas.find_closest(event.x, event.y)
    if itens_proximos:
        id_item_clicado = itens_proximos[0]
        tags = canvas.gettags(id_item_clicado)
        if "transicao" in tags or "rotulo" in tags:
            if not simulacao_mt_rodando:
                editar_rotulo_transicao(id_item_clicado)
            return

    if modo_atual == "arrastar":
        if simulacao_mt_rodando: return
        estado_clicado = encontrar_estado_clicado(event)
        if estado_clicado:
            dist = math.dist((event.x, event.y), (estado_clicado.x, estado_clicado.y))
            if dist <= estado_clicado.raio:
                objeto_arrastado["id"] = estado_clicado
                objeto_arrastado["x_inicial"], objeto_arrastado["y_inicial"] = event.x, event.y
            else:
                criar_novo_estado(event.x, event.y)
        else:
            criar_novo_estado(event.x, event.y)
            
    elif modo_atual == "selecao":
        if simulacao_mt_rodando: return
        estado_clicado = encontrar_estado_clicado(event)
        distancia_do_clique = math.inf
        if estado_clicado:
            distancia_do_clique = math.dist((event.x, event.y), (estado_clicado.x, estado_clicado.y))

        if estado_clicado and estado_clicado in itens_selecionados and distancia_do_clique <= estado_clicado.raio:
            objeto_arrastado["id"] = "grupo"
            objeto_arrastado["x_inicial"], objeto_arrastado["y_inicial"] = event.x, event.y
        else:
            for item in itens_selecionados: item.desselecionar()
            itens_selecionados.clear()
            caixa_selecao = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="blue", dash=(3, 5))
            objeto_arrastado["x_inicial"], objeto_arrastado["y_inicial"] = event.x, event.y

    elif modo_atual == "transicao":
        if simulacao_mt_rodando: return
        gerenciar_clique_transicao(event)

def gerenciar_clique_arrastar(event):
    # (Esta função permanece inalterada)
    estado_clicado = encontrar_estado_clicado(event)
    if estado_clicado:
        dist = math.dist((event.x, event.y), (estado_clicado.x, estado_clicado.y))
        if dist <= estado_clicado.raio:
            objeto_arrastado["id"] = estado_clicado
            objeto_arrastado["x_inicial"], objeto_arrastado["y_inicial"] = event.x, event.y
            return
    criar_novo_estado(event.x, event.y)

def gerenciar_clique_transicao(event):
    # (Esta função permanece inalterada)
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
            offset_dist = 15 
            nova_transicao.offset_x, nova_transicao.offset_y = vetor_perp_x * offset_dist, vetor_perp_y * offset_dist
            nova_transicao.atualizar_posicao()
            transicao_gemea.offset_x, transicao_gemea.offset_y = -vetor_perp_x * offset_dist, -vetor_perp_y * offset_dist
            transicao_gemea.atualizar_posicao()
        canvas.itemconfig(estado_origem.id_circulo, fill="lightblue")
        transicao_info["origem"] = None
        status_acao.config(text="Transição criada! Clique nela para editar o símbolo.")

def editar_rotulo_transicao(id_item_clicado):
    # (Esta função permanece a mesma da v14)
    tags_do_item = canvas.gettags(id_item_clicado)
    tag_alvo = next((tag for tag in tags_do_item if tag.startswith("trans_")), None) 
    if not tag_alvo: return
    transicao_alvo = next((t for t in transicoes if t.tag_unica == tag_alvo), None) 
    if not transicao_alvo: return

    if tipo_automato_atual == "MT":
        valor_inicial = transicao_alvo._get_rotulo_texto()
        novo_rotulo_completo = simpledialog.askstring(
            "Editar Transição (MT)",
            "Formato: leitura ; escrita, movimento (R/L/S)",
            initialvalue=valor_inicial
        )
        if novo_rotulo_completo is not None:
            transicao_alvo.atualizar_simbolo(novo_rotulo_completo)

    elif tipo_automato_atual == "AP":
        valor_inicial = transicao_alvo._get_rotulo_texto()
        novo_rotulo_completo = simpledialog.askstring(
            "Editar Transição (AP)",
            "Formato: entrada, pop ; push (ex: a, X ; YX)",
            initialvalue=valor_inicial
        )
        if novo_rotulo_completo is not None:
            transicao_alvo.atualizar_simbolo(novo_rotulo_completo)

    elif tipo_automato_atual in ["AFD", "AFN", "AFNe", "Moore"]:
        valor_inicial = ",".join(transicao_alvo.simbolos_entrada)
        novo_rotulo = simpledialog.askstring(
            f"Editar Símbolos ({tipo_automato_atual})",
            "Digite o(s) símbolo(s) de entrada, separados por vírgula:",
            initialvalue=valor_inicial
        )
        if novo_rotulo is not None:
            simbolos_novos = [s.strip() for s in novo_rotulo.split(',') if s.strip()]
            if not simbolos_novos: simbolos_novos = ["ε"]
            if tipo_automato_atual in ["AFD", "AFN"] and "ε" in simbolos_novos:
                messagebox.showerror(f"Regra de {tipo_automato_atual} Violada", f"Um {tipo_automato_atual} não pode conter transições épsilon (ε).")
                return 
            if tipo_automato_atual == "AFD":
                for simbolo in simbolos_novos:
                    for outra_t in transicoes:
                        if outra_t == transicao_alvo: continue
                        if outra_t.origem == transicao_alvo.origem and simbolo in outra_t.simbolos_entrada:
                            messagebox.showerror("Regra de AFD Violada", 
                                f"Não-determinismo detectado!\nO estado '{transicao_alvo.origem.nome}' já tem uma transição para o símbolo '{simbolo}'.")
                            return 
            transicao_alvo.atualizar_simbolo(novo_rotulo)

    elif tipo_automato_atual == "Mealy":
        valor_inicial = transicao_alvo._get_rotulo_texto()
        novo_rotulo_completo = simpledialog.askstring(
            "Editar Transição (Mealy)",
            "Formato: entrada / saida (ex: a/1)",
            initialvalue=valor_inicial
        )
        if novo_rotulo_completo is not None:
            transicao_alvo.atualizar_simbolo(novo_rotulo_completo)

# --- MODIFICADO: Chama recalcular_offsets_loops ao apagar um loop (v15) ---
def gerenciar_clique_apagar(event):
    if simulacao_mt_rodando: return
    estado_clicado = encontrar_estado_clicado(event)
    if estado_clicado:
        apagar_estado(estado_clicado) # apagar_estado lida com seus próprios loops
        return

    itens_proximos = canvas.find_closest(event.x, event.y)
    if not itens_proximos: return
    id_item_clicado = itens_proximos[0]
    tags = canvas.gettags(id_item_clicado)
    
    tag_alvo = next((t for t in tags if t.startswith("trans_")), None)
    if tag_alvo:
        transicao_para_apagar = next((t for t in transicoes if t.tag_unica == tag_alvo), None)
        if transicao_para_apagar:
            estado_origem = transicao_para_apagar.origem # Salva o estado de origem
            era_loop = transicao_para_apagar.is_loop    # Salva se era loop
            
            transicao_para_apagar.destruir()
            transicoes.remove(transicao_para_apagar)
            status_acao.config(text="Transição apagada com sucesso.")
            
            # --- NOVO: Recalcula offsets se apagou um loop ---
            if era_loop:
                recalcular_offsets_loops(estado_origem)
            # --- FIM DA MODIFICAÇÃO ---

def arrastar_objeto(event):
    if simulacao_mt_rodando: return
    
    if modo_atual == "arrastar" and isinstance(objeto_arrastado.get("id"), Estado):
        estado = objeto_arrastado["id"]
        dx, dy = event.x - objeto_arrastado["x_inicial"], event.y - objeto_arrastado["y_inicial"]
        estado.mover(dx, dy)
        objeto_arrastado["x_inicial"], objeto_arrastado["y_inicial"] = event.x, event.y
        atualizar_transicoes_conectadas(estado)
        
    elif modo_atual == "selecao" and caixa_selecao:
        x0, y0 = objeto_arrastado["x_inicial"], objeto_arrastado["y_inicial"]
        canvas.coords(caixa_selecao, x0, y0, event.x, event.y)

    elif modo_atual == "selecao" and objeto_arrastado.get("id") == "grupo":
        dx, dy = event.x - objeto_arrastado["x_inicial"], event.y - objeto_arrastado["y_inicial"]
        for estado in itens_selecionados:
            estado.mover(dx, dy)
        for estado in itens_selecionados:
            atualizar_transicoes_conectadas(estado)
        objeto_arrastado["x_inicial"], objeto_arrastado["y_inicial"] = event.x, event.y

def finalizar_arraste(event):
    if simulacao_mt_rodando: return
    global caixa_selecao
    if modo_atual == "selecao" and caixa_selecao:
        coords_caixa = canvas.coords(caixa_selecao)
        ids_na_caixa = canvas.find_enclosed(*coords_caixa)
        for item_id in ids_na_caixa:
            tags = canvas.gettags(item_id)
            if "estado" in tags:
                nome_estado = next((t for t in tags if not t.startswith("trans_") and t not in ["estado", "texto", "rotulo", "aceitacao"]), None)
                if nome_estado and estados.get(nome_estado) not in itens_selecionados:
                    estado = estados[nome_estado]
                    estado.selecionar()
                    itens_selecionados.add(estado)
        canvas.delete(caixa_selecao)
        caixa_selecao = None
    objeto_arrastado["id"] = None

def criar_novo_estado(x, y):
    if simulacao_mt_rodando: return
    global contador_estados
    nome_estado = f"q{contador_estados}"
    estado = Estado(nome_estado, x, y, canvas)
    estados[nome_estado] = estado
    if not any(est.inicial for est in estados.values() if est != estado):
        estado.set_inicial()
    contador_estados += 1

def toggle_aceitacao_event(event):
    if simulacao_mt_rodando: return
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
    if simulacao_mt_rodando: return
    
    estado_clicado = encontrar_estado_clicado(event)
    if not estado_clicado: return

    menu_contexto = tk.Menu(janela, tearoff=0)
    acao_em_grupo = estado_clicado in itens_selecionados and len(itens_selecionados) > 1

    if acao_em_grupo:
        if tipo_automato_atual not in ["Mealy", "Moore"]:
            menu_contexto.add_command(
                label=f"Marcar/Desmarcar Aceitação/Halt ({len(itens_selecionados)} itens)",
                command=toggle_aceitacao_selecao
            )
        menu_contexto.add_command(label="Renomear Estados...", state="disabled")
        menu_contexto.add_command(
            label=f"Alterar Cor ({len(itens_selecionados)} itens)...",
            command=mudar_cor_selecao
        )
        menu_contexto.add_separator()
        menu_contexto.add_command(
            label=f"Apagar {len(itens_selecionados)} Estados Selecionados",
            command=apagar_selecao
        )
    else:
        if tipo_automato_atual not in ["Mealy", "Moore"]:
            label_aceitacao = "Marcar/Desmarcar Aceitação"
            if tipo_automato_atual == "MT":
                label_aceitacao += "/Halt" 
            menu_contexto.add_command(label=label_aceitacao, command=estado_clicado.toggle_aceitacao)
        
        if tipo_automato_atual == "Moore":
            menu_contexto.add_command(label="Definir Saída do Estado...", command=lambda: definir_saida_estado(estado_clicado))
        
        menu_contexto.add_command(label="Renomear Estado...", command=lambda: renomear_estado(estado_clicado))
        menu_contexto.add_command(label="Alterar Cor...", command=lambda: mudar_cor_estado(estado_clicado))
        menu_contexto.add_separator()
        menu_contexto.add_command(label="Apagar Estado", command=lambda: apagar_estado(estado_clicado))

    menu_contexto.post(event.x_root, event.y_root)

def atualizar_status_modo():
    texto_modo = modo_atual.capitalize().replace("Arrastar", "Criar/Arrastar")
    status_modo.config(text=f"Tipo: {tipo_automato_atual}  |  Modo: {texto_modo}")

def mudar_cor_estado(estado):
    if simulacao_mt_rodando: return
    nova_cor = colorchooser.askcolor(title=f"Escolha a cor para {estado.nome}")
    if nova_cor and nova_cor[1]:
        canvas.itemconfig(estado.id_circulo, fill=nova_cor[1])

def renomear_estado(estado):
    if simulacao_mt_rodando: return
    novo_nome = simpledialog.askstring("Renomear Estado", f"Digite o novo nome para '{estado.nome}':", initialvalue=estado.nome)
    if novo_nome and novo_nome not in estados:
        nome_antigo = estado.nome
        ids_componentes = canvas.find_withtag(nome_antigo)
        for item_id in ids_componentes:
            tags_atuais = list(canvas.gettags(item_id))
            novas_tags = [novo_nome if t == nome_antigo else t for t in tags_atuais]
            canvas.itemconfig(item_id, tags=tuple(novas_tags))
        
        estado.nome = novo_nome
        estado.atualizar_texto() 
        
        estados[novo_nome] = estados.pop(nome_antigo)
    elif novo_nome:
        messagebox.showwarning("Erro", "O nome inserido já existe ou é inválido.")

# --- MODIFICADO: Chama recalcular_offsets_loops ao apagar estado (v15) ---
def apagar_estado(estado_para_apagar):
    if simulacao_mt_rodando: return
    if not estado_para_apagar: return
    confirmar = messagebox.askyesno(
        "Apagar Estado",
        f"Tem certeza que deseja apagar o estado '{estado_para_apagar.nome}'?\n"
        f"Todas as transições conectadas a ele também serão apagadas."
    )
    if confirmar:
        transicoes_a_remover = [
            t for t in transicoes
            if t.origem == estado_para_apagar or t.destino == estado_para_apagar
        ]
        
        # --- MODIFICADO: Recalcula loops de estados afetados ---
        estados_loops_afetados = set()
        for t in transicoes_a_remover:
            # Se a transição é um loop, ela não afeta outros estados
            if not t.is_loop:
                # Se for uma linha, pode afetar loops no estado OPOSTO
                if t.origem == estado_para_apagar and t.destino.nome in estados:
                    estados_loops_afetados.add(t.destino)
                elif t.destino == estado_para_apagar and t.origem.nome in estados:
                    estados_loops_afetados.add(t.origem)
            
            t.destruir()
            transicoes.remove(t)
        
        # Recalcula offsets para estados que tinham linhas conectadas ao estado apagado
        for estado in estados_loops_afetados:
            recalcular_offsets_loops(estado)
        # --- FIM DA MODIFICAÇÃO ---

        nome_estado = estado_para_apagar.nome
        estado_para_apagar.destruir()
        del estados[nome_estado]
        status_acao.config(text=f"Estado {nome_estado} apagado.")
    else:
        status_acao.config(text="Ação de apagar cancelada.")

def cancelar_criacao_transicao(event):
    if simulacao_mt_rodando: return
    global transicao_info
    if transicao_info["origem"]:
        canvas.itemconfig(transicao_info["origem"].id_circulo, fill="lightblue")
        transicao_info["origem"] = None
        status_acao.config(text="Criação de transição cancelada.")
        print("Criação de transição cancelada.")

def gerenciar_atalhos_teclado(event):
    if simulacao_mt_rodando: return 
    
    if event.keysym == "F1":
        ativar_modo_arrastar()
    elif event.keysym == "F2":
        ativar_modo_transicao()
    elif event.keysym == "F3":
        ativar_modo_selecao()
    elif event.keysym == "F4":
        ativar_modo_apagar()
    elif event.keysym == "Delete" and itens_selecionados:
        apagar_selecao()

# --- MODIFICADO: Chama recalcular_offsets_loops ao criar loop (v15) ---
def gerenciar_clique_duplo(event):
    if simulacao_mt_rodando: return
    
    if modo_atual == "transicao":
        estado_clicado = encontrar_estado_clicado(event)
        if estado_clicado:
            nova_transicao = Transicao(estado_clicado, estado_clicado, canvas)
            transicoes.append(nova_transicao)
            
            # --- LÓGICA DE OFFSET SUBSTITUÍDA ---
            recalcular_offsets_loops(estado_clicado)
            # --- FIM DA SUBSTITUIÇÃO ---
            
            if transicao_info["origem"]:
                canvas.itemconfig(transicao_info["origem"].id_circulo, fill="lightblue")
                transicao_info["origem"] = None
            status_acao.config(text=f"Laço criado para o estado {estado_clicado.nome}.")
    else:
        toggle_aceitacao_event(event)

# --- Funções de Modo e Tipo ---
def ativar_modo_arrastar():
    if simulacao_mt_rodando: return
    global modo_atual
    limpar_selecao() 
    modo_atual = "arrastar"
    atualizar_status_modo()
    print("Modo alterado para: arrastar")

def ativar_modo_transicao():
    if simulacao_mt_rodando: return
    global modo_atual
    limpar_selecao() 
    modo_atual = "transicao"
    atualizar_status_modo()
    print("Modo alterado para: transicao")

def ativar_modo_apagar():
    if simulacao_mt_rodando: return
    global modo_atual
    limpar_selecao() 
    modo_atual = "apagar"
    atualizar_status_modo()
    print("Modo alterado para: apagar")

def ativar_modo_selecao():
    if simulacao_mt_rodando: return
    global modo_atual
    modo_atual = "selecao"
    atualizar_status_modo() 
    print("Modo alterado para: selecao")

def limpar_selecao():
    if itens_selecionados:
        for item in itens_selecionados:
            item.desselecionar()
        itens_selecionados.clear()
        print("Seleção limpa.")

# --- MODIFICADO: Chama recalcular_offsets_loops ao apagar seleção (v15) ---
def apagar_selecao():
    if simulacao_mt_rodando: return
    if not itens_selecionados:
        return
    confirmar = messagebox.askyesno(
        "Apagar Seleção",
        f"Tem certeza que deseja apagar os {len(itens_selecionados)} estados selecionados?\n"
        "Todas as transições conectadas a eles também serão apagadas."
    )
    if confirmar:
        estados_para_apagar = set(itens_selecionados)
        transicoes_para_apagar = set()
        
        estados_loops_afetados = set()
        
        for t in transicoes:
            if t.origem in estados_para_apagar or t.destino in estados_para_apagar:
                transicoes_para_apagar.add(t)
                
                if t.is_loop:
                    if t.origem in estados_para_apagar:
                        pass 
                elif t.origem in estados_para_apagar and t.destino not in estados_para_apagar:
                    estados_loops_afetados.add(t.destino)
                elif t.destino in estados_para_apagar and t.origem not in estados_para_apagar:
                    estados_loops_afetados.add(t.origem)
        
        for t in transicoes_para_apagar:
            t.destruir()
            if t in transicoes:
                transicoes.remove(t)
                
        for estado in estados_para_apagar:
            nome_estado = estado.nome
            estado.destruir()
            if nome_estado in estados:
                del estados[nome_estado]
        
        for estado in estados_loops_afetados:
            if estado.nome in estados: 
                recalcular_offsets_loops(estado)
        
        itens_selecionados.clear()
        status_acao.config(text=f"{len(estados_para_apagar)} estados foram apagados.")

def atalho_apagar_selecao(event):
    if simulacao_mt_rodando: return
    apagar_selecao()

def toggle_aceitacao_selecao():
    if simulacao_mt_rodando: return
    if not itens_selecionados: return
    if tipo_automato_atual in ["Mealy", "Moore"]: return
    
    for estado in itens_selecionados:
        estado.toggle_aceitacao()
    status_acao.config(text=f"Estado de aceitação alterado para {len(itens_selecionados)} itens.")

def mudar_cor_selecao():
    if simulacao_mt_rodando: return
    if not itens_selecionados: return
    nova_cor = colorchooser.askcolor(title="Escolha a cor para a seleção") 
    if nova_cor and nova_cor[1]:
        for estado in itens_selecionados:
            canvas.itemconfig(estado.id_circulo, fill=nova_cor[1]) 
        status_acao.config(text=f"Cor alterada para {len(itens_selecionados)} itens.")

def definir_tipo_automato(novo_tipo, forcar=False):
    global tipo_automato_atual
    
    if simulacao_mt_rodando:
        messagebox.showwarning("Simulação em Andamento", "Resete a simulação da Máquina de Turing antes de mudar o tipo.")
        return

    # Atualiza a UI da fita ANTES de qualquer confirmação
    if novo_tipo == "MT":
        painel_fita.pack(side=tk.BOTTOM, fill="x", padx=10, pady=5)
    else:
        painel_fita.pack_forget()

    confirmar = True # Assume True se 'forcar'
    if not forcar: # Só pergunta se não for forçado
        if estados or transicoes:
            confirmar = messagebox.askyesno(
                "Mudar Tipo de Autômato",
                f"Você tem certeza que deseja mudar para {novo_tipo}?\n"
                "Todo o trabalho não salvo no autômato atual será perdido."
            )
            if not confirmar:
                # Reverte a exibição da fita se o usuário cancelar
                if tipo_automato_atual == "MT":
                    painel_fita.pack(side=tk.BOTTOM, fill="x", padx=10, pady=5)
                else:
                    painel_fita.pack_forget()
                return

    if confirmar:
        novo_automato()
        tipo_automato_atual = novo_tipo
        atualizar_status_modo() 
        status_acao.config(text=f"Tipo alterado para {novo_tipo}.") 
        print(f"Tipo de autômato definido para: {tipo_automato_atual}")

def definir_saida_estado(estado):
    if simulacao_mt_rodando: return
    nova_saida = simpledialog.askstring(
        "Definir Saída de Estado (Moore)",
        f"Digite o símbolo de saída para o estado '{estado.nome}':",
        initialvalue=estado.simbolo_saida
    )
    if nova_saida is not None: 
        estado.simbolo_saida = nova_saida
        estado.atualizar_texto() 

# --- Funções de Animação e Simulação ---

def desenhar_fita(fita_dict, posicao_cabecote):
    # (Esta função permanece a mesma da v14)
    global celulas_fita_ids
    canvas_fita.delete("all") 
    celulas_fita_ids.clear()
    
    largura_canvas = canvas_fita.winfo_width()
    if largura_canvas <= 1: largura_canvas = 800 
    altura_canvas = canvas_fita.winfo_height()
    tamanho_celula = 40
    
    num_celulas_visiveis = (largura_canvas // tamanho_celula)
    indice_inicio = posicao_cabecote - (num_celulas_visiveis // 2)
    
    for i in range(num_celulas_visiveis):
        indice_fita = indice_inicio + i
        x0 = i * tamanho_celula
        y0 = (altura_canvas - tamanho_celula) / 2 
        if y0 < 0: y0 = 10 
        
        simbolo = fita_dict.get(indice_fita, SIMBOLO_BRANCO)
        
        cor_fundo = "white"
        if indice_fita == posicao_cabecote:
             cor_fundo = "#FFFFCC" 

        id_rect = canvas_fita.create_rectangle(x0, y0, x0 + tamanho_celula, y0 + tamanho_celula, 
                                               fill=cor_fundo, outline="black", width=1)
        
        id_text = canvas_fita.create_text(x0 + tamanho_celula / 2, y0 + tamanho_celula / 2,
                                          text=simbolo, font=("Courier", 14))
        
        celulas_fita_ids.extend([id_rect, id_text])
        
        if indice_fita == posicao_cabecote:
            x_cabecote = x0 + tamanho_celula / 2
            id_cabecote = canvas_fita.create_polygon(
                x_cabecote - 7, y0 - 15,
                x_cabecote + 7, y0 - 15,
                x_cabecote, y0 - 5,
                fill="red"
            )
            celulas_fita_ids.append(id_cabecote)

def animar_token(token_id, origem, destino, callback_ao_finalizar, passo_atual=0, total_passos=30):
    # (Esta função permanece inalterada)
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
    # (Esta função permanece inalterada)
    fecho = set(estados_origem)
    pilha = list(estados_origem)
    while pilha:
        estado_atual = pilha.pop()
        for t in transicoes:
            if tipo_automato_atual == "AFNe":
                if t.origem == estado_atual and "ε" in t.simbolos_entrada:
                    if t.destino not in fecho:
                        fecho.add(t.destino)
                        pilha.append(t.destino)
    return fecho

def validar_automato_como_AFD():
    # (Esta função permanece inalterada)
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
    # (Esta função permanece a mesma da v14 - já está correta para passo-a-passo)
    global tipo_automato_atual, simulacao_mt_rodando, fita_atual, posicao_cabecote_atual, estado_mt_atual, historico_passos_mt
    
    if tipo_automato_atual == "MT":
        if simulacao_mt_rodando: 
            finalizar_simulacao_mt("Simulação resetada.", "black", resetar_botoes=True)
            canvas_fita.delete("all")
            resultado.config(text="")
            status_acao.config(text="Simulação MT resetada.")
            return

        palavra = input_entry.get()
        estado_inicial = next((est for est in estados.values() if est.inicial), None)
        if not estado_inicial:
            resultado.config(text="Erro: Nenhum estado inicial definido.", fg="red")
            return

        simulacao_mt_rodando = True
        botao_simular.config(text="Resetar")
        btn_proximo_passo.config(state="normal")
        btn_passo_anterior.config(state="disabled") 
        for btn in [btn_estado, btn_transicao, btn_selecionar, btn_apagar, btn_salvar]:
            btn.config(state="disabled")
        
        fita_atual = {i: simbolo for i, simbolo in enumerate(palavra) if simbolo} 
        posicao_cabecote_atual = 0
        estado_mt_atual = estado_inicial
        historico_passos_mt = [] 
        
        desenhar_fita(fita_atual, posicao_cabecote_atual)
        resultado.config(text="Pronto para iniciar.", fg="blue")
        simbolo_lido = fita_atual.get(0, SIMBOLO_BRANCO)
        status_acao.config(text=f"Pronto. Estado: {estado_mt_atual.nome}, Lendo: {simbolo_lido}")
        return 
    
    palavra = input_entry.get()
    resultado.config(text="Simulando...")
    sequencia_saida.config(text="Saída: ")
    estado_inicial = next((est for est in estados.values() if est.inicial), None)
    if not estado_inicial:
        resultado.config(text="Erro: Nenhum estado inicial definido.", fg="red")
        return
    historico = []
        
    if tipo_automato_atual == "AFD":
        simular_passo_a_passo_AFD(palavra, estado_inicial)
    elif tipo_automato_atual in ["AFNe", "AFN"]:
        estados_atuais = calcular_fecho_epsilon({estado_inicial})
        simular_passo_a_passo_AFNe(palavra, estados_atuais, "")
    elif tipo_automato_atual == "AP":
        simular_AP(palavra, estado_inicial) 
    elif tipo_automato_atual == "Mealy":
        simular_passo_a_passo_Mealy(palavra, estado_inicial, "", historico)
    elif tipo_automato_atual == "Moore":
        saida_inicial = estado_inicial.simbolo_saida
        sequencia_saida.config(text=f"Saída: {saida_inicial}")
        passo_zero = { "Passo": 0, "Estado Atual": estado_inicial.nome, "Lendo Símbolo": "", "Saída Gerada": saida_inicial, "Próximo Estado": estado_inicial.nome }
        historico.append(passo_zero)
        simular_passo_a_passo_Moore(palavra, estado_inicial, saida_inicial, historico)

def finalizar_simulacao_mt(status_msg, cor="black", resetar_botoes=True):
    # (Esta função permanece a mesma da v14)
    global simulacao_mt_rodando, estado_mt_atual
    simulacao_mt_rodando = False
    estado_mt_atual = None 
    
    resultado.config(text=status_msg, fg=cor)
    
    if resetar_botoes:
        botao_simular.config(text="Simular")
        btn_proximo_passo.config(state="disabled")
        btn_passo_anterior.config(state="normal" if historico_passos_mt else "disabled")
        for btn in [btn_estado, btn_transicao, btn_selecionar, btn_apagar, btn_salvar]:
            btn.config(state="normal")

def executar_proximo_passo_mt():
    # (Esta função permanece a mesma da v14)
    global simulacao_mt_rodando, fita_atual, posicao_cabecote_atual, estado_mt_atual, historico_passos_mt
    
    if not simulacao_mt_rodando:
        return 

    estado_atual = estado_mt_atual 
    if not estado_atual:
        finalizar_simulacao_mt("Erro: Estado atual nulo.", "red")
        return

    historico_passos_mt.append((estado_mt_atual, dict(fita_atual), posicao_cabecote_atual))
    btn_passo_anterior.config(state="normal") 

    if estado_atual.aceitacao:
        finalizar_simulacao_mt("Palavra aceita ✅ (Halt)", "green", resetar_botoes=True)
        return

    simbolo_lido = fita_atual.get(posicao_cabecote_atual, SIMBOLO_BRANCO)
    
    transicao_encontrada = next(
        (t for t in transicoes 
         if t.origem == estado_atual and t.simbolo_leitura == simbolo_lido), 
        None
    )
    
    if not transicao_encontrada:
        finalizar_simulacao_mt(f"Rejeitada ❌ (Preso em '{simbolo_lido}')", "red", resetar_botoes=True)
        return
        
    t = transicao_encontrada
    fita_atual[posicao_cabecote_atual] = t.simbolo_escrita
    
    if t.movimento_cabecote == "R":
        posicao_cabecote_atual += 1
    elif t.movimento_cabecote == "L":
        posicao_cabecote_atual -= 1
    
    estado_mt_atual = t.destino 
    
    desenhar_fita(fita_atual, posicao_cabecote_atual)
    simbolo_lido_proximo = fita_atual.get(posicao_cabecote_atual, SIMBOLO_BRANCO)
    status_acao.config(text=f"Estado: {estado_mt_atual.nome}, Lendo: {simbolo_lido_proximo}")

def executar_passo_anterior_mt():
    # (Esta função permanece a mesma da v14)
    global simulacao_mt_rodando, fita_atual, posicao_cabecote_atual, estado_mt_atual, historico_passos_mt
    
    if not historico_passos_mt:
        return 

    if not simulacao_mt_rodando:
        simulacao_mt_rodando = True
        botao_simular.config(text="Resetar")
        for btn in [btn_estado, btn_transicao, btn_selecionar, btn_apagar, btn_salvar]:
            btn.config(state="disabled")

    estado_mt_atual, fita_atual, posicao_cabecote_atual = historico_passos_mt.pop()
    
    desenhar_fita(fita_atual, posicao_cabecote_atual)
    
    simbolo_lido_atual = fita_atual.get(posicao_cabecote_atual, SIMBOLO_BRANCO)
    status_acao.config(text=f"RETROCEDEU. Estado: {estado_mt_atual.nome}, Lendo: {simbolo_lido_atual}")
    resultado.config(text="Retrocedeu...", fg="blue")
    
    btn_proximo_passo.config(state="normal")
    if not historico_passos_mt:
        btn_passo_anterior.config(state="disabled")

def simular_AP(palavra, estado_inicial):
    # (Esta função permanece inalterada)
    configuracao_inicial = (estado_inicial, list(palavra), ["Z"]) 
    fila_de_configuracoes = [configuracao_inicial]
    visitados = set()
    limite_passos = 2000 
    passos = 0
    while fila_de_configuracoes and passos < limite_passos:
        passos += 1
        estado_atual, entrada_restante, pilha_atual = fila_de_configuracoes.pop(0)
        config_tuple = (estado_atual.nome, "".join(entrada_restante), "".join(pilha_atual))
        if config_tuple in visitados:
            continue 
        visitados.add(config_tuple)
        if not entrada_restante and estado_atual.aceitacao:
            resultado.config(text="Palavra aceita ✅", fg="green")
            sequencia_saida.config(text="Pilha final: " + "".join(pilha_atual if pilha_atual else ["ε"]))
            return 
        simbolo_lido = entrada_restante[0] if entrada_restante else None
        topo_pilha = pilha_atual[-1] if pilha_atual else None 
        transicoes_aplicaveis = []
        if simbolo_lido:
            for t in transicoes:
                if (t.origem == estado_atual and 
                    t.simbolos_entrada[0] == simbolo_lido and
                    (t.simbolo_pop == topo_pilha or t.simbolo_pop == "ε")):
                    transicoes_aplicaveis.append((t, "consumir_input"))
        for t in transicoes:
             if (t.origem == estado_atual and 
                t.simbolos_entrada[0] == "ε" and
                (t.simbolo_pop == topo_pilha or t.simbolo_pop == "ε")):
                transicoes_aplicaveis.append((t, "movimento_epsilon"))
        for t, tipo_movimento in transicoes_aplicaveis:
            nova_pilha = list(pilha_atual) 
            if t.simbolo_pop == topo_pilha and topo_pilha is not None:
                nova_pilha = pilha_atual[:-1] 
            if t.string_push != "ε":
                nova_pilha.extend(list(reversed(t.string_push)))
            nova_entrada = entrada_restante
            if tipo_movimento == "consumir_input":
                nova_entrada = entrada_restante[1:] 
            fila_de_configuracoes.append((t.destino, nova_entrada, nova_pilha))
    if passos >= limite_passos:
         resultado.config(text="Simulação Parada ❌ (Limite de passos atingido)", fg="orange")
    else:
         resultado.config(text="Palavra rejeitada ❌", fg="red")
    sequencia_saida.config(text="")

def simular_passo_a_passo_AFD(palavra_restante, estado_atual):
    # (Esta função permanece inalterada)
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
    # (Esta função permanece inalterada)
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

def simular_passo_a_passo_Mealy(palavra_restante, estado_atual, saida_acumulada, historico_passos):
    # (Esta função permanece inalterada)
    for est in estados.values(): canvas.itemconfig(est.id_circulo, outline="black", width=2)
    canvas.itemconfig(estado_atual.id_circulo, outline="blue", width=3)
    def limpar_realces_finais():
        for est in estados.values():
            canvas.itemconfig(est.id_circulo, outline="black", width=2)
    if not palavra_restante:
        resultado.config(text="Simulação concluída!", fg="blue")
        sequencia_saida.config(text=f"Saída Final: {saida_acumulada}")
        janela.after(500, lambda: salvar_saida_em_arquivo(input_entry.get(), historico_passos))
        janela.after(2000, limpar_realces_finais)
        return
    simbolo_atual = palavra_restante[0]
    proxima_palavra = palavra_restante[1:]
    transicao_encontrada = next((t for t in transicoes if t.origem == estado_atual and simbolo_atual in t.simbolos_entrada), None)
    if not transicao_encontrada:
        resultado.config(text=f"Rejeitada ❌ (transição inválida para '{simbolo_atual}')", fg="red")
        janela.after(2000, limpar_realces_finais)
        return
    estado_destino = transicao_encontrada.destino
    nova_saida_acumulada = saida_acumulada + transicao_encontrada.simbolo_saida
    passo_info = {
        "Passo": len(historico_passos) + 1, "Estado Atual": estado_atual.nome,
        "Lendo Símbolo": simbolo_atual, "Saída Gerada": transicao_encontrada.simbolo_saida,
        "Próximo Estado": estado_destino.nome
    }
    historico_passos.append(passo_info)
    canvas.itemconfig(transicao_encontrada.tag_unica, fill="red")
    status_acao.config(text=f"Lendo '{simbolo_atual}', gerando '{transicao_encontrada.simbolo_saida}'...")
    sequencia_saida.config(text=f"Saída: {nova_saida_acumulada}")
    def ir_para_proximo_passo():
        canvas.itemconfig(transicao_encontrada.tag_unica, fill="black")
        simular_passo_a_passo_Mealy(proxima_palavra, estado_destino, nova_saida_acumulada, historico_passos)
    janela.after(800, ir_para_proximo_passo)

def simular_passo_a_passo_Moore(palavra_restante, estado_atual, saida_acumulada, historico_passos):
    # (Esta função permanece inalterada)
    for est in estados.values(): canvas.itemconfig(est.id_circulo, outline="black", width=2)
    canvas.itemconfig(estado_atual.id_circulo, outline="blue", width=3)
    def limpar_realces_finais():
        for est in estados.values():
            canvas.itemconfig(est.id_circulo, outline="black", width=2)
    if not palavra_restante:
        resultado.config(text="Simulação concluída!", fg="blue")
        sequencia_saida.config(text=f"Saída Final: {saida_acumulada}")
        janela.after(500, lambda: salvar_saida_em_arquivo(input_entry.get(), historico_passos))
        janela.after(2000, limpar_realces_finais) 
        return
    simbolo_atual = palavra_restante[0]
    proxima_palavra = palavra_restante[1:]
    transicao_encontrada = next((t for t in transicoes if t.origem == estado_atual and simbolo_atual in t.simbolos_entrada), None)
    if not transicao_encontrada:
        resultado.config(text=f"Rejeitada ❌ (transição inválida para '{simbolo_atual}')", fg="red")
        janela.after(2000, limpar_realces_finais) 
        return
    estado_destino = transicao_encontrada.destino
    nova_saida_acumulada = saida_acumulada + estado_destino.simbolo_saida
    passo_info = {
        "Passo": len(historico_passos) + 1,
        "Estado Atual": estado_atual.nome,
        "Lendo Símbolo": simbolo_atual,
        "Saída Gerada": estado_destino.simbolo_saida, 
        "Próximo Estado": estado_destino.nome
    }
    historico_passos.append(passo_info)
    canvas.itemconfig(transicao_encontrada.tag_unica, fill="red")
    status_acao.config(text=f"Lendo '{simbolo_atual}', gerando '{estado_destino.simbolo_saida}'...")
    sequencia_saida.config(text=f"Saída: {nova_saida_acumulada}")
    def ir_para_proximo_passo():
        canvas.itemconfig(transicao_encontrada.tag_unica, fill="black")
        simular_passo_a_passo_Moore(proxima_palavra, estado_destino, nova_saida_acumulada, historico_passos)
    janela.after(800, ir_para_proximo_passo)


# --- Funções de Arquivo ---
def novo_automato():
    global estados, transicoes, contador_estados, caminho_arquivo_atual
    
    if simulacao_mt_rodando:
        finalizar_simulacao_mt("Novo autômato criado.", "black", resetar_botoes=True)

    canvas.delete("all")
    canvas_fita.delete("all") 
    estados, transicoes, historico_passos_mt = {}, [], []
    contador_estados = 0
    caminho_arquivo_atual = None
    resultado.config(text="")
    status_acao.config(text=f"Novo autômato ({tipo_automato_atual}) criado. Clique para começar.")

def _salvar_dados_no_arquivo(caminho):
    # (Esta função permanece a mesma da v14)
    dados = {
        "tipo": tipo_automato_atual,  # 👈 CORRIGIDO!
        "estados": [{"nome": e.nome, "x": e.x, "y": e.y, 
                     "inicial": e.inicial, "aceitacao": e.aceitacao, 
                     "simbolo_saida": e.simbolo_saida} 
                    for e in estados.values()],
        "transicoes": [
            {
                "origem": t.origem.nome, "destino": t.destino.nome, 
                "simbolos_entrada": t.simbolos_entrada, "simbolo_saida": t.simbolo_saida,
                "simbolo_pop": t.simbolo_pop, "string_push": t.string_push,
                "simbolo_leitura": t.simbolo_leitura, "simbolo_escrita": t.simbolo_escrita,
                "movimento_cabocote": t.movimento_cabecote,
                "offset_x": t.offset_x, "offset_y": t.offset_y
            } 
            for t in transicoes
        ]
    }
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)
    status_acao.config(text=f"Autômato salvo em {caminho.split('/')[-1]}")

def salvar():
    if simulacao_mt_rodando: return
    if caminho_arquivo_atual:
        if caminho_arquivo_atual.lower().endswith('.jff'):
            exportar_para_jflap_xml(caminho_arquivo_atual)
        else:
            _salvar_dados_no_arquivo(caminho_arquivo_atual)
    else:
        salvar_como()

def salvar_como():
    if simulacao_mt_rodando: return
    global caminho_arquivo_atual
    arquivo = filedialog.asksaveasfilename(
        defaultextension=".json", 
        filetypes=[("JSON files", "*.json"), ("JFLAP files", "*.jff"), ("All files", "*.*")]
    )
    if not arquivo: return
    caminho_arquivo_atual = arquivo
    if caminho_arquivo_atual.lower().endswith('.jff'):
        exportar_para_jflap_xml(caminho_arquivo_atual)
    else: 
        _salvar_dados_no_arquivo(caminho_arquivo_atual)

def salvar_saida_em_arquivo(palavra_entrada, historico_passos):
    # (Esta função permanece inalterada)
    if not historico_passos: return
    string_saida = "".join([passo["Saída Gerada"] for passo in historico_passos])
    confirmar = messagebox.askyesno(
        "Salvar Relatório de Simulação",
        f"A simulação para a entrada '{palavra_entrada}' gerou a saída: '{string_saida}'\n\n"
        "Deseja salvar um relatório detalhado (.csv)?"
    )
    if confirmar:
        nome_sugerido = f"relatorio_{palavra_entrada}.csv" if palavra_entrada else "relatorio.csv"
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Arquivo CSV", "*.csv"), ("Todos os arquivos", "*.*")],
            initialfile=nome_sugerido
        )
        if arquivo:
            try:
                with open(arquivo, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(["Palavra de Entrada", palavra_entrada])
                    writer.writerow(["Palavra de Saída", string_saida])
                    writer.writerow([])
                    headers = historico_passos[0].keys()
                    writer.writerow(headers)
                    for passo in historico_passos:
                        writer.writerow(passo.values())
                status_acao.config(text=f"Relatório salvo em {arquivo.split('/')[-1]}")
            except Exception as e:
                messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o relatório:\n{e}")

# --- MODIFICADO: Correção do bug 'caminho' (v16) ---
def exportar_para_jflap_xml(caminho_arquivo):
    global tipo_automato_atual
    raiz = ET.Element('structure')
    
    if tipo_automato_atual == "AP":
        ET.SubElement(raiz, 'type').text = "pda"
    elif tipo_automato_atual == "MT":
        ET.SubElement(raiz, 'type').text = "turing" 
    else:
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
        
        if tipo_automato_atual == "AP":
            simbolo_input = transicao.simbolos_entrada[0] 
            read_tag = ET.SubElement(t_xml, 'read')
            if simbolo_input.lower() != "ε": read_tag.text = simbolo_input
            simbolo_pop = transicao.simbolo_pop
            pop_tag = ET.SubElement(t_xml, 'pop')
            if simbolo_pop.lower() != "ε": pop_tag.text = simbolo_pop
            string_push = transicao.string_push
            push_tag = ET.SubElement(t_xml, 'push')
            if string_push.lower() != "ε": push_tag.text = string_push

        elif tipo_automato_atual == "MT":
            simbolo_read = transicao.simbolo_leitura
            read_tag = ET.SubElement(t_xml, 'read')
            if simbolo_read != SIMBOLO_BRANCO and simbolo_read: 
                 read_tag.text = simbolo_read
            simbolo_write = transicao.simbolo_escrita
            write_tag = ET.SubElement(t_xml, 'write')
            if simbolo_write != SIMBOLO_BRANCO and simbolo_write:
                write_tag.text = simbolo_write
            move_tag = ET.SubElement(t_xml, 'move')
            move_tag.text = transicao.movimento_cabecote 
        else:
            simbolo_input = transicao.simbolos_entrada[0] 
            read_tag = ET.SubElement(t_xml, 'read')
            if simbolo_input.lower() != "ε":
                read_tag.text = simbolo_input

    xml_string = ET.tostring(raiz, encoding='utf-8')
    reparsed = minidom.parseString(xml_string) 
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(reparsed.toprettyxml(indent="  "))
  
    # --- CORREÇÃO APLICADA AQUI (v16) ---
    status_acao.config(text=f"Exportado para JFLAP XML (JFF) em: {caminho_arquivo.split('/')[-1]}")
    # --- FIM DA CORREÇÃO ---

def atalho_salvar(event):
    if simulacao_mt_rodando: return
    salvar()
    print("Atalho Ctrl+S acionado: arquivo salvo.")

def abrir_automato():
    if simulacao_mt_rodando: return
    global caminho_arquivo_atual
    arquivo = filedialog.askopenfilename(
        filetypes=[
            ("Todos os Arquivos de Autômato", "*.jff;*.json"),
            ("JFLAP files", "*.jff"),
            ("JSON files", "*.json")
        ]
    )
    if not arquivo: return
    caminho_arquivo_atual = arquivo
    
    if caminho_arquivo_atual.lower().endswith('.jff'):
        if importar_de_jflap_xml(caminho_arquivo_atual):
            # A própria função de importação já atualiza o status
            pass 
            
    elif caminho_arquivo_atual.lower().endswith('.json'):
        # _carregar_dados_json agora faz a troca de modo E atualiza o status
        _carregar_dados_json(caminho_arquivo_atual)
        
    else:
        messagebox.showwarning("Erro de Formato", "Formato de arquivo não reconhecido. Tente .jff ou .json.")
    
    corrigir_desvios_carregados()

def _carregar_dados_json(arquivo):
    global estados, transicoes, contador_estados, tipo_automato_atual, caminho_arquivo_atual

    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        # 1. Detecta o tipo do arquivo.
        novo_tipo = dados.get("tipo", "AFNe") # Padrão AFNe se a chave "tipo" não existir
        
        # 2. CHAMA definir_tipo_automato FORÇADAMENTE
        # Isto vai limpar o canvas (chamando novo_automato) e definir o modo
        definir_tipo_automato(novo_tipo, forcar=True) 
        
        # 3. Restaura o caminho do arquivo (que novo_automato() limpou)
        caminho_arquivo_atual = arquivo

        # 4. Carrega os dados no canvas agora limpo e com o modo correto
        for e_data in dados["estados"]:
            estado = Estado(e_data["nome"], e_data["x"], e_data["y"], canvas)
            estados[e_data["nome"]] = estado
            if e_data.get("inicial"): estado.set_inicial()
            if e_data.get("aceitacao"): estado.set_aceitacao(True)
            estado.simbolo_saida = e_data.get("simbolo_saida", "")
            estado.atualizar_texto()
            
        if estados:
            numeros_estado = [int(nome.replace('q', '')) for nome in estados.keys() if nome.startswith('q') and nome[1:].isdigit()]
            if numeros_estado:
                contador_estados = max(numeros_estado) + 1
            else:
                contador_estados = 1 
                
        for t_data in dados["transicoes"]:
            origem, destino = estados.get(t_data["origem"]), estados.get(t_data["destino"])
            if not origem or not destino: continue
            transicoes.append(Transicao(
                origem, destino, canvas, 
                t_data.get("simbolos_entrada", ["ε"]), 
                t_data.get("simbolo_saida", ""),
                t_data.get("simbolo_pop", "ε"),
                t_data.get("string_push", "ε"),
                t_data.get("simbolo_leitura", SIMBOLO_BRANCO),
                t_data.get("simbolo_escrita", SIMBOLO_BRANCO),
                t_data.get("movimento_cabecote", "S"),
                t_data.get("offset_x", 0), 
                t_data.get("offset_y", 0)
            ))
        
        status_acao.config(text=f"Autômato JSON ({novo_tipo}) carregado de {arquivo.split('/')[-1]}")
        
    except Exception as e:
        messagebox.showerror("Erro ao Carregar JSON", f"Não foi possível ler o ficheiro JSON:\n{e}")
        novo_automato()

def importar_de_jflap_xml(caminho_arquivo):
    global estados, transicoes, contador_estados, tipo_automato_atual, caminho_arquivo_atual 
    try:
        tree = ET.parse(caminho_arquivo)
        raiz = tree.getroot()
        
        # 1. Detecta o tipo
        tipo_xml = raiz.find('type')
        novo_tipo = "AFNe" # Padrão
        if tipo_xml is not None:
            if tipo_xml.text == "pda":
                novo_tipo = "AP"
            elif tipo_xml.text == "turing":
                novo_tipo = "MT"

        # 2. CHAMA definir_tipo_automato FORÇADAMENTE
        definir_tipo_automato(novo_tipo, forcar=True)
        caminho_arquivo_atual = caminho_arquivo # Restaura o caminho
        # --- FIM DA LÓGICA CORRIGIDA ---

        mapa_id_nome = {}
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
                
        if estados:
            numeros_estado = [int(n.replace('q', '')) for n in estados.keys() if n.startswith('q') and n[1:].isdigit()]
            if numeros_estado:
                contador_estados = max(numeros_estado) + 1
                
        for t_xml in raiz.findall('./automaton/transition'):
            origem = estados.get(mapa_id_nome.get(t_xml.find('from').text))
            destino = estados.get(mapa_id_nome.get(t_xml.find('to').text))
            if not origem or not destino: continue
            
            simbolo_input, simbolo_pop, string_push = "ε", "ε", "ε"
            simbolo_read, simbolo_write, move = SIMBOLO_BRANCO, SIMBOLO_BRANCO, "S"

            if tipo_automato_atual == "MT":
                read_element = t_xml.find('read')
                simbolo_read = read_element.text if read_element is not None and read_element.text is not None else SIMBOLO_BRANCO
                write_element = t_xml.find('write')
                simbolo_write = write_element.text if write_element is not None and write_element.text is not None else SIMBOLO_BRANCO
                move_element = t_xml.find('move')
                move = move_element.text if move_element is not None else "S"
            elif tipo_automato_atual == "AP":
                read_element = t_xml.find('read')
                simbolo_input = read_element.text if read_element is not None and read_element.text else 'ε'
                pop_element = t_xml.find('pop')
                simbolo_pop = pop_element.text if pop_element is not None and pop_element.text else 'ε'
                push_element = t_xml.find('push')
                string_push = push_element.text if push_element is not None and push_element.text else 'ε'
            else: # AFs
                read_element = t_xml.find('read')
                simbolo_input = read_element.text if read_element is not None and read_element.text else 'ε'

            transicoes.append(Transicao(
                origem, destino, canvas, 
                simbolos_entrada=simbolo_input, simbolo_pop=simbolo_pop, string_push=string_push,
                simbolo_leitura=simbolo_read, simbolo_escrita=simbolo_write, movimento_cabecote=move
            ))
        return True
    except Exception as e:
        messagebox.showerror("Erro de Importação JFLAP", f"Erro ao carregar o arquivo JFLAP: {e}")
        novo_automato() 
        return False
    
# --- MODIFICADO: Lógica de correção de loop atualizada (v16) ---
def corrigir_desvios_carregados():
    pares_verificados = set()
    for t1 in transicoes:
        for t2 in transicoes:
            if t1 == t2 or tuple(sorted((id(t1), id(t2)))) in pares_verificados: continue
            # Corrige linhas paralelas
            if t1.origem == t2.destino and t1.destino == t2.origem:
                if t1.offset_x == 0 and t2.offset_x == 0: 
                    estado_origem, estado_destino = t1.origem, t1.destino
                    dist = math.dist((estado_origem.x, estado_origem.y), (estado_destino.x, estado_destino.y))
                    if dist == 0: dist = 1
                    vetor_x, vetor_y = (estado_destino.x - estado_origem.x) / dist, (estado_destino.y - estado_origem.y) / dist
                    vetor_perp_x, vetor_perp_y = -vetor_y, vetor_x
                    offset_dist = 15 
                    t1.offset_x, t1.offset_y = vetor_perp_x * offset_dist, vetor_perp_y * offset_dist
                    t1.atualizar_posicao()
                    t2.offset_x, t2.offset_y = -vetor_perp_x * offset_dist, -vetor_perp_y * offset_dist
                    t2.atualizar_posicao()
                pares_verificados.add(tuple(sorted((id(t1), id(t2))))) 

    # --- LÓGICA DE LOOP SUBSTITUÍDA (v16) ---
    # Agrupa todos os estados que têm loops e recalcula
    estados_com_loops = {t.origem for t in transicoes if t.is_loop}
    for estado in estados_com_loops:
        recalcular_offsets_loops(estado)
    # --- FIM DA SUBSTITUIÇÃO ---


# --- UI Setup ---
janela = tk.Tk()
janela.title("Mini-JFLAP em Python v17") # <-- Título atualizado
janela.geometry("900x750") 

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

menu_tipo = tk.Menu(menu_bar, tearoff=0)
menu_tipo.add_command(label="Autômato Finito Determinístico (AFD)", command=lambda: definir_tipo_automato("AFD"))
menu_tipo.add_command(label="Autômato Finito Não Determinístico (AFN)", command=lambda: definir_tipo_automato("AFN")) 
menu_tipo.add_command(label="Autômato Finito Não Determinístico com ε (AFNe)", command=lambda: definir_tipo_automato("AFNe")) 
menu_tipo.add_separator() 
menu_tipo.add_command(label="Máquina de Mealy", command=lambda: definir_tipo_automato("Mealy")) 
menu_tipo.add_command(label="Máquina de Moore", command=lambda: definir_tipo_automato("Moore")) 
menu_tipo.add_separator() 
menu_tipo.add_command(label="Autômato com Pilha (AP)", command=lambda: definir_tipo_automato("AP")) 
menu_tipo.add_command(label="Máquina de Turing (MT)", command=lambda: definir_tipo_automato("MT"))
menu_bar.add_cascade(label="Tipo de Autômato", menu=menu_tipo)
janela.config(menu=menu_bar)

# --- Toolbar ---
toolbar = tk.Frame(janela, bd=1, relief=tk.RAISED)
toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
icones = {}
try:
    nomes_icones = ["selecionar", "estado", "transicao", "apagar", "salvar"]
    for nome in nomes_icones:
        # --- LINHA MODIFICADA ---
        caminho_icone = resource_path(f"icones/{nome}.png")
        # --- FIM DA MODIFICAÇÃO ---
        img = Image.open(caminho_icone).resize((24, 24), Image.Resampling.LANCZOS)
        icones[nome] = ImageTk.PhotoImage(img)
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
btn_selecionar = criar_botao_toolbar(toolbar, "selecionar", "Selecionar", ativar_modo_selecao) 
btn_apagar = criar_botao_toolbar(toolbar, "apagar", "Apagar", ativar_modo_apagar)
tk.Frame(toolbar, height=30, width=2, bg="grey").pack(side=tk.LEFT, padx=5, pady=2)
btn_salvar = criar_botao_toolbar(toolbar, "salvar", "Salvar", salvar)

# --- Canvas Principal ---
canvas = tk.Canvas(janela, bg="white", highlightthickness=1, highlightbackground="black") 
canvas.pack(fill="both", expand=True, padx=10, pady=10) 
canvas.bind("<ButtonPress-1>", iniciar_movimento) 
canvas.bind("<Double-Button-1>", gerenciar_clique_duplo) 
canvas.bind("<B1-Motion>", arrastar_objeto) 
canvas.bind("<ButtonRelease-1>", finalizar_arraste) 
canvas.bind("<Button-2>", cancelar_criacao_transicao)  
canvas.bind("<Button-3>", mostrar_menu_contexto) 
janela.bind("<Key>", gerenciar_atalhos_teclado) 
janela.bind("<Control-s>", atalho_salvar) 

# --- Painel Inferior (Status Bar) ---
status_bar = tk.Frame(janela, bd=1, relief=tk.SUNKEN)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)
status_modo = tk.Label(status_bar, text="", bd=1, relief=tk.FLAT, anchor=tk.W)
status_modo.pack(side=tk.LEFT, padx=5, pady=2)
status_acao = tk.Label(status_bar, text="Bem-vindo!", bd=1, relief=tk.FLAT, anchor=tk.E)
status_acao.pack(side=tk.RIGHT, padx=5, pady=2)

# --- Painel de Simulação (com botões de passo-a-passo) ---
painel_simulacao = tk.Frame(janela)
tk.Label(painel_simulacao, text="Palavra:", font=("Arial", 10)).pack(side=tk.LEFT, padx=2)
input_entry = tk.Entry(painel_simulacao, width=30)
input_entry.pack(side=tk.LEFT, padx=2)

botao_simular = tk.Button(painel_simulacao, text="Simular", command=simular_palavra)
botao_simular.pack(side=tk.LEFT, padx=2)

btn_passo_anterior = tk.Button(painel_simulacao, text="◀ Anterior", command=executar_passo_anterior_mt, state="disabled")
btn_passo_anterior.pack(side=tk.LEFT, padx=(5, 2))

btn_proximo_passo = tk.Button(painel_simulacao, text="Próximo ▶", command=executar_proximo_passo_mt, state="disabled")
btn_proximo_passo.pack(side=tk.LEFT, padx=2)

resultado = tk.Label(painel_simulacao, text="", font=("Arial", 12, "bold"))
resultado.pack(side=tk.LEFT, padx=5)
sequencia_saida = tk.Label(painel_simulacao, text="Saída: ", font=("Arial", 12))  
sequencia_saida.pack(side=tk.LEFT, padx=5)

# --- Painel da Fita da MT ---
painel_fita = tk.Frame(janela, height=70, bd=1, relief=tk.SUNKEN)
canvas_fita = tk.Canvas(painel_fita, bg="#f0f0f0", height=65)
canvas_fita.pack(fill="x", expand=True, padx=5, pady=5)

# --- Ordem de Empacotamento da UI ---
painel_fita.pack(side=tk.BOTTOM, fill="x", padx=10, pady=5)
painel_simulacao.pack(side=tk.BOTTOM, fill="x", padx=10, pady=5)

# Inicia o programa
definir_tipo_automato("AFNe") 
ativar_modo_arrastar()
janela.mainloop()
