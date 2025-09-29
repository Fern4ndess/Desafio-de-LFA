import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from tkinter import colorchooser # <-- NOVA LINHA
from PIL import Image, ImageTk
import json
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

    # Dentro da class Estado:

    def set_aceitacao(self, eh_aceitacao):
        """
        Define DIRETAMENTE o estado de aceitação, desenhando ou apagando
        o círculo extra de forma segura.
        """
        # Se o estado já está como queremos, não faz nada
        if self.aceitacao == eh_aceitacao:
            return

        self.aceitacao = eh_aceitacao
        
        # Primeiro, apaga QUALQUER anel de aceitação antigo deste estado para evitar duplicatas
        for item in self.canvas.find_withtag("aceitacao"):
            if self.nome in self.canvas.gettags(item):
                self.canvas.delete(item)

        # Se o novo estado é de aceitação, desenha o anel
        if self.aceitacao:
            self.canvas.create_oval(
                self.x - self.raio + 5, self.y - self.raio + 5,
                self.x + self.raio - 5, self.y + self.raio - 5,
                outline="black", width=2, tags=("aceitacao", self.nome)
            )

    def toggle_aceitacao(self):
        """
        Inverte o estado de aceitação atual. Usado pelo menu de contexto.
        """
        # A função de 'inverter' agora simplesmente chama a função de 'definir'
        self.set_aceitacao(not self.aceitacao)

    def destruir(self):
        self.canvas.delete(self.nome)

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
        texto_entrada = ",".join(self.simbolos_entrada)
        if self.simbolo_saida:
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
        raio_estado = self.origem.raio
        raio_loop = 20
        bounding_box = (x - raio_loop, y - (2 * raio_estado), x + raio_loop, y)
        self.canvas.create_arc(bounding_box, start=210, extent=-240, style=tk.ARC, outline="black", width=2, tags=(self.tag_unica, "transicao"))
        angulo_final_rad = math.radians(-30)
        centro_arco_x, centro_arco_y = x, y - raio_estado
        ponta_x = centro_arco_x + raio_loop * math.cos(angulo_final_rad)
        ponta_y = centro_arco_y - raio_loop * math.sin(angulo_final_rad)
        ponta1, ponta2, ponta3 = (ponta_x, ponta_y), (ponta_x - 10, ponta_y - 2), (ponta_x - 2, ponta_y + 8)
        self.canvas.create_polygon(ponta1, ponta2, ponta3, fill="black", tags=(self.tag_unica, "transicao"))
        coords_texto = (x, y - raio_estado - raio_loop - 8)
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
        # Verifica se o clique foi dentro do raio do círculo
        dist = math.dist((event.x, event.y), (estado_clicado.x, estado_clicado.y))
        if dist <= estado_clicado.raio:
            objeto_arrastado["id"] = estado_clicado
            objeto_arrastado["x_inicial"] = event.x
            objeto_arrastado["y_inicial"] = event.y
            return # Sai da função para não criar um novo estado

    # Se não clicou em um estado existente, cria um novo
    criar_novo_estado(event.x, event.y)

def gerenciar_clique_transicao(event):
    """
    Gerencia os cliques no modo de transição, com a lógica completa para
    o primeiro e o segundo clique.
    """
    global transicao_info
    estado_clicado = encontrar_estado_clicado(event)

    # Se clicou fora de qualquer estado...
    if not estado_clicado:
        # ...cancela a criação da transição se uma origem já foi selecionada.
        if transicao_info["origem"]:
            canvas.itemconfig(transicao_info["origem"].id_circulo, fill="lightblue")
        transicao_info["origem"] = None
        instrucoes.config(text="Ação cancelada. Clique no estado de origem.")
        return

    # Se este é o PRIMEIRO clique da criação da transição
    if transicao_info["origem"] is None:
        transicao_info["origem"] = estado_clicado
        canvas.itemconfig(estado_clicado.id_circulo, fill="yellow") # Realça a origem
        instrucoes.config(text=f"Origem: {estado_clicado.nome}. Agora clique no destino.")
    
    # Se este é o SEGUNDO clique (já temos uma origem)
    else:
        estado_origem = transicao_info["origem"]
        estado_destino = estado_clicado

        # Lógica para encontrar transição gêmea (para o desvio)
        transicao_gemea = next((t for t in transicoes if t.origem == estado_destino and t.destino == estado_origem), None)
        
        # Cria a nova transição
        nova_transicao = Transicao(estado_origem, estado_destino, canvas)
        transicoes.append(nova_transicao)

        # Se encontrou uma gêmea, aplica o desvio em ambas
        if transicao_gemea:
            dist = math.dist((estado_origem.x, estado_origem.y), (estado_destino.x, estado_destino.y))
            if dist == 0: dist = 1
            vetor_x = (estado_destino.x - estado_origem.x) / dist
            vetor_y = (estado_destino.y - estado_origem.y) / dist
            vetor_perp_x, vetor_perp_y = -vetor_y, vetor_x
            offset_dist = 10
            
            nova_transicao.offset_x, nova_transicao.offset_y = vetor_perp_x * offset_dist, vetor_perp_y * offset_dist
            nova_transicao.atualizar_posicao()

            transicao_gemea.offset_x, transicao_gemea.offset_y = -vetor_perp_x * offset_dist, -vetor_perp_y * offset_dist
            transicao_gemea.atualizar_posicao()

        # Limpa a seleção e reseta para a próxima criação
        canvas.itemconfig(estado_origem.id_circulo, fill="lightblue")
        transicao_info["origem"] = None
        instrucoes.config(text="Transição criada! Clique nela para editar o símbolo.")

def editar_rotulo_transicao(id_item_clicado):
    tags_do_item = canvas.gettags(id_item_clicado)
    tag_alvo = next((tag for tag in tags_do_item if tag.startswith("trans_")), None)
    if tag_alvo:
        transicao_alvo = next((t for t in transicoes if t.tag_unica == tag_alvo), None)
        if transicao_alvo:
            valor_inicial = transicao_alvo._get_rotulo_texto()
            novo_rotulo_completo = simpledialog.askstring("Editar Transição", "Formato: simbolo1,simbolo2 / saida", initialvalue=valor_inicial)
            if novo_rotulo_completo is not None:
                transicao_alvo.atualizar_simbolo(novo_rotulo_completo)

def gerenciar_clique_apagar(event):
    itens_proximos = canvas.find_closest(event.x, event.y)
    if not itens_proximos: return
    id_item_clicado = itens_proximos[0]
    tags_do_item = canvas.gettags(id_item_clicado)
    nome_estado = next((t for t in tags_do_item if t.startswith('q')), None)
    if nome_estado:
        estado_para_apagar = estados.get(nome_estado)
        if not estado_para_apagar: return
        confirmar = messagebox.askyesno("Apagar Estado", f"Tem certeza que deseja apagar o estado '{nome_estado}'?\nTodas as transições conectadas a ele também serão apagadas.")
        if confirmar:
            transicoes_a_remover = [t for t in transicoes if t.origem == estado_para_apagar or t.destino == estado_para_apagar]
            for t in transicoes_a_remover:
                t.destruir()
                transicoes.remove(t)
            estado_para_apagar.destruir()
            del estados[nome_estado]
            instrucoes.config(text=f"Estado {nome_estado} apagado.")
        else:
            instrucoes.config(text="Ação de apagar cancelada.")
        return
    tag_alvo = next((tag for tag in tags_do_item if tag.startswith("trans_")), None)
    if tag_alvo:
        transicao_para_apagar = next((t for t in transicoes if t.tag_unica == tag_alvo), None)
        if transicao_para_apagar:
            transicao_para_apagar.destruir()
            transicoes.remove(transicao_para_apagar)
            instrucoes.config(text="Transição apagada com sucesso.")

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
    itens = canvas.find_closest(event.x, event.y)
    if not itens: return
    tag_estado = next((t for t in canvas.gettags(itens[0]) if t.startswith("q")), None)
    if tag_estado:
        estados[tag_estado].toggle_aceitacao()

def atualizar_transicoes_conectadas(estado_movido):
    for transicao in transicoes:
        if transicao.origem == estado_movido or transicao.destino == estado_movido:
            transicao.atualizar_posicao()

# --- Funções de Modo ---
def ativar_modo_arrastar():
    global modo_atual
    modo_atual = "arrastar"
    instrucoes.config(text="Modo Criar/Arrastar: Clique no canvas para criar ou arraste um estado.")

def ativar_modo_transicao():
    global modo_atual
    modo_atual = "transicao"
    instrucoes.config(text="Modo Transição: Clique no estado de origem e depois no de destino.")

def ativar_modo_apagar():
    global modo_atual
    modo_atual = "apagar"
    instrucoes.config(text="Modo Apagar: CUIDADO! Clique em um item para apagar.")

# --- Funções de Simulação (AFNe) ---
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

def simular_palavra():
    palavra = input_entry.get()
    resultado.config(text="Simulando...")
    sequencia_saida.config(text="Saída: ")
    estado_inicial = next((est for est in estados.values() if est.inicial), None)
    if not estado_inicial:
        resultado.config(text="Erro: Nenhum estado inicial definido!", fg="orange")
        return
    estados_atuais = calcular_fecho_epsilon({estado_inicial})
    simular_passo_a_passo(palavra, estados_atuais, "")

def simular_passo_a_passo(palavra_restante, estados_atuais, saida_acumulada):
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
                transicoes_usadas.append(t)

    if not proximos_estados_brutos:
        resultado.config(text=f"Rejeitada ❌ (preso no símbolo '{simbolo_atual}')", fg="red")
        janela.after(1000, lambda: [canvas.itemconfig(e.id_circulo, outline="black", width=2) for e in estados.values()])
        return

    proximos_estados_finais = calcular_fecho_epsilon(proximos_estados_brutos)
    nova_saida_acumulada = saida_acumulada + saida_passo
    
    for t in transicoes_usadas: canvas.itemconfig(t.tag_unica, fill="red")
    nomes_atuais = ", ".join(sorted([e.nome for e in proximos_estados_finais]))
    instrucoes.config(text=f"Lendo '{simbolo_atual}'... Próximos estados: [{nomes_atuais}]")
    sequencia_saida.config(text=f"Saída: {nova_saida_acumulada}")
    
    def ir_para_proximo_passo():
        for t in transicoes_usadas: canvas.itemconfig(t.tag_unica, fill="black")
        simular_passo_a_passo(proxima_palavra, proximos_estados_finais, nova_saida_acumulada)
    janela.after(700, ir_para_proximo_passo)

# --- Funções de Arquivo ---
def novo_automato():
    global estados, transicoes, contador_estados, caminho_arquivo_atual
    canvas.delete("all")
    estados, transicoes = {}, []
    contador_estados = 0
    caminho_arquivo_atual = None
    resultado.config(text="")
    instrucoes.config(text="Novo autômato criado. Clique no canvas para começar.")

def _salvar_dados_no_arquivo(caminho):
    dados = {
        "estados": [{"nome": e.nome, "x": e.x, "y": e.y, "inicial": e.inicial, "aceitacao": e.aceitacao} for e in estados.values()],
        "transicoes": [{"origem": t.origem.nome, "destino": t.destino.nome, "simbolos_entrada": t.simbolos_entrada,
                        "simbolo_saida": t.simbolo_saida, "offset_x": t.offset_x, "offset_y": t.offset_y} for t in transicoes]
    }
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)
    instrucoes.config(text=f"Autômato salvo em {caminho.split('/')[-1]}")

def salvar():
    if caminho_arquivo_atual:
        _salvar_dados_no_arquivo(caminho_arquivo_atual)
    else:
        salvar_como()

def salvar_como():
    global caminho_arquivo_atual
    arquivo = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if arquivo:
        caminho_arquivo_atual = arquivo
        _salvar_dados_no_arquivo(caminho_arquivo_atual)

def abrir_automato():
    global estados, transicoes, contador_estados, caminho_arquivo_atual
    arquivo = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if not arquivo: return

    with open(arquivo, "r", encoding="utf-8") as f:
        dados = json.load(f)

    novo_automato()
    caminho_arquivo_atual = arquivo
    
    for e_data in dados["estados"]:
        estado = Estado(e_data["nome"], e_data["x"], e_data["y"], canvas)
        estados[e_data["nome"]] = estado
        if e_data.get("inicial"): estado.set_inicial()
        if e_data.get("aceitacao"): estado.set_aceitacao(True)
    
    if estados:
        maior_num_estado = max([int(nome.replace('q', '')) for nome in estados.keys()]) + 1
        contador_estados = maior_num_estado if maior_num_estado > contador_estados else contador_estados

    for t_data in dados["transicoes"]:
        origem, destino = estados.get(t_data["origem"]), estados.get(t_data["destino"])
        if not origem or not destino: continue
        transicoes.append(Transicao(origem, destino, canvas, t_data.get("simbolos_entrada", ["ε"]), 
                                t_data.get("simbolo_saida", ""), t_data.get("offset_x", 0), t_data.get("offset_y", 0)))
    
    corrigir_desvios_carregados()
    instrucoes.config(text=f"Autômato carregado de {arquivo.split('/')[-1]}")

def corrigir_desvios_carregados():
    pares_verificados = set()
    for t1 in transicoes:
        for t2 in transicoes:
            if t1 == t2 or tuple(sorted((id(t1), id(t2)))) in pares_verificados: continue
            if t1.origem == t2.destino and t1.destino == t2.origem:
                if t1.offset_x == 0 and t2.offset_x == 0:
                    estado_origem, estado_destino = t1.origem, t1.destino
                    dist = math.dist((estado_origem.x, estado_origem.y), (estado_destino.x, estado_destino.y))
                    if dist == 0: dist = 1
                    vetor_x, vetor_y = (estado_destino.x - estado_origem.x) / dist, (estado_destino.y - estado_origem.y) / dist
                    vetor_perp_x, vetor_perp_y = -vetor_y, vetor_x
                    offset_dist = 10
                    t1.offset_x, t1.offset_y = vetor_perp_x * offset_dist, vetor_perp_y * offset_dist
                    t1.atualizar_posicao()
                    t2.offset_x, t2.offset_y = -vetor_perp_x * offset_dist, -vetor_perp_y * offset_dist
                    t2.atualizar_posicao()
                pares_verificados.add(tuple(sorted((id(t1), id(t2)))))


def renomear_estado(estado):
    """Abre uma caixa de diálogo para renomear um estado de forma segura."""
    novo_nome = simpledialog.askstring(
        "Renomear Estado",
        f"Digite o novo nome para '{estado.nome}':",
        initialvalue=estado.nome
    )
    
    # Validação para garantir que o nome não seja vazio ou já exista
    if novo_nome and novo_nome not in estados:
        nome_antigo = estado.nome
        
        # --- LÓGICA DE ATUALIZAÇÃO SEGURA DAS TAGS ---
        # 1. Encontra todos os IDs dos componentes visuais associados ao nome antigo
        ids_componentes = canvas.find_withtag(nome_antigo)
        
        # 2. Para cada componente, atualiza sua tag de nome individualmente
        for item_id in ids_componentes:
            tags_atuais = list(canvas.gettags(item_id))
            
            # Cria uma nova lista de tags, substituindo apenas a de nome
            novas_tags = [novo_nome if t == nome_antigo else t for t in tags_atuais]
            
            # Aplica a nova lista de tags ao item
            canvas.itemconfig(item_id, tags=tuple(novas_tags))
            
        # --- O RESTO DA LÓGICA (QUE JÁ ESTAVA CORRETA) ---
        # 3. Atualiza o texto visível no canvas
        canvas.itemconfig(estado.id_texto, text=novo_nome)
        
        # 4. Atualiza o nome no objeto Estado
        estado.nome = novo_nome
        
        # 5. Atualiza a chave no dicionário principal de estados
        estados[novo_nome] = estados.pop(nome_antigo)
        
        print(f"Estado '{nome_antigo}' renomeado para '{novo_nome}'.")

    elif novo_nome:
        messagebox.showwarning("Erro", "O nome inserido já existe ou é inválido.")

def mudar_cor_estado(estado):
    """Abre uma caixa de diálogo para escolher uma nova cor para o estado."""
    # askcolor() retorna uma tupla (rgb, hex_code) ou (None, None) se cancelado
    nova_cor = colorchooser.askcolor(title=f"Escolha a cor para {estado.nome}")
    
    if nova_cor and nova_cor[1]: # nova_cor[1] é o código hexadecimal da cor (ex: "#ff0000")
        canvas.itemconfig(estado.id_circulo, fill=nova_cor[1])
        print(f"Cor do estado '{estado.nome}' alterada para {nova_cor[1]}.")

def mostrar_menu_contexto(event):
    """Exibe o menu de contexto se o clique direito foi em um estado."""
    estado_clicado = encontrar_estado_clicado(event)
    
    if estado_clicado:
        menu_contexto = tk.Menu(janela, tearoff=0)
        menu_contexto.add_command(
            label="Marcar/Desmarcar como Aceitação",
            command=estado_clicado.toggle_aceitacao
        )
        menu_contexto.add_command(
            label="Renomear Estado...",
            command=lambda: renomear_estado(estado_clicado)
        )
        menu_contexto.add_command(
            label="Alterar Cor...",
            command=lambda: mudar_cor_estado(estado_clicado)
        )
        menu_contexto.post(event.x_root, event.y_root)

def encontrar_estado_clicado(event):
    """
    Recebe um evento de clique e retorna o objeto Estado correspondente,
    ou None se o clique não foi em um estado.
    """
    itens_proximos = canvas.find_closest(event.x, event.y)
    if not itens_proximos:
        return None
        
    id_item_clicado = itens_proximos[0]
    tags_do_item = canvas.gettags(id_item_clicado)
    
    # Procura pela tag de nome, ignorando as tags de sistema
    tags_de_sistema = {"estado", "texto", "seta_inicial", "aceitacao"}
    tag_nome = next((tag for tag in tags_do_item if tag not in tags_de_sistema), None)
    
    # Retorna o objeto Estado do dicionário, se encontrado
    return estados.get(tag_nome)


# --- UI Setup ---
janela = tk.Tk()
janela.title("Mini-JFLAP em Python v8")
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
janela.config(menu=menu_bar)

# --- Toolbar ---
toolbar = tk.Frame(janela, bd=1, relief=tk.RAISED)
toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

# Usando um dicionário para carregar ícones de forma mais limpa
icones = {}
try:
    # Coloque seus ícones em uma pasta chamada 'icones'
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
canvas = tk.Canvas(janela, bg="white", highlightthickness=1, highlightbackground="black")
canvas.pack(fill="both", expand=True, padx=10, pady=10)

canvas.bind("<ButtonPress-1>", iniciar_movimento) # Botão 1 é o esquerdo
canvas.bind("<B1-Motion>", arrastar_objeto)
canvas.bind("<ButtonRelease-1>", finalizar_arraste) 
canvas.bind("<Double-Button-1>", toggle_aceitacao_event)
canvas.bind("<Button-3>", mostrar_menu_contexto) # Botão 3 é o direito

# --- Painel Inferior (Status Bar) ---
status_bar = tk.Frame(janela, bd=1, relief=tk.SUNKEN)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)
instrucoes = tk.Label(status_bar, text="Bem-vindo!", bd=1, relief=tk.FLAT, anchor=tk.W)
instrucoes.pack(fill=tk.X, padx=5, pady=2)


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

ativar_modo_arrastar() # Inicia no modo padrão
janela.mainloop()