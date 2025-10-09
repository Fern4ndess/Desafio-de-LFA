import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, colorchooser
from PIL import Image, ImageTk
import json
import math
import xml.etree.ElementTree as ET # <-- NOVA IMPORTAÇÃO
from xml.dom import minidom        # <-- NOVA IMPORTAÇÃO
import csv # <-- NOVA LINHA v11

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

    def atualizar_texto(self):
        """Atualiza o texto do estado no canvas para incluir a saída (se aplicável)."""
        texto_display = self.nome
        # Em modo Moore, se houver símbolo de saída, exibe "nome/saida"
        if tipo_automato_atual == "Moore" and self.simbolo_saida:
            texto_display = f"{self.nome}/{self.simbolo_saida}"
        self.canvas.itemconfig(self.id_texto, text=texto_display)

    def selecionar(self):
        self.canvas.itemconfig(self.id_circulo, outline="green", width=3)
    def desselecionar(self):
        self.canvas.itemconfig(self.id_circulo, outline="black", width=2)

    # Dentro da class Estado
    # Dentro da class Estado
    def redesenhar(self):
        """Redesenha todos os componentes visuais do estado no canvas."""
        # Recria o círculo e o texto
        self.id_circulo = self.canvas.create_oval(
            self.x - self.raio, self.y - self.raio, self.x + self.raio, self.y + self.raio,
            fill=self.canvas.itemcget(self.id_circulo, "fill"), # Mantém a cor atual
            outline="black", width=2, tags=("estado", self.nome)
        )
        self.id_texto = self.canvas.create_text(
            self.x, self.y, text=self.nome, font=("Arial", 12, "bold"), tags=("texto", self.nome)
        )
        
        # Recria a marcação de inicial, se necessário
        if self.inicial:
            # Apaga qualquer seta antiga para evitar duplicatas
            for item in self.canvas.find_withtag(f"seta_inicial_{self.nome}"): self.canvas.delete(item)
            self.set_inicial() # Recria a seta
            
        # Recria a marcação de aceitação, se necessário
        if self.aceitacao:
            # Chama o método set_aceitacao diretamente, que é mais seguro
            self.set_aceitacao(True)


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
        
        # Garante que o arco tenha a tag_unica
        self.canvas.create_arc(bounding_box, start=210, extent=-240, style=tk.ARC, 
                               outline="black", width=2, tags=(self.tag_unica, "transicao"))
        
        angulo_final_rad = math.radians(-30)
        centro_arco_x, centro_arco_y = x, y - raio_estado
        ponta_x = centro_arco_x + raio_loop * math.cos(angulo_final_rad)
        ponta_y = centro_arco_y - raio_loop * math.sin(angulo_final_rad)
        ponta1, ponta2, ponta3 = (ponta_x, ponta_y), (ponta_x - 10, ponta_y - 2), (ponta_x - 2, ponta_y + 8)
        
        # Garante que o polígono da seta tenha a tag_unica
        self.canvas.create_polygon(ponta1, ponta2, ponta3, fill="black", tags=(self.tag_unica, "transicao"))
        
        coords_texto = (x, y - raio_estado - raio_loop - 20)
        
        # Garante que o texto do rótulo tenha a tag_unica
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

    # Dentro da class Transicao
    def destruir(self):
        """Versão de depuração para encontrar o 'loop fantasma'."""
        print("-" * 20)
        print(f"--> Iniciando 'destruir' para a transição com tag: {self.tag_unica}")
        
        # Procura por todos os itens no canvas que têm essa tag
        itens_encontrados = self.canvas.find_withtag(self.tag_unica)
        
        if not itens_encontrados:
            print("!!! ALERTA: Nenhum componente visual foi encontrado com esta tag!")
        else:
            print(f"    Encontrados {len(itens_encontrados)} componentes visuais para apagar:")
            for item_id in itens_encontrados:
                # Para cada item, mostra suas tags
                print(f"    - ID do item: {item_id}, Tags: {self.canvas.gettags(item_id)}")
        
        # Executa o comando de apagar
        self.canvas.delete(self.tag_unica)
        print(f"<-- Comando de exclusão para '{self.tag_unica}' executado.")
        print("-" * 20)
        
    def selecionar(self):
        self.canvas.itemconfig(self.tag_unica, fill="green")

    def desselecionar(self):
        self.atualizar_posicao()

# --- Classes de Comando (para Undo/Redo) ---]
class Comando:
    """Classe base para todas as ações que podem ser desfeitas."""
    def executar(self):
        raise NotImplementedError
    def desfazer(self):
        raise NotImplementedError

class ComandoCriarEstado(Comando):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.estado_criado = None
        self.nome_original = None # NOVO: Para lembrar o nome

    def executar(self):
        global contador_estados
        
        # Se estamos refazendo, usa o nome original. Senão, cria um novo nome.
        if self.nome_original:
            nome_estado = self.nome_original
        else:
            nome_estado = f"q{contador_estados}"
            self.nome_original = nome_estado # Guarda o nome para o futuro
            contador_estados += 1

        self.estado_criado = Estado(nome_estado, self.x, self.y, canvas)
        estados[nome_estado] = self.estado_criado
        
        # Lógica para definir como inicial (pode ser aprimorada no futuro)
        is_initial = not any(est.inicial for est in estados.values() if est != self.estado_criado)
        if is_initial:
            self.estado_criado.set_inicial()

        print(f"Comando Executado: Criar Estado {nome_estado}")
        return True

    def desfazer(self):
        # Não precisamos mais mexer no contador global aqui
        if self.estado_criado:
            nome_estado = self.estado_criado.nome
            self.estado_criado.destruir()
            del estados[nome_estado]
            print(f"Comando Desfeito: Apagar Estado {nome_estado}")

class ComandoApagarTransicao(Comando):
    def __init__(self, transicao_a_apagar):
        # A "ordem" precisa saber qual transição ela é responsável por apagar.
        self.transicao_apagada = transicao_a_apagar

    def executar(self):
        """Ação de apagar: remove a transição da lista e da tela."""
        if self.transicao_apagada in transicoes:
            self.transicao_apagada.destruir()
            transicoes.remove(self.transicao_apagada)
            print(f"Comando Executado: Apagar Transição")
            return True
        return False # Não executou se a transição já não existia

    def desfazer(self):
        """Ação de desfazer: coloca a transição de volta na lista e a redesenha."""
        if self.transicao_apagada not in transicoes:
            transicoes.append(self.transicao_apagada)
            self.transicao_apagada.atualizar_posicao() # Redesenha a transição
            print(f"Comando Desfeito: Restaurar Transição")

class ComandoCriarTransicao(Comando):
    def __init__(self, origem, destino):
        self.origem = origem
        self.destino = destino
        self.transicao_criada = None
        self.transicao_gemea = None
        self.offset_original_gemea = (0, 0)

    def executar(self):
        # Cria a nova transição
        self.transicao_criada = Transicao(self.origem, self.destino, canvas)
        transicoes.append(self.transicao_criada)

        # Procura por uma transição gêmea
        self.transicao_gemea = next((t for t in transicoes if t.origem == self.destino and t.destino == self.origem), None)

        if self.transicao_gemea:
            # Guarda o estado original da gêmea antes de modificá-la
            self.offset_original_gemea = (self.transicao_gemea.offset_x, self.transicao_gemea.offset_y)
            
            # Aplica o desvio em ambas
            dist = math.dist((self.origem.x, self.origem.y), (self.destino.x, self.destino.y))
            if dist == 0: dist = 1
            vetor_x = (self.destino.x - self.origem.x) / dist
            vetor_y = (self.destino.y - self.origem.y) / dist
            vetor_perp_x, vetor_perp_y = -vetor_y, vetor_x
            offset_dist = 15

            self.transicao_criada.offset_x = vetor_perp_x * offset_dist
            self.transicao_criada.offset_y = vetor_perp_y * offset_dist
            self.transicao_criada.atualizar_posicao()

            self.transicao_gemea.offset_x = -vetor_perp_x * offset_dist
            self.transicao_gemea.offset_y = -vetor_perp_y * offset_dist
            self.transicao_gemea.atualizar_posicao()
        
        print("Comando Executado: Criar Transição")
        return True

    def desfazer(self):
        # Apaga a transição que foi criada
        self.transicao_criada.destruir()
        transicoes.remove(self.transicao_criada)

        # Se uma transição gêmea foi modificada, restaura ela ao seu estado original
        if self.transicao_gemea:
            self.transicao_gemea.offset_x, self.transicao_gemea.offset_y = self.offset_original_gemea
            self.transicao_gemea.atualizar_posicao()
            
        print("Comando Desfeito: Criar Transição")

class ComandoToggleAceitacao(Comando):
    def __init__(self, estados_para_alternar):
        # Esta classe é inteligente, ela aceita uma lista ou conjunto de estados
        self.estados_afetados = list(estados_para_alternar)

    def executar(self):
        for estado in self.estados_afetados:
            estado.toggle_aceitacao()
        print(f"Comando Executado: Alternar aceitação para {len(self.estados_afetados)} estado(s).")
        return True

    def desfazer(self):
        # A ação de desfazer um 'toggle' é simplesmente fazer o 'toggle' de novo!
        for estado in self.estados_afetados:
            estado.toggle_aceitacao()
        print(f"Comando Desfeito: Alternar aceitação para {len(self.estados_afetados)} estado(s).")

class ComandoAlterarCor(Comando):
    def __init__(self, estados_para_alterar):
        self.estados_afetados = list(estados_para_alterar)
        self.cores_antigas = {}
        self.nova_cor = None

    def executar(self):
        # Primeiro, abre a caixa de diálogo para escolher a cor
        cor_escolhida = colorchooser.askcolor(title="Escolha a nova cor")
        if not cor_escolhida or not cor_escolhida[1]:
            return False # Usuário cancelou, a ação não foi executada

        self.nova_cor = cor_escolhida[1] # Guarda o código hexadecimal (ex: "#ffffff")
        
        # Antes de mudar, guarda as cores antigas de cada estado
        for estado in self.estados_afetados:
            cor_antiga = canvas.itemcget(estado.id_circulo, "fill")
            self.cores_antigas[estado] = cor_antiga
        
        # Aplica a nova cor a todos os estados
        for estado in self.estados_afetados:
            canvas.itemconfig(estado.id_circulo, fill=self.nova_cor)

        print(f"Comando Executado: Mudar cor para {len(self.estados_afetados)} estado(s).")
        return True

    def desfazer(self):
        # Restaura a cor antiga de cada estado, uma por uma
        for estado in self.estados_afetados:
            cor_original = self.cores_antigas.get(estado)
            if cor_original:
                canvas.itemconfig(estado.id_circulo, fill=cor_original)
        print(f"Comando Desfeito: Restaurar cor para {len(self.estados_afetados)} estado(s).")

class ComandoRenomearEstado(Comando):
    def __init__(self, estado_para_renomear):
        self.estado = estado_para_renomear
        self.nome_antigo = None
        self.nome_novo = None

    def _aplicar_rename(self, de, para):
        """Função auxiliar para aplicar a renomeação (em qualquer direção)."""
        # Atualiza tags
        ids_componentes = canvas.find_withtag(de)
        for item_id in ids_componentes:
            tags_atuais = list(canvas.gettags(item_id))
            novas_tags = [para if t == de else t for t in tags_atuais]
            canvas.itemconfig(item_id, tags=tuple(novas_tags))
        # Atualiza texto
        canvas.itemconfig(self.estado.id_texto, text=para)
        # Atualiza objeto e dicionário
        self.estado.nome = para
        estados[para] = estados.pop(de)

    def executar(self):
        self.nome_antigo = self.estado.nome
        novo_nome = simpledialog.askstring("Renomear Estado", f"Digite o novo nome para '{self.nome_antigo}':", initialvalue=self.nome_antigo)
        
        if novo_nome and novo_nome != self.nome_antigo:
            if novo_nome in estados:
                messagebox.showwarning("Erro", "O nome inserido já existe.")
                return False
            
            self.nome_novo = novo_nome
            self._aplicar_rename(self.nome_antigo, self.nome_novo)
            print(f"Comando Executado: Renomear {self.nome_antigo} -> {self.nome_novo}")
            return True
        return False

    def desfazer(self):
        if self.nome_antigo and self.nome_novo:
            self._aplicar_rename(self.nome_novo, self.nome_antigo)
            print(f"Comando Desfeito: Renomear {self.nome_novo} -> {self.nome_antigo}")

class ComandoEditarTransicao(Comando):
    def __init__(self, transicao):
        self.transicao = transicao
        self.simbolos_antigos = None
        self.simbolo_saida_antigo = None
        self.novo_rotulo = None

    def executar(self):
        # Guarda o estado antigo
        self.simbolos_antigos = list(self.transicao.simbolos_entrada)
        self.simbolo_saida_antigo = self.transicao.simbolo_saida

        # Abre o diálogo para o usuário
        valor_inicial = self.transicao._get_rotulo_texto()
        # A lógica de qual diálogo abrir está na função 'editar_rotulo_transicao'
        # Aqui, vamos chamar a função, mas de uma forma que possamos capturar o resultado.
        # Por simplicidade, vamos mover a lógica do diálogo para DENTRO do comando.
        
        # (Lógica movida de editar_rotulo_transicao para cá)
        if tipo_automato_atual in ["AFD", "AFN", "AFNe", "Moore"]:
            self.novo_rotulo = simpledialog.askstring(f"Editar Símbolos ({tipo_automato_atual})", "Símbolos de entrada:", initialvalue=valor_inicial)
        elif tipo_automato_atual == "Mealy":
            self.novo_rotulo = simpledialog.askstring("Editar Transição (Mealy)", "Formato: entrada / saida", initialvalue=valor_inicial)

        if self.novo_rotulo is not None:
            # Aplica a atualização (a função 'atualizar_simbolo' já parseia o texto)
            self.transicao.atualizar_simbolo(self.novo_rotulo)
            print("Comando Executado: Editar Transição")
            return True
        return False # Usuário cancelou

    def desfazer(self):
        # Restaura os valores antigos
        self.transicao.simbolos_entrada = self.simbolos_antigos
        self.transicao.simbolo_saida = self.simbolo_saida_antigo
        self.transicao.atualizar_posicao() # Redesenha com os valores antigos
        print("Comando Desfeito: Reverter Edição de Transição")

class ComandoMover(Comando):
    def __init__(self, itens_para_mover, dx, dy):
        self.itens_movidos = set(itens_para_mover)
        self.dx = dx
        self.dy = dy

    def executar(self):
        for item in self.itens_movidos:
            item.mover(self.dx, self.dy)
            atualizar_transicoes_conectadas(item)
        print(f"Comando Executado: Mover {len(self.itens_movidos)} item(ns)")
        return True

    def desfazer(self):
        for item in self.itens_movidos:
            item.mover(-self.dx, -self.dy)
            atualizar_transicoes_conectadas(item)
        print(f"Comando Desfeito: Mover {len(self.itens_movidos)} item(ns)")

class ComandoApagar(Comando):
    def __init__(self, itens_para_apagar):
        # Guarda os itens que o usuário mandou apagar
        self.itens_apagados_diretamente = set(itens_para_apagar)
        # Guarda as transições que serão apagadas como consequência
        self.transicoes_em_cascata = set()

    def executar(self):
        estados_a_apagar = {item for item in self.itens_apagados_diretamente if isinstance(item, Estado)}
        
        # Encontra e guarda as transições conectadas aos estados que serão apagados
        for t in transicoes:
            if t.origem in estados_a_apagar or t.destino in estados_a_apagar:
                if t not in self.itens_apagados_diretamente:
                    self.transicoes_em_cascata.add(t)

        # Junta todas as transições que devem sumir
        todas_transicoes_a_apagar = self.itens_apagados_diretamente.union(self.transicoes_em_cascata)

        # Executa a exclusão
        for item in todas_transicoes_a_apagar:
            if isinstance(item, Transicao) and item in transicoes:
                item.destruir()
                transicoes.remove(item)
        
        for estado in estados_a_apagar:
            if estado.nome in estados:
                estado.destruir()
                del estados[estado.nome]
        
        itens_selecionados.clear()
        print(f"Comando Executado: Apagar itens.")
        return True

    def desfazer(self):
        # Restaura os estados primeiro
        estados_a_restaurar = {item for item in self.itens_apagados_diretamente if isinstance(item, Estado)}
        for estado in estados_a_restaurar:
            estados[estado.nome] = estado
            estado.redesenhar() # Usa o novo método para recriar na tela!
        
        # Restaura todas as transições depois
        todas_transicoes_a_restaurar = self.itens_apagados_diretamente.union(self.transicoes_em_cascata)
        for t in todas_transicoes_a_restaurar:
            if isinstance(t, Transicao):
                if t not in transicoes:
                    transicoes.append(t)
                t.atualizar_posicao()
        
        print(f"Comando Desfeito: Restaurar itens apagados.")



# --- Variáveis Globais ---
contador_estados = 0 # Contador para nomes automáticos de estados
estados = {} # Dicionário de estados, chave é o nome do estado
transicoes = [] 
objeto_arrastado = {"id": None, "x_inicial": 0, "y_inicial": 0} # Estado ou "grupo"
modo_atual = "arrastar" # Modos: arrastar, transicao, apagar, selecao
transicao_info = {"origem": None} # Informação temporária para criação de transições
caminho_arquivo_atual = None # Caminho do arquivo atualmente aberto
tipo_automato_atual = "AFNe" # Padrão inicial
itens_selecionados = set() # Conjunto de estados selecionados
caixa_selecao = None # ID do retângulo de seleção
historico_acoes = []      # Pilha de Undo
historico_refazer = []    # Pilha de Redo
comando_em_andamento = None # NOVO v12: Guarda um comando enquanto ele está sendo executado
ponto_inicial_arraste = None # NOVO v12: Guarda o ponto inicial do arraste


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
    global ponto_inicial_arraste, caixa_selecao, comando_em_andamento
    
    # Prioridade 1: Apagar
    if modo_atual == "apagar":
        gerenciar_clique_apagar(event)
        return

    # Prioridade 2: Editar transição
    itens_proximos = canvas.find_closest(event.x, event.y)
    if itens_proximos:
        tags = canvas.gettags(itens_proximos[0])
        if "transicao" in tags or "rotulo" in tags:
            editar_rotulo_transicao(itens_proximos[0])
            return

    # Se não for apagar nem editar, registra o ponto inicial para um possível arraste
    ponto_inicial_arraste = (event.x, event.y)

    if modo_atual == "arrastar":
        estado_clicado = encontrar_estado_clicado(event)
        if estado_clicado and math.dist((event.x, event.y), (estado_clicado.x, estado_clicado.y)) <= estado_clicado.raio:
            objeto_arrastado["id"] = estado_clicado
        else:
            objeto_arrastado["id"] = None
            
    elif modo_atual == "selecao":
        estado_clicado = encontrar_estado_clicado(event)
        if estado_clicado and estado_clicado in itens_selecionados:
            objeto_arrastado["id"] = "grupo"
        else:
            limpar_selecao()
            caixa_selecao = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="blue", dash=(3, 5))
    
    elif modo_atual == "transicao":
        gerenciar_clique_transicao(event)

def arrastar_objeto(event):
    global comando_em_andamento
    if ponto_inicial_arraste is None: return

    # Se um comando de movimento já foi iniciado (pela lógica de Desfazer/Refazer)
    if isinstance(comando_em_andamento, ComandoMover):
        dx_total = event.x - ponto_inicial_arraste[0]
        dy_total = event.y - ponto_inicial_arraste[1]
        
        # Para o 'desfazer' funcionar corretamente, precisamos mover a partir da posição original
        # Desfazemos o último movimento antes de aplicar o novo movimento total
        comando_em_andamento.desfazer() 
        comando_em_andamento.dx, comando_em_andamento.dy = dx_total, dy_total
        comando_em_andamento.executar()
        return

    # Lógica de arraste visual (antes de criar o comando)
    dx = event.x - objeto_arrastado.get("x_prev", event.x)
    dy = event.y - objeto_arrastado.get("y_prev", event.y)

    if modo_atual == "arrastar" and isinstance(objeto_arrastado.get("id"), Estado):
        estado = objeto_arrastado["id"]
        estado.mover(dx, dy)
        atualizar_transicoes_conectadas(estado)
    elif modo_atual == "selecao" and objeto_arrastado.get("id") == "grupo":
        for estado in itens_selecionados:
            estado.mover(dx, dy)
            atualizar_transicoes_conectadas(estado)
    elif modo_atual == "selecao" and caixa_selecao:
        canvas.coords(caixa_selecao, ponto_inicial_arraste[0], ponto_inicial_arraste[1], event.x, event.y)

    objeto_arrastado["x_prev"], objeto_arrastado["y_prev"] = event.x, event.y


def finalizar_arraste(event):
    global caixa_selecao, ponto_inicial_arraste
    
    if ponto_inicial_arraste is None:
        return

    dx = event.x - ponto_inicial_arraste[0]
    dy = event.y - ponto_inicial_arraste[1]
    
    # Se o movimento foi significativo, cria um ComandoMover
    if (abs(dx) > 3 or abs(dy) > 3):
        itens_movidos = set()
        if modo_atual == "arrastar" and isinstance(objeto_arrastado.get("id"), Estado):
            itens_movidos = {objeto_arrastado["id"]}
        elif modo_atual == "selecao" and objeto_arrastado.get("id") == "grupo":
            itens_movidos = itens_selecionados
        
        if itens_movidos:
            comando = ComandoMover(itens_movidos, dx, dy)
            executar_comando(comando)
            status_acao.config(text=f"{len(itens_movidos)} item(ns) movido(s).")
    
    # Se NÃO houve arraste (foi um clique simples) no modo arrastar
    elif modo_atual == "arrastar" and objeto_arrastado.get("id") is None:
         comando = ComandoCriarEstado(event.x, event.y)
         executar_comando(comando)
         status_acao.config(text=f"Estado {comando.estado_criado.nome} criado.")

    # Finaliza o DESENHO da caixa de seleção
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

    # Limpeza final
    objeto_arrastado.clear()
    ponto_inicial_arraste = None

def gerenciar_clique_arrastar(event):
    """
    Gerencia o clique no modo arrastar. Se o clique for em um estado,
    prepara para arrastar. Se for no fundo, usa o sistema de COMANDOS
    para criar um novo estado (permitindo o Undo/Redo).
    """
    estado_clicado = encontrar_estado_clicado(event)
    
    # Se o clique foi dentro de um estado existente, prepara para arrastar
    if estado_clicado:
        dist = math.dist((event.x, event.y), (estado_clicado.x, estado_clicado.y))
        if dist <= estado_clicado.raio:
            objeto_arrastado["id"] = estado_clicado
            objeto_arrastado["x_inicial"], objeto_arrastado["y_inicial"] = event.x, event.y
            return # Ação de arrastar definida, termina a função aqui

    # Se a função chegou até aqui, significa que o clique foi no fundo do canvas.
    # Em vez de chamar a função antiga, usamos o novo sistema de Comandos:
    
    # 1. Cria a "ordem de serviço" para criar um estado
    comando = ComandoCriarEstado(event.x, event.y)
    
    # 2. Executa o comando e o adiciona ao histórico
    executar_comando(comando)
    
    # 3. Atualiza o status para o usuário
    status_acao.config(text=f"Estado {comando.estado_criado.nome} criado.")

def gerenciar_clique_transicao(event):
    global transicao_info
    estado_clicado = encontrar_estado_clicado(event)

    if not estado_clicado:
        cancelar_criacao_transicao(event) # Reutiliza a função de cancelar
        return

    if transicao_info["origem"] is None:
        transicao_info["origem"] = estado_clicado
        canvas.itemconfig(estado_clicado.id_circulo, fill="yellow")
        status_acao.config(text=f"Origem: {estado_clicado.nome}. Clique no destino ou botão do meio para cancelar.")
    else:
        estado_origem = transicao_info["origem"]
        estado_destino = estado_clicado

        # --- MUDANÇA PRINCIPAL AQUI ---
        # Em vez de fazer a lógica aqui, apenas criamos e executamos o comando
        comando = ComandoCriarTransicao(estado_origem, estado_destino)
        executar_comando(comando)
        
        # Limpa e reseta a UI
        canvas.itemconfig(estado_origem.id_circulo, fill="lightblue")
        transicao_info["origem"] = None
        status_acao.config(text="Transição criada! Clique nela para editar.")

def editar_rotulo_transicao(id_item_clicado):
    tags_do_item = canvas.gettags(id_item_clicado) # Obtém todas as tags do item clicado
    tag_alvo = next((tag for tag in tags_do_item if tag.startswith("trans_")), None)
    if not tag_alvo: return
    transicao_alvo = next((t for t in transicoes if t.tag_unica == tag_alvo), None)
    if not transicao_alvo: return

    # Em vez de ter a lógica aqui, criamos e executamos o comando
    comando = ComandoEditarTransicao(transicao_alvo)
    executar_comando(comando)

def gerenciar_clique_apagar(event):
    """
    Gerencia cliques no modo apagar. Usa o sistema de Comandos para
    ações que podem ser desfeitas.
    """
    # Encontra o item clicado, seja estado ou transição
    estado_clicado = encontrar_estado_clicado(event)
    
    # --- LÓGICA PARA APAGAR ESTADO ---
    if estado_clicado:
        # Se o estado faz parte de uma seleção, o comando é para o grupo
        if estado_clicado in itens_selecionados:
            comando = ComandoApagar(itens_selecionados)
        else: # Senão, é só para o estado clicado
            comando = ComandoApagar({estado_clicado})
        
        executar_comando(comando)
        status_acao.config(text="Item(ns) apagado(s).")
        return

    # --- LÓGICA PARA APAGAR TRANSIÇÃO (PREENCHIDA) ---
    itens_proximos = canvas.find_closest(event.x, event.y)
    if not itens_proximos: return
    id_item_clicado = itens_proximos[0]
    tags = canvas.gettags(id_item_clicado)
    
    tag_alvo = next((t for t in tags if t.startswith("trans_")), None) # Encontrou uma transição?
    if tag_alvo:
        transicao_para_apagar = next((t for t in transicoes if t.tag_unica == tag_alvo), None) # Encontrou a transição
        
        if transicao_para_apagar: # Se encontrou, cria e executa o comando
            comando = ComandoApagar({transicao_para_apagar})
            executar_comando(comando)
            status_acao.config(text="Transição apagada.")

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
    estado_clicado = encontrar_estado_clicado(event)
    if not estado_clicado: return

    menu_contexto = tk.Menu(janela, tearoff=0)
    acao_em_grupo = estado_clicado in itens_selecionados and len(itens_selecionados) > 1

    if acao_em_grupo:
        # --- MENU PARA AÇÕES EM GRUPO ---
        if tipo_automato_atual not in ["Mealy", "Moore"]:
            menu_contexto.add_command(label=f"Marcar/Desmarcar Aceitação ({len(itens_selecionados)} itens)", command=lambda: executar_comando(ComandoToggleAceitacao(itens_selecionados)))
        menu_contexto.add_command(label="Renomear Estados...", state="disabled")
        menu_contexto.add_command(label=f"Alterar Cor ({len(itens_selecionados)} itens)...", command=lambda: executar_comando(ComandoAlterarCor(itens_selecionados)))
        menu_contexto.add_separator()
        menu_contexto.add_command(label=f"Apagar {len(itens_selecionados)} Estados Selecionados", command=apagar_selecao)
    else:
        # --- MENU PARA AÇÃO INDIVIDUAL ---
        if tipo_automato_atual not in ["Mealy", "Moore"]:
            menu_contexto.add_command(label="Marcar/Desmarcar como Aceitação", command=lambda: executar_comando(ComandoToggleAceitacao({estado_clicado})))
        if tipo_automato_atual == "Moore":
            menu_contexto.add_command(label="Definir Saída do Estado...", command=lambda: definir_saida_estado(estado_clicado))
        
        menu_contexto.add_command(label="Renomear Estado...", command=lambda: executar_comando(ComandoRenomearEstado(estado_clicado)))
        menu_contexto.add_command(label="Alterar Cor...", command=lambda: executar_comando(ComandoAlterarCor({estado_clicado})))
        menu_contexto.add_separator()
        menu_contexto.add_command(label="Apagar Estado", command=lambda: apagar_estado(estado_clicado))

    menu_contexto.post(event.x_root, event.y_root)

def atualizar_status_modo():
    """Atualiza o texto do painel de status da esquerda com o modo e tipo atuais."""
    # Capitalize() deixa a primeira letra maiúscula (ex: 'arrastar' -> 'Arrastar')
    texto_modo = modo_atual.capitalize().replace("Arrastar", "Criar/Arrastar")
    status_modo.config(text=f"Tipo: {tipo_automato_atual}  |  Modo: {texto_modo}")

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
        ativar_modo_selecao()
    elif event.keysym == "F4":
        ativar_modo_apagar()
    elif event.keysym == "Delete" and itens_selecionados:
        apagar_selecao()

def gerenciar_clique_duplo(event):
    """
    Gerencia o evento de clique duplo, usando o sistema de Comandos.
    """
    if modo_atual == "transicao":
        estado_clicado = encontrar_estado_clicado(event)
        if estado_clicado:
            # --- MUDANÇA AQUI ---
            # Em vez de criar diretamente, usamos o sistema de Comandos
            comando = ComandoCriarTransicao(estado_clicado, estado_clicado)
            executar_comando(comando)
            
            if transicao_info["origem"]:
                canvas.itemconfig(transicao_info["origem"].id_circulo, fill="lightblue")
                transicao_info["origem"] = None
            status_acao.config(text=f"Laço criado para o estado {estado_clicado.nome}.")
            
    else: # Para qualquer outro modo
        # A ação de toggle também já usa o sistema de Comandos, então está correto
        estado_clicado = encontrar_estado_clicado(event)
        if estado_clicado:
            comando = ComandoToggleAceitacao({estado_clicado})
            executar_comando(comando)

def executar_comando(comando, vindo_do_refazer=False):
    if comando.executar():
        historico_acoes.append(comando)
        if not vindo_do_refazer:
            historico_refazer.clear()

def desfazer_acao(event=None):
    if not historico_acoes:
        status_acao.config(text="Nada para desfazer.")
        return
    
    comando = historico_acoes.pop()
    comando.desfazer()
    historico_refazer.append(comando)

    # 🔧 Correção para loops visuais que não desaparecem
    for item_id in canvas.find_all():
        if canvas.type(item_id) == "arc":  # loops são desenhados como 'arc'
            tags = canvas.gettags(item_id)
            # Se a tag não pertence a nenhuma transição ativa, remove
            if not any(t.tag_unica in tags for t in transicoes):
                canvas.delete(item_id)
                
    status_acao.config(text="Ação desfeita.")


def refazer_acao(event=None):
    if not historico_refazer:
        status_acao.config(text="Nada para refazer.")
        return

    comando = historico_refazer.pop()
    # Avisa ao executor que esta ação está vindo do refazer
    executar_comando(comando, vindo_do_refazer=True) 
    status_acao.config(text="Ação refeita.")



# --- Funções de Modo e Tipo ---
def ativar_modo_arrastar():
    global modo_atual
    limpar_selecao() # Limpa a seleção ao entrar neste modo
    modo_atual = "arrastar"
    atualizar_status_modo()
    print("Modo alterado para: arrastar")

def ativar_modo_transicao():
    global modo_atual
    limpar_selecao() # Limpa a seleção ao entrar neste modo
    modo_atual = "transicao"
    atualizar_status_modo()
    print("Modo alterado para: transicao")

def ativar_modo_apagar():
    global modo_atual
    limpar_selecao() # Limpa a seleção ao entrar neste modo
    modo_atual = "apagar"
    atualizar_status_modo()
    print("Modo alterado para: apagar")

def ativar_modo_selecao():
    global modo_atual
    modo_atual = "selecao"
    atualizar_status_modo() # Atualiza o painel de status
    print("Modo alterado para: selecao")
def limpar_selecao():
    """
    Desseleciona todos os itens visualmente e limpa o conjunto de
    itens selecionados na memória.
    """
    if itens_selecionados:
        for item in itens_selecionados:
            item.desselecionar()
        itens_selecionados.clear()
        print("Seleção limpa.")
def apagar_selecao():
    """
    Verifica se há itens selecionados e, após confirmação, apaga todos
    os estados selecionados e suas transições conectadas.
    """
    # Se não há nada selecionado, não faz nada
    if not itens_selecionados:
        return

    # Pede confirmação ao usuário, informando quantos itens serão apagados
    confirmar = messagebox.askyesno(
        "Apagar Seleção",
        f"Tem certeza que deseja apagar os {len(itens_selecionados)} estados selecionados?\n"
        "Todas as transições conectadas a eles também serão apagadas."
    )

    if confirmar:
        estados_para_apagar = set(itens_selecionados)
        transicoes_para_apagar = set()

        # Encontra todas as transições conectadas aos estados selecionados
        for t in transicoes:
            if t.origem in estados_para_apagar or t.destino in estados_para_apagar:
                transicoes_para_apagar.add(t)
        
        # Apaga as transições encontradas
        for t in transicoes_para_apagar:
            t.destruir()
            if t in transicoes:
                transicoes.remove(t)

        # Apaga os estados selecionados
        for estado in estados_para_apagar:
            nome_estado = estado.nome
            estado.destruir()
            if nome_estado in estados:
                del estados[nome_estado]
        
        # Limpa a memória de seleção
        itens_selecionados.clear()
        status_acao.config(text=f"{len(estados_para_apagar)} estados foram apagados.")
def atalho_apagar_selecao(event):
    """Função adaptadora para o atalho da tecla Delete."""
    apagar_selecao()

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
        # ...
        return
    
    # Cria a lista de histórico vazia para a simulação
    historico = []
        
    if tipo_automato_atual == "AFD":
        # ...
        simular_passo_a_passo_AFD(palavra, estado_inicial)

    elif tipo_automato_atual in ["AFNe", "AFN"]:
        estados_atuais = calcular_fecho_epsilon({estado_inicial})
        # A simulação de AFNe não gera relatório de saída, então não passamos o histórico
        simular_passo_a_passo_AFNe(palavra, estados_atuais, "")

    elif tipo_automato_atual == "Mealy":
        # Inicia a simulação passando o histórico vazio
        simular_passo_a_passo_Mealy(palavra, estado_inicial, "", historico)

    elif tipo_automato_atual == "Moore":
        saida_inicial = estado_inicial.simbolo_saida
        sequencia_saida.config(text=f"Saída: {saida_inicial}")
        # Adiciona o passo 0 (inicial) ao histórico de Moore
        passo_zero = {
            "Passo": 0, "Estado Atual": estado_inicial.nome, "Lendo Símbolo": "",
            "Saída Gerada": saida_inicial, "Próximo Estado": estado_inicial.nome
        }
        historico.append(passo_zero)
        # Inicia a simulação passando o histórico com o primeiro passo
        simular_passo_a_passo_Moore(palavra, estado_inicial, saida_inicial, historico)

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

def simular_passo_a_passo_Mealy(palavra_restante, estado_atual, saida_acumulada, historico_passos):
    """
    Motor de simulação para Máquinas de Mealy, com realce de estados e transições.
    """
    # Limpa realces anteriores e realça o estado atual em azul
    for est in estados.values(): canvas.itemconfig(est.id_circulo, outline="black", width=2)
    canvas.itemconfig(estado_atual.id_circulo, outline="blue", width=3)

    # Função de limpeza para o final
    def limpar_realces_finais():
        for est in estados.values():
            canvas.itemconfig(est.id_circulo, outline="black", width=2)

    # Fim da simulação
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
    
    # Registra o passo no histórico
    passo_info = {
        "Passo": len(historico_passos) + 1, "Estado Atual": estado_atual.nome,
        "Lendo Símbolo": simbolo_atual, "Saída Gerada": transicao_encontrada.simbolo_saida,
        "Próximo Estado": estado_destino.nome
    }
    historico_passos.append(passo_info)
    
    # Realça a transição usada
    canvas.itemconfig(transicao_encontrada.tag_unica, fill="red")
    
    # ATUALIZA A UI A CADA PASSO
    status_acao.config(text=f"Lendo '{simbolo_atual}', gerando '{transicao_encontrada.simbolo_saida}'...")
    sequencia_saida.config(text=f"Saída: {nova_saida_acumulada}")
    
    def ir_para_proximo_passo():
        canvas.itemconfig(transicao_encontrada.tag_unica, fill="black")
        simular_passo_a_passo_Mealy(proxima_palavra, estado_destino, nova_saida_acumulada, historico_passos)

    janela.after(800, ir_para_proximo_passo)

def simular_passo_a_passo_Moore(palavra_restante, estado_atual, saida_acumulada, historico_passos):
    # ... (o início e a limpeza continuam iguais)

    if not palavra_restante:
        # ... (configura o resultado final)
        # Chama a nova função de salvar com o histórico completo
        janela.after(500, lambda: salvar_saida_em_arquivo(input_entry.get(), historico_passos))
        janela.after(2000, lambda: [canvas.itemconfig(e.id_circulo, outline="black", width=2) for e in estados.values()])
        return

    simbolo_atual = palavra_restante[0]
    proxima_palavra = palavra_restante[1:]
    
    transicao_encontrada = next((t for t in transicoes if t.origem == estado_atual and simbolo_atual in t.simbolos_entrada), None)
            
    if not transicao_encontrada:
        # ... (lógica de rejeição continua igual)
        return

    estado_destino = transicao_encontrada.destino
    nova_saida_acumulada = saida_acumulada + estado_destino.simbolo_saida

    # --- NOVIDADE AQUI: REGISTRA O PASSO ---
    passo_info = {
        "Passo": len(historico_passos) + 1,
        "Estado Atual": estado_atual.nome,
        "Lendo Símbolo": simbolo_atual,
        "Saída Gerada": estado_destino.simbolo_saida, # Saída de Moore é do estado de destino
        "Próximo Estado": estado_destino.nome
    }
    historico_passos.append(passo_info)
    
    # ... (realce e atualização da UI continuam iguais)
    
    def ir_para_proximo_passo():
        # ...
        # Passa o histórico atualizado para o próximo passo
        simular_passo_a_passo_Moore(proxima_palavra, estado_destino, nova_saida_acumulada, historico_passos)

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

def salvar_saida_em_arquivo(palavra_entrada, historico_passos):
    """
    Pergunta ao usuário se deseja salvar o histórico da simulação e, se sim,
    abre um diálogo para salvar em um arquivo .csv formatado para o Excel.
    """
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
                # --- CORREÇÕES APLICADAS AQUI ---
                # Usamos 'utf-8-sig' para ajudar o Excel a entender os acentos
                # E 'newline=""' que é uma boa prática para arquivos csv
                with open(arquivo, "w", encoding="utf-8-sig", newline="") as f:
                    # Usamos delimiter=';' para separar as colunas corretamente no Excel
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
janela.title("Mini-JFLAP em Python v11")
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
menu_tipo.add_command(label="Máquina de Turing [EM BREVE]", state="disabled")
menu_bar.add_cascade(label="Tipo de Autômato", menu=menu_tipo)
janela.config(menu=menu_bar)



# --- Toolbar ---
toolbar = tk.Frame(janela, bd=1, relief=tk.RAISED)
toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
icones = {}
try:
    # A linha de import original já nos dá o "Image"
    nomes_icones = ["selecionar", "estado", "transicao", "apagar", "salvar", "desfazer", "refazer"] # <-- NOVOS ÍCONES v11 e v12
    for nome in nomes_icones:
        # A correção está aqui, usando Image.Resampling.LANCZOS
        img = Image.open(f"icones/{nome}.png").resize((24, 24), Image.Resampling.LANCZOS)
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
btn_selecionar = criar_botao_toolbar(toolbar, "selecionar", "Selecionar", ativar_modo_selecao) # <-- NOVO BOTÃO v11
btn_apagar = criar_botao_toolbar(toolbar, "apagar", "Apagar", ativar_modo_apagar)
tk.Frame(toolbar, height=30, width=2, bg="grey").pack(side=tk.LEFT, padx=5, pady=2)
btn_desfazer = criar_botao_toolbar(toolbar, "desfazer", "Desfazer", desfazer_acao) # <-- NOVO BOTÃO v12
btn_refazer = criar_botao_toolbar(toolbar, "refazer", "Refazer", refazer_acao) # <-- NOVO BOTÃO v12
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
janela.bind("<Control-z>", desfazer_acao) # Atalho Ctrl+Z para desfazer
janela.bind("<Control-y>", refazer_acao) # Atalho Ctrl+Y para refazer


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
