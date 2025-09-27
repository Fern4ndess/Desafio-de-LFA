#---NESSA VERSÃO ESTOU ADICIONANDO BOTÕES"---

import tkinter as tk
from tkinter import messagebox 
from tkinter import simpledialog 
from tkinter import filedialog 
from PIL import Image, ImageTk # <-- NOVA LINHA v5
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

    # Dentro da classe Estado

    def set_aceitacao(self, eh_aceitacao):
        """
        Define diretamente o estado de aceitação, desenhando ou apagando
        o círculo extra conforme necessário.
        """
        # Se o novo estado for igual ao atual, não faz nada
        if self.aceitacao == eh_aceitacao:
            return

        self.aceitacao = eh_aceitacao
        
        # Apaga qualquer círculo de aceitação antigo associado a este estado
        # para evitar duplicatas.
        for item in self.canvas.find_withtag("aceitacao"):
            if self.nome in self.canvas.gettags(item):
                self.canvas.delete(item)

        # Se for um estado de aceitação, desenha o novo círculo
        if self.aceitacao:
            self.canvas.create_oval(
                self.x - self.raio + 5, self.y - self.raio + 5,
                self.x + self.raio - 5, self.y + self.raio - 5,
                outline="black", width=2, tags=("aceitacao", self.nome)
            )

    def toggle_aceitacao(self):
        """
        Inverte o estado de aceitação atual. Usado pelo clique do botão direito.
        """
        # Agora, a função toggle simplesmente chama a função set.
        self.set_aceitacao(not self.aceitacao)

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
    def __init__(self, origem, destino, canvas, simbolo_entrada="ε", simbolo_saida="", offset_x=0, offset_y=0):
        self.origem = origem
        self.destino = destino
        self.canvas = canvas
        self.simbolo_entrada = simbolo_entrada # Renomeado de 'simbolo' para 'simbolo_entrada'
        self.simbolo_saida = simbolo_saida     # NOVO: Símbolo de saída
        self.tag_unica = f"trans_{id(self)}"
        self.offset_x = offset_x #v7
        self.offset_y = offset_y #v7
        self.is_loop = (self.origem == self.destino)
        self.atualizar_posicao()

    def atualizar_posicao(self):
        self.canvas.delete(self.tag_unica)
        if self.is_loop:
            self._desenhar_loop()
        else:
            self._desenhar_linha_reta()
        # No final de atualizar_posicao, dentro da classe Transicao
        self.canvas.tag_raise("estado")
        self.canvas.tag_raise("texto")
        self.canvas.tag_raise("aceitacao") # <-- A LINHA DA SOLUÇÃO

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
        rotulo_completo = f"{self.simbolo_entrada}/{self.simbolo_saida}" # NOVO: simbolo de saida
        self.canvas.create_text(coords_texto, text=rotulo_completo, font=("Arial", 10, "italic"), tags=(self.tag_unica, "rotulo"))

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
        rotulo_completo = f"{self.simbolo_entrada}/{self.simbolo_saida}" # NOVO: simnbolo de saida
        self.canvas.create_text(coords_texto, text=rotulo_completo, font=("Arial", 10, "italic"), tags=(self.tag_unica, "rotulo"))
        
    def atualizar_simbolo(self, novo_simbolo_entrada, novo_simbolo_saida):
        self.simbolo_entrada = novo_simbolo_entrada
        self.simbolo_saida = novo_simbolo_saida # NOVO: simbolo de saida
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
caminho_arquivo_atual = None # NOVO: Guarda o caminho do arquivo aberto


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
        nova_transicao = Transicao(estado_origem, estado_destino, canvas, simbolo_entrada="ε", simbolo_saida="")
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
    Encontra a transição clicada e abre uma caixa de diálogo para editar 
    o Símbolo de ENTRADA e o Símbolo de SAÍDA (Mealy).
    """
    tags_do_item = canvas.gettags(id_item_clicado)
    tag_alvo = None
    for tag in tags_do_item:
        if tag.startswith("trans_"):
            tag_alvo = tag
            break
            
    if tag_alvo:
        transicao_alvo = None
        for t in transicoes:
            if t.tag_unica == tag_alvo:
                transicao_alvo = t
                break
        
        if transicao_alvo:
            # Apresenta o formato ENTRADA/SAÍDA
            valor_inicial = f"{transicao_alvo.simbolo_entrada}/{transicao_alvo.simbolo_saida}"
            
            novo_rotulo_completo = simpledialog.askstring(
                "Editar Transição (Mealy)",
                "Formato: Símbolo de ENTRADA / Símbolo de SAÍDA (Ex: a/1)",
                initialvalue=valor_inicial
            )
            
            if novo_rotulo_completo is not None:
                # 1. Separa a entrada e saída pela barra (/)
                partes = novo_rotulo_completo.split('/', 1)
                
                # Garante que temos pelo menos a entrada
                simbolo_entrada_novo = partes[0].strip()
                simbolo_saida_novo = partes[1].strip() if len(partes) > 1 else ""
                
                # 2. Lógica para transição vazia (ε)
                # Se o usuário apagar TUDO da entrada, assume ε
                if not simbolo_entrada_novo:
                    simbolo_entrada_final = "ε"
                else:
                    simbolo_entrada_final = simbolo_entrada_novo
                    
                # 3. Se a saída for apagada, ela fica vazia ("")
                simbolo_saida_final = simbolo_saida_novo
                
                # 4. Atualiza a transição
                transicao_alvo.atualizar_simbolo(simbolo_entrada_final, simbolo_saida_final)


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

#---------------------------------------------- Adicionando v5 -------------------------------------- 

# --- NOVO: Ativadores de modo específicos ---
def ativar_modo_arrastar():
    global modo_atual
    modo_atual = "arrastar"
    botao_modo.config(text="Modo Atual: Criar/Arrastar Estado")
    instrucoes.config(text="Clique para criar ou arrastar estados.")
    print("Modo alterado para: arrastar")

def ativar_modo_transicao():
    global modo_atual
    modo_atual = "transicao"
    botao_modo.config(text="Modo Atual: Criar Transição")
    instrucoes.config(text="Clique em um estado de origem e depois no destino.")
    print("Modo alterado para: transicao")

def ativar_modo_apagar():
    global modo_atual
    modo_atual = "apagar"
    botao_modo.config(text="Modo Atual: APAGAR")
    instrucoes.config(text="CUIDADO: Clique em um estado ou transição para apagar.")
    print("Modo alterado para: apagar")






#------------------------------------------- FIM v5 --------------------------------------------

def criar_novo_estado(x, y):
    global contador_estados
    nome_estado = f"q{contador_estados}"
    estado = Estado(nome_estado, x, y, canvas)
    estados[nome_estado] = estado

    # Se for o primeiro estado, define como inicial
    if contador_estados == 0:
        estado.set_inicial()
    else:
        # Garante que não crie múltiplas setas de inicial sem querer
        if not any(est.inicial for est in estados.values()):
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


# --- NOVAS FUNÇÕES DE SIMULAÇÃO AFNE ---

def calcular_fecho_epsilon(estados_origem):
    """
    Calcula o Fecho-Epsilon (E-closure) de um conjunto de estados.
    Encontra todos os estados alcançáveis seguindo apenas transições com símbolo 'ε'.

    Args:
        estados_origem (set): Um conjunto de objetos Estado (não nomes).
    
    Returns:
        set: Um conjunto de objetos Estado que formam o E-closure.
    """
    fecho = set(estados_origem)
    pilha = list(estados_origem)

    while pilha:
        estado_atual = pilha.pop()
        
        # Procura transições ε a partir do estado atual
        for t in transicoes:
            if t.origem == estado_atual and t.simbolo_entrada == "ε":
                estado_destino = t.destino
                
                # Se o estado de destino ainda não está no fecho, adiciona-o
                if estado_destino not in fecho:
                    fecho.add(estado_destino)
                    pilha.append(estado_destino)
                    
    return fecho

def simular_palavra():
    """
    Função inicial para simulação AFNe.
    Define o estado inicial e seu fecho-epsilon, e inicia o processo.
    """
    palavra = input_entry.get()
    resultado.config(text="") 

    estado_inicial = None
    for est in estados.values():
        if est.inicial:
            estado_inicial = est
            break
    
    if not estado_inicial:
        resultado.config(text="Erro: Nenhum estado inicial definido!", fg="orange")
        return
    
    # O conjunto de estados iniciais é o fecho-epsilon do estado inicial
    estados_atuais = calcular_fecho_epsilon({estado_inicial})
    
    # Inicia a simulação
    simular_passo_a_passo(palavra, estados_atuais)

def simular_passo_a_passo(palavra_restante, estados_atuais):
    """
    Executa um passo da simulação AFNe: lê um símbolo e calcula o próximo conjunto de estados.
    """
    
    # Remove quaisquer realces anteriores antes de começar o novo passo
    for estado in estados.values():
        canvas.itemconfig(estado.id_circulo, outline="black", width=2)
    
    # ------------------- FIM DA PALAVRA -------------------
    if not palavra_restante:
        # Palavra aceita se QUALQUER um dos estados atuais for de aceitação
        aceita = any(estado.aceitacao for estado in estados_atuais)
        
        if aceita:
            resultado.config(text="Palavra aceita ✅", fg="green")
        else:
            resultado.config(text="Palavra rejeitada ❌", fg="red")
        return

    simbolo_atual = palavra_restante[0]
    proxima_palavra = palavra_restante[1:]
    
    # ------------------- CALCULAR PRÓXIMOS ESTADOS -------------------
    proximos_estados_brutos = set()

    for estado_origem in estados_atuais:
        # 1. Realça os estados de onde a transição vai partir
        canvas.itemconfig(estado_origem.id_circulo, outline="red", width=3)
        
        for t in transicoes:
            # 2. Procura transições que saem dos estados atuais E consomem o símbolo
            if t.origem == estado_origem and t.simbolo_entrada == simbolo_atual:
                proximos_estados_brutos.add(t.destino)

    # ------------------- VERIFICAÇÃO E RECURSÃO -------------------
    if not proximos_estados_brutos:
        # Se não há transições possíveis para o símbolo, a palavra é rejeitada
        resultado.config(text=f"Palavra rejeitada ❌ (preso no símbolo '{simbolo_atual}')", fg="red")
        
        # O estado final (rejeitado) deve manter o realce por um momento
        def limpar_realce():
            for estado in estados.values():
                canvas.itemconfig(estado.id_circulo, outline="black", width=2)
        janela.after(1000, limpar_realce) # Mantém realce por 1 segundo
        
        return
    
    # 3. Calcula o fecho-epsilon do conjunto de destino para obter os estados finais do passo
    proximos_estados_finais = calcular_fecho_epsilon(proximos_estados_brutos)
    
    # 4. Mostra o símbolo atual sendo lido
    nomes_atuais = ", ".join([e.nome for e in estados_atuais])
    instrucoes.config(text=f"Lendo símbolo: '{simbolo_atual}'. Estados Atuais: [{nomes_atuais}]")
    
    # 5. Agenda o próximo passo (com um pequeno atraso para visualização)
    def ir_para_proximo_passo():
        # Chama a si mesma com o resto da palavra e os novos estados
        simular_passo_a_passo(proxima_palavra, proximos_estados_finais)

    # 500ms de atraso para o usuário ver de onde está partindo a transição e qual símbolo está a ser lido
    janela.after(500, ir_para_proximo_passo)

def novo_automato():
    global estados, transicoes, contador_estados, caminho_arquivo_atual # Adicione aqui
    canvas.delete("all")
    estados = {}
    transicoes = []
    contador_estados = 0
    caminho_arquivo_atual = None # Limpa a memória
    resultado.config(text="")
    instrucoes.config(text="Novo autômato criado.")


def salvar():
    """Função de salvamento rápido. Salva no caminho atual ou chama 'Salvar como...' se for novo."""
    if caminho_arquivo_atual:
        _salvar_dados_no_arquivo(caminho_arquivo_atual)
    else:
        # Se não há caminho, comporta-se como "Salvar como..."
        salvar_automato()


def salvar_automato(): # Esta agora é a nossa função "Salvar como..."
    global caminho_arquivo_atual
    arquivo = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if arquivo:
        caminho_arquivo_atual = arquivo
        _salvar_dados_no_arquivo(caminho_arquivo_atual)


def _salvar_dados_no_arquivo(caminho):
    """Função auxiliar que pega os dados do autômato e os salva no caminho especificado."""
    dados = {
        "estados": [
            {"nome": est.nome, "x": est.x, "y": est.y, "inicial": est.inicial, "aceitacao": est.aceitacao}
            for est in estados.values()
        ],
        "transicoes": [
            {"origem": t.origem.nome, "destino": t.destino.nome,
             "simbolo_entrada": t.simbolo_entrada, "simbolo_saida": t.simbolo_saida,
             "offset_x": t.offset_x, "offset_y": t.offset_y}
            for t in transicoes
        ]
    }
    try:
        import json
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4)
        instrucoes.config(text=f"Autômato salvo em {caminho.split('/')[-1]}")
    except Exception as e:
        messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo:\n{e}")


def abrir_automato():
    global estados, transicoes, contador_estados
    arquivo = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if not arquivo:
        return
    
    caminho_arquivo_atual = arquivo # Guarda o caminho do arquivo abert
    import json
    with open(arquivo, "r", encoding="utf-8") as f:
        dados = json.load(f)

    # Resetar
    canvas.delete("all")
    estados = {}
    transicoes = []
    contador_estados = 0

    # Recriar estados
    for e in dados["estados"]:
        estado = Estado(e["nome"], e["x"], e["y"], canvas)
        estados[e["nome"]] = estado
        if e["inicial"]:
            estado.set_inicial()
        if e["aceitacao"]:
            estado.set_aceitacao(True)
        contador_estados += 1

    # Recriar transições
    # Recriar transições
    for t in dados["transicoes"]:
        origem = estados[t["origem"]]
        destino = estados[t["destino"]]
        simbolo_entrada = t.get("simbolo_entrada", t.get("simbolo", "ε"))
        simbolo_saida = t.get("simbolo_saida", "")
        # --- LINHAS NOVAS ---
        # Lê os valores de offset do arquivo, com 0 como padrão se não existirem
        offset_x = t.get("offset_x", 0)
        offset_y = t.get("offset_y", 0)
        
        # Passa os valores de offset para a nova transição
        transicoes.append(Transicao(origem, destino, canvas, simbolo_entrada, simbolo_saida, offset_x, offset_y))

    instrucoes.config(text=f"Autômato carregado de {arquivo}")


#----------------------------------fim v4--------------------------------------------


# --- Janela ---
janela = tk.Tk()
janela.title("Mini-JFLAP em Python")
janela.geometry("800x700")

#------------------------------- MENU ------------------------------------
menu_bar = tk.Menu(janela)

# Menu Arquivo
menu_arquivo = tk.Menu(menu_bar, tearoff=0)
menu_arquivo.add_command(label="Novo", command=novo_automato)
menu_arquivo.add_command(label="Abrir", command=abrir_automato)
menu_arquivo.add_command(label="Salvar", command=salvar) # <-- NOVA LINHA v7
menu_arquivo.add_command(label="Salvar como...", command=salvar_automato)
menu_arquivo.add_separator()
menu_arquivo.add_command(label="Sair", command=janela.quit)

menu_bar.add_cascade(label="Arquivo", menu=menu_arquivo)

# Ativar menu
janela.config(menu=menu_bar)

#------------------------------------- MENU --------------------------------------------

#----------------------------------- BOTOES --------------------------------------------

# Criar uma barra de ferramentas
toolbar = tk.Frame(janela, bd=1, relief=tk.RAISED)
toolbar.pack(side=tk.TOP, fill=tk.X)

# Tenta carregar ícones; se falhar, usa texto nos botões
try:
    icone_estado = Image.open("estado.png").resize((35, 35))
    icone_estado = ImageTk.PhotoImage(icone_estado)
    icone_transicao = Image.open("transicao.png").resize((35, 35))
    icone_transicao = ImageTk.PhotoImage(icone_transicao)
    icone_apagar = Image.open("apagar.png").resize((35, 35))
    icone_apagar = ImageTk.PhotoImage(icone_apagar)
    usar_icone = True
except Exception as e:
    print("Aviso: não foi possível carregar ícones (estado.png / transicao.png). Usando botões texto.\nErro:", e)
    usar_icone = False

# Botão para criar estados
if usar_icone:
    btn_estado = tk.Button(toolbar, image=icone_estado, relief=tk.FLAT, command=ativar_modo_arrastar)
    btn_estado.image = icone_estado
else:
    btn_estado = tk.Button(toolbar, text="Estado", relief=tk.FLAT, command=ativar_modo_arrastar)
btn_estado.pack(side=tk.LEFT, padx=2, pady=2)

# Botão para criar transições
if usar_icone:
    btn_transicao = tk.Button(toolbar, image=icone_transicao, relief=tk.FLAT, command=ativar_modo_transicao)
    btn_transicao.image = icone_transicao
else:
    btn_transicao = tk.Button(toolbar, text="Transição", relief=tk.FLAT, command=ativar_modo_transicao)
btn_transicao.pack(side=tk.LEFT, padx=2, pady=2)

# Botao para apagar estados
if usar_icone:
    btn_apagar = tk.Button(toolbar, image=icone_apagar, relief=tk.FLAT, command=ativar_modo_apagar)
    btn_apagar.image = icone_apagar
else:
    btn_apagar = tk.Button(toolbar, text="Apagar", relief=tk.FLAT, command=ativar_modo_apagar)
btn_apagar.pack(side=tk.LEFT, padx=2, pady=2)

# Tenta carregar o ícone de Salvar v7
try:
    # Use "salvar.png" ou "salvar_caneta.png", o que você preferir
    icone_salvar = Image.open("salvar.png").resize((35, 35))
    icone_salvar = ImageTk.PhotoImage(icone_salvar)
except Exception as e:
    print("Aviso: não foi possível carregar o ícone (salvar.png).", e)
    icone_salvar = None # Define como None se falhar

# Botão para Salvar
# Adicione um separador visual na barra de ferramentas
separator = tk.Frame(toolbar, height=35, width=2, bg="grey")
separator.pack(side=tk.LEFT, padx=5, pady=2)

if icone_salvar:
    btn_salvar = tk.Button(toolbar, image=icone_salvar, relief=tk.FLAT, command=salvar)
    btn_salvar.image = icone_salvar
else:
    btn_salvar = tk.Button(toolbar, text="Salvar", relief=tk.FLAT, command=salvar)
btn_salvar.pack(side=tk.LEFT, padx=2, pady=2)



#----------------------------------------fim BOTOES v4 ----------------------------------------

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

# NOVO: Label para a Sequência de Saída 
sequencia_saida = tk.Label(janela, text="Saída: ", font=("Arial", 12))
sequencia_saida.pack(pady=5)

janela.mainloop() 