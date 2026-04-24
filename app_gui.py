import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import calendar as cal

from calculo_reserva import valor_mensal_efetivo
from database import (
    listar_unidades,
    listar_unidades_disponiveis,
    listar_reservas_dashboard,
    relatorio_financeiro,
    relatorio_financeiro_mensal,
    registrar_cliente,
    obter_ou_criar_cliente,
    criar_reserva,
    validar_conflito_reserva,
    cancelar_reserva,
    listar_clientes,
    obter_metricas_dashboard,
    sincronizar_disponibilidade_unidades,
)


class SistemaCondominioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestão do Condomínio Arsenio Mateus")
        self.root.geometry("1400x820")
        self.root.minsize(1120, 680)
        self.root.configure(bg="#0b1020")

        self.colors = {
            "bg": "#0b1020",
            "sidebar": "#0f172a",
            "panel": "#111827",
            "panel_soft": "#1f2937",
            "surface": "#0f1628",
            "text": "#e2e8f0",
            "muted": "#94a3b8",
            "primary": "#2563eb",
            "border": "#243247",
            "success": "#16a34a",
            "warning": "#f59e0b",
        }

        self._configurar_estilos()
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.sidebar = tk.Frame(self.root, bg=self.colors["sidebar"], width=250)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.main = tk.Frame(self.root, bg=self.colors["bg"])
        self.main.grid(row=0, column=1, sticky="nsew", padx=(16, 16), pady=16)
        self.main.grid_rowconfigure(2, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        self.nav_buttons = {}
        self.current_view = "Reservas"
        self._construir_sidebar()
        self._construir_topo()
        self._construir_tabela()
        self._construir_insights()
        sincronizar_disponibilidade_unidades()
        self.atualizar_dashboard()
        self.mostrar_reservas_pendentes()

    def _construir_sidebar(self):
        tk.Label(
            self.sidebar,
            text="ARSENIO\nMATEUS",
            font=("Segoe UI", 18, "bold"),
            fg=self.colors["text"],
            bg=self.colors["sidebar"],
            justify="left",
        ).pack(anchor="w", padx=22, pady=(24, 10))

        tk.Label(
            self.sidebar,
            text="Condominium Admin",
            font=("Segoe UI", 10),
            fg=self.colors["muted"],
            bg=self.colors["sidebar"],
        ).pack(anchor="w", padx=22, pady=(0, 22))

        self._criar_nav("Dashboard", "Dashboard", self.mostrar_reservas_pendentes)
        self._criar_nav("Clientes", "Clientes", self.mostrar_clientes)
        self._criar_nav("Unidades", "Unidades", self.mostrar_unidades)
        self._criar_nav("Disponibilidade", "Disponibilidade", self.mostrar_unidades_disponiveis)
        self._criar_nav("Reservas", "Reservas", self.mostrar_reservas_pendentes)
        self._criar_nav("Relatório", "Relatório", self.mostrar_relatorio)
        self._definir_nav_ativo("Reservas")

    def _construir_topo(self):
        topo = tk.Frame(self.main, bg=self.colors["bg"])
        topo.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        topo.grid_columnconfigure(0, weight=1)

        tk.Label(
            topo,
            text="Dashboard de Operações",
            font=("Segoe UI", 20, "bold"),
            fg=self.colors["text"],
            bg=self.colors["bg"],
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            topo,
            text="Gestão de clientes, unidades e reservas em tempo real",
            font=("Segoe UI", 10),
            fg=self.colors["muted"],
            bg=self.colors["bg"],
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self._criar_acao(topo, "Nova Reserva", self.abrir_janela_reserva, primary=True).grid(
            row=0, column=1, rowspan=2, padx=(8, 0), sticky="e"
        )
        self._criar_acao(topo, "Novo Cliente", self.abrir_janela_cliente).grid(
            row=0, column=2, rowspan=2, padx=(8, 0), sticky="e"
        )

        cards = tk.Frame(self.main, bg=self.colors["bg"])
        cards.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        for i in range(4):
            cards.grid_columnconfigure(i, weight=1)

        self.kpi_labels = {}
        self.previous_metrics = {}
        self._criar_card_kpi(cards, "Total de Unidades", "0", 0, "UN")
        self._criar_card_kpi(cards, "Unidades Disponíveis", "0", 1, "DP")
        self._criar_card_kpi(cards, "Reservas Pendentes", "0", 2, "RS")
        self._criar_card_kpi(cards, "Volume Financeiro", "0.00 Kz", 3, "KZ")

    def _construir_tabela(self):
        painel = tk.Frame(self.main, bg=self.colors["panel"], highlightthickness=1, highlightbackground=self.colors["border"])
        painel.grid(row=2, column=0, sticky="nsew")
        painel.grid_rowconfigure(2, weight=1)
        painel.grid_columnconfigure(0, weight=1)

        cab = tk.Frame(painel, bg=self.colors["panel"])
        cab.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 8))
        cab.grid_columnconfigure(0, weight=1)

        tk.Label(
            cab,
            text="Reservas Ativas",
            font=("Segoe UI", 13, "bold"),
            fg=self.colors["text"],
            bg=self.colors["panel"],
        ).grid(row=0, column=0, sticky="w")

        tk.Button(
            cab,
            text="Atualizar",
            command=lambda: [self.atualizar_dashboard(), self.mostrar_reservas_pendentes()],
            bg=self.colors["surface"],
            fg=self.colors["text"],
            activebackground="#1b2438",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
        ).grid(row=0, column=1, sticky="e")
        self._add_hover(cab.grid_slaves(row=0, column=1)[0], self.colors["surface"], "#1e293b")

        acoes = tk.Frame(painel, bg=self.colors["panel"])
        acoes.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        tk.Button(
            acoes,
            text="Abrir Reserva",
            command=self.acao_abrir_reserva,
            bg=self.colors["primary"],
            fg="#ffffff",
            activebackground="#1d4ed8",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
        ).pack(side="left")
        tk.Button(
            acoes,
            text="Cancelar Reserva",
            command=self.acao_cancelar_reserva,
            bg="#7f1d1d",
            fg="#ffffff",
            activebackground="#991b1b",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=(8, 0))
        self._add_hover(acoes.pack_slaves()[0], self.colors["primary"], "#1d4ed8")
        self._add_hover(acoes.pack_slaves()[1], "#7f1d1d", "#991b1b")

        tabela_frame = tk.Frame(painel, bg=self.colors["panel"])
        tabela_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 12))
        tabela_frame.grid_rowconfigure(0, weight=1)
        tabela_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tabela_frame, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar_y = ttk.Scrollbar(tabela_frame, orient="vertical", command=self.tree.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar_y.set)

        self.status_label = tk.Label(
            self.main,
            text="Pronto.",
            font=("Segoe UI", 10),
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            anchor="w",
        )
        self.status_label.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        self.configurar_colunas(["ID", "Cliente", "Unidade", "Início", "Fim", "Valor", "Status"])

    def _construir_insights(self):
        insights = tk.Frame(self.main, bg=self.colors["bg"])
        insights.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        insights.grid_columnconfigure(0, weight=1)
        insights.grid_columnconfigure(1, weight=1)

        self.alertas_box = tk.Frame(
            insights,
            bg=self.colors["panel"],
            highlightthickness=1,
            highlightbackground=self.colors["border"],
        )
        self.alertas_box.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        tk.Label(
            self.alertas_box,
            text="Insights e Alertas",
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["text"],
            bg=self.colors["panel"],
        ).pack(anchor="w", padx=12, pady=(10, 4))
        self.alertas_label = tk.Label(
            self.alertas_box,
            text="-",
            justify="left",
            font=("Segoe UI", 9),
            fg=self.colors["muted"],
            bg=self.colors["panel"],
        )
        self.alertas_label.pack(anchor="w", padx=12, pady=(0, 12))

        charts = tk.Frame(
            insights,
            bg=self.colors["panel"],
            highlightthickness=1,
            highlightbackground=self.colors["border"],
        )
        charts.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        tk.Label(
            charts,
            text="Revenue / Occupancy",
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["text"],
            bg=self.colors["panel"],
        ).pack(anchor="w", padx=12, pady=(10, 4))
        self.chart_canvas = tk.Canvas(
            charts,
            width=460,
            height=120,
            bg=self.colors["panel"],
            bd=0,
            highlightthickness=0,
        )
        self.chart_canvas.pack(fill="x", padx=10, pady=(0, 10))

    def limpar_tabela(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#0f172a",
            foreground="#cbd5e1",
            fieldbackground="#0f172a",
            rowheight=34,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#0b1324",
            foreground="#e2e8f0",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", "#1d4ed8")],
            foreground=[("selected", "#f8fafc")],
        )
        style.configure("TCombobox", fieldbackground="#0f172a", foreground="#e2e8f0")

    def _criar_nav(self, text, key, command):
        icon_map = {
            "Dashboard": "DB",
            "Clientes": "CL",
            "Unidades": "UN",
            "Disponibilidade": "DP",
            "Reservas": "RS",
            "Relatório": "RP",
        }
        btn = tk.Button(
            self.sidebar,
            text=f"{icon_map.get(text, '  ')}   {text}",
            command=lambda: self._on_nav_click(key, command),
            bg=self.colors["sidebar"],
            fg=self.colors["muted"],
            activebackground="#1e293b",
            activeforeground="#f8fafc",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            relief="flat",
            padx=16,
            pady=11,
            anchor="w",
            cursor="hand2",
        )
        btn.pack(fill="x", padx=14, pady=3)
        self.nav_buttons[key] = btn
        self._add_hover(btn, self.colors["sidebar"], "#1e293b", active_only=False)

    def _on_nav_click(self, key, command):
        self._definir_nav_ativo(key)
        command()

    def _definir_nav_ativo(self, key):
        self.current_view = key
        for nav_key, btn in self.nav_buttons.items():
            active = nav_key == key
            btn.configure(
                bg="#1e293b" if active else self.colors["sidebar"],
                fg="#f8fafc" if active else self.colors["muted"],
            )

    def _criar_acao(self, parent, text, command, primary=False):
        if primary:
            bg, fg, active = self.colors["primary"], "#ffffff", "#1d4ed8"
        else:
            bg, fg, active = self.colors["surface"], self.colors["text"], "#1b2438"
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active,
            activeforeground=fg,
            font=("Segoe UI", 10, "bold"),
            bd=0,
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2",
        )
        self._add_hover(btn, bg, active)
        return btn

    def _criar_card_kpi(self, parent, titulo, valor_inicial, column, icon_text):
        card = tk.Frame(parent, bg=self.colors["panel_soft"], highlightthickness=1, highlightbackground=self.colors["border"])
        card.grid(row=0, column=column, padx=(0 if column == 0 else 10, 0), pady=0, sticky="nsew")

        topo = tk.Frame(card, bg=self.colors["panel_soft"])
        topo.pack(fill="x", padx=14, pady=(10, 0))

        tk.Label(
            topo,
            text=icon_text,
            font=("Segoe UI", 8, "bold"),
            fg="#cbd5e1",
            bg="#334155",
            padx=6,
            pady=2,
        ).pack(side="right")

        tk.Label(
            topo,
            text=titulo,
            font=("Segoe UI", 10),
            bg=self.colors["panel_soft"],
            fg=self.colors["muted"],
            anchor="w",
        ).pack(side="left")

        valor_label = tk.Label(
            card,
            text=valor_inicial,
            font=("Segoe UI", 17, "bold"),
            bg=self.colors["panel_soft"],
            fg=self.colors["text"],
            anchor="w",
        )
        valor_label.pack(fill="x", padx=14, pady=(0, 12))
        trend_label = tk.Label(
            card,
            text="--",
            font=("Segoe UI", 9),
            bg=self.colors["panel_soft"],
            fg=self.colors["muted"],
            anchor="w",
        )
        trend_label.pack(fill="x", padx=14, pady=(0, 10))
        self.kpi_labels[titulo] = (valor_label, trend_label)

    def _add_hover(self, widget, normal_bg, hover_bg, active_only=True):
        def on_enter(_event):
            if not active_only or widget.cget("bg") == normal_bg:
                widget.configure(bg=hover_bg)
        def on_leave(_event):
            if not active_only or widget.cget("bg") == hover_bg:
                widget.configure(bg=normal_bg)
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _set_kpi(self, titulo, valor_texto, valor_numerico):
        valor_label, trend_label = self.kpi_labels[titulo]
        valor_label.config(text=valor_texto)
        anterior = self.previous_metrics.get(titulo)
        if anterior is None:
            trend_label.config(text="Sem histórico", fg=self.colors["muted"])
        else:
            diff = valor_numerico - anterior
            if diff > 0:
                trend_label.config(text=f"+{diff:.2f}", fg="#22c55e")
            elif diff < 0:
                trend_label.config(text=f"{diff:.2f}", fg="#ef4444")
            else:
                trend_label.config(text="Sem variação", fg=self.colors["muted"])
        self.previous_metrics[titulo] = valor_numerico

    def _desenhar_graficos(self, total_unidades, unidades_disponiveis):
        self.chart_canvas.delete("all")
        mensal = relatorio_financeiro_mensal()
        receitas = [float(item[2]) for item in mensal[:6]][::-1]
        if not receitas:
            receitas = [0]
        max_receita = max(receitas) or 1

        left = 15
        base_y = 95
        bar_w = 28
        gap = 12
        for i, valor in enumerate(receitas):
            x1 = left + i * (bar_w + gap)
            x2 = x1 + bar_w
            h = int((valor / max_receita) * 60)
            self.chart_canvas.create_rectangle(x1, base_y - h, x2, base_y, fill="#2563eb", width=0)

        self.chart_canvas.create_text(15, 108, text="Revenue", anchor="w", fill="#94a3b8", font=("Segoe UI", 9))

        occ_x1, occ_y1, occ_x2, occ_y2 = 250, 36, 440, 58
        ocupacao = 0 if total_unidades == 0 else (total_unidades - unidades_disponiveis) / total_unidades
        self.chart_canvas.create_rectangle(occ_x1, occ_y1, occ_x2, occ_y2, fill="#1e293b", width=0)
        self.chart_canvas.create_rectangle(
            occ_x1, occ_y1, occ_x1 + int((occ_x2 - occ_x1) * ocupacao), occ_y2, fill="#16a34a", width=0
        )
        self.chart_canvas.create_text(250, 24, text="Occupancy", anchor="w", fill="#94a3b8", font=("Segoe UI", 9))
        self.chart_canvas.create_text(
            445, 47, text=f"{ocupacao * 100:.1f}%", anchor="e", fill="#e2e8f0", font=("Segoe UI", 10, "bold")
        )

    def _atualizar_alertas(self, total_unidades, unidades_disponiveis, reservas_pendentes, total_valor):
        ocupacao_pct = 0 if total_unidades == 0 else ((total_unidades - unidades_disponiveis) / total_unidades) * 100
        alertas = [
            f"- Ocupação atual: {ocupacao_pct:.1f}%",
            f"- Reservas pendentes: {reservas_pendentes}",
            f"- Receita acumulada: {total_valor:.2f} Kz",
        ]
        if ocupacao_pct > 85:
            alertas.append("- Alerta: alta ocupação, considerar reajuste de preço.")
        if reservas_pendentes > 10:
            alertas.append("- Alerta: fila de reservas alta, priorizar confirmação.")
        self.alertas_label.config(text="\n".join(alertas))

    def atualizar_dashboard(self):
        try:
            m = obter_metricas_dashboard()
            total_unidades = m["total_unidades"]
            unidades_disponiveis = m["unidades_disponiveis"]
            reservas_pendentes = m["reservas_pendentes"]
            total_valor = m["valor_total_financeiro"]

            self._set_kpi("Total de Unidades", str(total_unidades), float(total_unidades))
            self._set_kpi("Unidades Disponíveis", str(unidades_disponiveis), float(unidades_disponiveis))
            self._set_kpi("Reservas Pendentes", str(reservas_pendentes), float(reservas_pendentes))
            self._set_kpi("Volume Financeiro", f"{total_valor:.2f} Kz", float(total_valor))
            self._desenhar_graficos(total_unidades, unidades_disponiveis)
            self._atualizar_alertas(total_unidades, unidades_disponiveis, reservas_pendentes, total_valor)
            self.status_label.config(text="Dashboard atualizado com sucesso.")
        except Exception as e:
            self.status_label.config(text=f"Falha ao atualizar dashboard: {e}")

    def atualizar_tudo_apos_reserva(self):
        # Mantém o painel sempre consistente logo após gravação.
        self.atualizar_dashboard()
        self.carregar_reservas_dashboard()

    def atualizar_todos_dados(self):
        self.atualizar_dashboard()
        self.carregar_reservas_dashboard()

    def configurar_colunas(self, titulos):
        colunas = [f"c{i}" for i in range(len(titulos))]
        self.tree["columns"] = colunas

        for i, titulo in enumerate(titulos):
            col_id = f"c{i}"
            self.tree.heading(col_id, text=titulo)
            self.tree.column(col_id, width=150, anchor="center")

    def mostrar_clientes(self):
        try:
            self._definir_nav_ativo("Clientes")
            dados = listar_clientes()
            self.limpar_tabela()
            self.configurar_colunas(["ID", "Nome", "Telefone", "Email"])

            for linha in dados:
                self.tree.insert("", "end", values=linha)

            self.status_label.config(text=f"{len(dados)} clientes carregados.")
            self.atualizar_dashboard()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar clientes:\n{e}")

    def mostrar_unidades(self):
        try:
            self._definir_nav_ativo("Unidades")
            dados = listar_unidades()
            self.limpar_tabela()
            self.configurar_colunas(
                ["Código", "Nome", "Andar", "Tipo", "Área m2", "Preço mensal (Kz)", "Disponível"]
            )

            for linha in dados:
                _uid, codigo, nome, andar, tipo, area_m2, disponivel, preco_m = linha
                estado = "Sim" if disponivel else "Não"
                pm = valor_mensal_efetivo(preco_m, tipo)
                self.tree.insert(
                    "",
                    "end",
                    values=(codigo, nome, andar, tipo, area_m2, f"{pm:,.0f}", estado),
                )

            self.status_label.config(text=f"{len(dados)} unidades carregadas.")
            self.atualizar_dashboard()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar unidades:\n{e}")

    def mostrar_unidades_disponiveis(self):
        try:
            self._definir_nav_ativo("Disponibilidade")
            dados = listar_unidades_disponiveis()
            self.limpar_tabela()
            self.configurar_colunas(
                ["Código", "Nome", "Andar", "Tipo", "Área m2", "Preço mensal (Kz)", "Disponível"]
            )

            for linha in dados:
                _uid, codigo, nome, andar, tipo, area_m2, disponivel, preco_m = linha
                estado = "Sim" if disponivel else "Não"
                pm = valor_mensal_efetivo(preco_m, tipo)
                self.tree.insert(
                    "",
                    "end",
                    values=(codigo, nome, andar, tipo, area_m2, f"{pm:,.0f}", estado),
                )

            self.status_label.config(
                text=f"{len(dados)} unidades disponíveis carregadas."
            )
            self.atualizar_dashboard()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar unidades disponíveis:\n{e}")

    def mostrar_reservas_pendentes(self):
        try:
            self._definir_nav_ativo("Reservas")
            self.carregar_reservas_dashboard()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar reservas pendentes:\n{e}")

    def carregar_reservas_dashboard(self):
        try:
            self.limpar_tabela()
            self.configurar_colunas(["ID", "Cliente", "Unidade", "Data Início", "Data Fim", "Valor", "Status"])

            dados = listar_reservas_dashboard()
            for linha in dados:
                rid, cliente, unidade, inicio, fim, valor, estado = linha
                valor_fmt = f"{float(valor):,.2f}" if valor is not None else "0.00"
                estado_texto = (estado or "pendente").upper()
                tag = "status_pendente"
                if estado_texto == "CANCELADA":
                    tag = "status_cancelada"
                elif estado_texto in ("PAGA", "ATIVA"):
                    tag = "status_ativa"
                self.tree.insert(
                    "",
                    "end",
                    values=(rid, cliente, unidade, inicio, fim, valor_fmt, f"● {estado_texto}"),
                    tags=(tag,),
                )

            self.tree.tag_configure("status_pendente", foreground="#fbbf24", background="#121a2d")
            self.tree.tag_configure("status_cancelada", foreground="#f87171", background="#2a1111")
            self.tree.tag_configure("status_ativa", foreground="#34d399", background="#0f201a")

            self.status_label.config(
                text=f"{len(dados)} reservas carregadas."
            )
            self.atualizar_dashboard()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar reservas no dashboard:\n{e}")

    def mostrar_relatorio(self):
        try:
            self._definir_nav_ativo("Relatório")
            total_reservas, total_valor = relatorio_financeiro()
            messagebox.showinfo(
                "Relatório Financeiro",
                f"Total de reservas: {total_reservas}\n"
                f"Valor total reservado: {total_valor:.2f} Kz",
            )
            self.status_label.config(text="Relatório financeiro exibido.")
            self.atualizar_dashboard()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar relatório:\n{e}")

    def acao_abrir_reserva(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione uma reserva na tabela.")
            return
        valores = self.tree.item(selecionado, "values")
        if not valores or len(valores) < 7:
            return
        messagebox.showinfo(
            "Detalhes da Reserva",
            f"Reserva: {valores[0]}\nCliente: {valores[1]}\nUnidade: {valores[2]}\nStatus: {valores[6]}",
        )

    def acao_cancelar_reserva(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione uma reserva para cancelar.")
            return

        valores = self.tree.item(selecionado, "values")
        if not valores or len(valores) < 1:
            messagebox.showwarning("Aviso", "Seleção inválida.")
            return

        try:
            reserva_id = int(valores[0])
        except ValueError:
            messagebox.showwarning("Aviso", "ID da reserva inválido.")
            return

        confirmar = messagebox.askyesno("Confirmar", f"Deseja cancelar a reserva #{reserva_id}?")
        if not confirmar:
            return

        try:
            sucesso = cancelar_reserva(reserva_id)
            if sucesso:
                messagebox.showinfo("Sucesso", "Reserva cancelada com sucesso.")
                self.atualizar_todos_dados()
            else:
                messagebox.showwarning("Aviso", "Reserva não encontrada.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao cancelar reserva:\n{e}")

    def _abrir_calendario(self, parent, target_entry, on_selected=None):
        popup = tk.Toplevel(parent)
        popup.title("Selecionar data")
        popup.configure(bg=self.colors["panel"])
        popup.resizable(False, False)
        popup.transient(parent)
        popup.grab_set()

        hoje = date.today()
        estado = {"ano": hoje.year, "mes": hoje.month}

        cabecalho = tk.Frame(popup, bg=self.colors["panel"])
        cabecalho.pack(fill="x", padx=10, pady=(10, 6))
        grade = tk.Frame(popup, bg=self.colors["panel"])
        grade.pack(padx=10, pady=(0, 10))

        titulo_mes = tk.Label(
            cabecalho,
            text="",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["text"],
            bg=self.colors["panel"],
        )
        titulo_mes.pack(side="left", expand=True)

        def mudar_mes(delta):
            estado["mes"] += delta
            if estado["mes"] < 1:
                estado["mes"] = 12
                estado["ano"] -= 1
            elif estado["mes"] > 12:
                estado["mes"] = 1
                estado["ano"] += 1
            desenhar()

        tk.Button(
            cabecalho,
            text="<",
            command=lambda: mudar_mes(-1),
            bg=self.colors["surface"],
            fg=self.colors["text"],
            activebackground="#1b2438",
            bd=0,
            width=3,
            cursor="hand2",
        ).pack(side="left", padx=(0, 6))
        tk.Button(
            cabecalho,
            text=">",
            command=lambda: mudar_mes(1),
            bg=self.colors["surface"],
            fg=self.colors["text"],
            activebackground="#1b2438",
            bd=0,
            width=3,
            cursor="hand2",
        ).pack(side="right")

        def selecionar_data(dia):
            data_escolhida = date(estado["ano"], estado["mes"], dia).strftime("%Y-%m-%d")
            target_entry.configure(state="normal")
            target_entry.delete(0, tk.END)
            target_entry.insert(0, data_escolhida)
            target_entry.configure(state="readonly")
            if on_selected:
                on_selected()
            popup.destroy()

        def desenhar():
            for widget in grade.winfo_children():
                widget.destroy()

            titulo_mes.config(text=f"{cal.month_name[estado['mes']]} {estado['ano']}")

            dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
            for col, nome_dia in enumerate(dias_semana):
                tk.Label(
                    grade,
                    text=nome_dia,
                    font=("Segoe UI", 9, "bold"),
                    fg=self.colors["muted"],
                    bg=self.colors["panel"],
                    width=4,
                ).grid(row=0, column=col, pady=(0, 6))

            semanas = cal.monthcalendar(estado["ano"], estado["mes"])
            for linha, semana in enumerate(semanas, start=1):
                for col, dia in enumerate(semana):
                    if dia == 0:
                        tk.Label(grade, text=" ", width=4, bg=self.colors["panel"]).grid(row=linha, column=col)
                        continue
                    tk.Button(
                        grade,
                        text=str(dia),
                        width=4,
                        command=lambda d=dia: selecionar_data(d),
                        bg=self.colors["surface"],
                        fg=self.colors["text"],
                        activebackground="#1d4ed8",
                        activeforeground="#ffffff",
                        bd=0,
                        cursor="hand2",
                    ).grid(row=linha, column=col, padx=1, pady=1)

        desenhar()

    def abrir_janela_cliente(self):
        janela = tk.Toplevel(self.root)
        janela.title("Cadastrar Cliente")
        janela.geometry("460x340")
        janela.configure(bg=self.colors["panel"])

        tk.Label(janela, text="Nome", bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI", 11)).pack(
            pady=(15, 5)
        )
        nome_entry = tk.Entry(janela, width=35, font=("Segoe UI", 11), bd=0, relief="flat")
        nome_entry.pack()

        tk.Label(janela, text="Telefone", bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI", 11)).pack(
            pady=(10, 5)
        )
        telefone_entry = tk.Entry(janela, width=35, font=("Segoe UI", 11), bd=0, relief="flat")
        telefone_entry.pack()

        tk.Label(janela, text="Email", bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI", 11)).pack(
            pady=(10, 5)
        )
        email_entry = tk.Entry(janela, width=35, font=("Segoe UI", 11), bd=0, relief="flat")
        email_entry.pack()

        def salvar_cliente():
            nome = nome_entry.get().strip()
            telefone = telefone_entry.get().strip()
            email = email_entry.get().strip()

            if not nome:
                messagebox.showwarning("Aviso", "O nome é obrigatório.")
                return

            try:
                cliente_id = registrar_cliente(nome, telefone, email)
                if cliente_id:
                    messagebox.showinfo(
                        "Sucesso",
                        f"Cliente cadastrado com sucesso! ID: {cliente_id}",
                    )
                    self.status_label.config(
                        text=f"Cliente '{nome}' cadastrado com sucesso."
                    )
                    self.atualizar_dashboard()
                    janela.destroy()
                else:
                    messagebox.showerror(
                        "Erro", "Não foi possível cadastrar o cliente."
                    )
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao cadastrar cliente:\n{e}")

        tk.Button(
            janela,
            text="Salvar Cliente",
            command=salvar_cliente,
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            font=("Segoe UI", 10, "bold"),
            width=18,
            bd=0,
            relief="flat",
            cursor="hand2",
        ).pack(pady=20)

    def abrir_janela_reserva(self):
        janela = tk.Toplevel(self.root)
        janela.title("Fazer Reserva")
        janela.geometry("600x540")
        janela.configure(bg=self.colors["panel"])

        tk.Label(
            janela,
            text="Nome do Cliente",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Segoe UI", 11),
        ).pack(pady=(16, 5))
        nome_cliente_entry = tk.Entry(janela, width=42, font=("Segoe UI", 11), bd=0, relief="flat")
        nome_cliente_entry.pack()

        tk.Label(
            janela,
            text="Telefone",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Segoe UI", 11),
        ).pack(pady=(10, 5))
        telefone_entry = tk.Entry(janela, width=42, font=("Segoe UI", 11), bd=0, relief="flat")
        telefone_entry.pack()

        tk.Label(
            janela,
            text="Email",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Segoe UI", 11),
        ).pack(pady=(10, 5))
        email_entry = tk.Entry(janela, width=42, font=("Segoe UI", 11), bd=0, relief="flat")
        email_entry.pack()

        tk.Label(
            janela, text="Data Início", bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI", 11)
        ).pack(pady=(12, 5))
        data_inicio_frame = tk.Frame(janela, bg=self.colors["panel"])
        data_inicio_frame.pack()
        data_inicio_entry = tk.Entry(
            data_inicio_frame, width=28, font=("Segoe UI", 11), bd=0, relief="flat", state="readonly"
        )
        data_inicio_entry.pack(side="left", padx=(0, 8))
        tk.Button(
            data_inicio_frame,
            text="Calendario",
            command=lambda: self._abrir_calendario(janela, data_inicio_entry, carregar_unidades_disponiveis),
            bg="#334155",
            fg="white",
            activebackground="#1e293b",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
        ).pack(side="left")

        tk.Label(
            janela, text="Data Fim", bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI", 11)
        ).pack(pady=(10, 5))
        data_fim_frame = tk.Frame(janela, bg=self.colors["panel"])
        data_fim_frame.pack()
        data_fim_entry = tk.Entry(
            data_fim_frame, width=28, font=("Segoe UI", 11), bd=0, relief="flat", state="readonly"
        )
        data_fim_entry.pack(side="left", padx=(0, 8))
        tk.Button(
            data_fim_frame,
            text="Calendario",
            command=lambda: self._abrir_calendario(janela, data_fim_entry, carregar_unidades_disponiveis),
            bg="#334155",
            fg="white",
            activebackground="#1e293b",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
        ).pack(side="left")

        tk.Label(
            janela,
            text="Unidades disponíveis (selecione para preencher)",
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
        ).pack(pady=(12, 4))

        unidades_combo = ttk.Combobox(
            janela,
            width=52,
            state="readonly",
            font=("Segoe UI", 10),
        )
        unidades_combo.pack(pady=(0, 10))

        info_label = tk.Label(
            janela,
            text="Preencha as datas para carregar unidades disponíveis.",
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
        )
        info_label.pack(pady=(8, 12))

        unidades_disponiveis_cache = []

        def datas_validas():
            data_inicio = data_inicio_entry.get().strip()
            data_fim = data_fim_entry.get().strip()
            if not data_inicio or not data_fim:
                return False
            try:
                inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
                fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
                return inicio < fim
            except ValueError:
                return False

        def carregar_unidades_disponiveis(_event=None):
            if not datas_validas():
                info_label.config(
                    text="Datas inválidas ou incompletas. Corrija sem perder os dados preenchidos.",
                    fg="#f59e0b",
                )
                return
            try:
                data_inicio = data_inicio_entry.get().strip()
                data_fim = data_fim_entry.get().strip()
                opcao_atual = unidades_combo.get().strip()
                unidades = listar_unidades_disponiveis(data_inicio, data_fim)
                unidades_disponiveis_cache[:] = unidades

                if not unidades:
                    unidades_combo["values"] = ["Nenhuma unidade disponível para o período"]
                    unidades_combo.current(0)
                    info_label.config(text="Sem disponibilidade no período selecionado.", fg="#f59e0b")
                    return

                opcoes = [
                    f"{uid} | {codigo} | {tipo} | Andar {andar}"
                    for uid, codigo, _nome, andar, tipo, _area_m2, _disp, _pm in unidades
                ]
                unidades_combo["values"] = opcoes
                if opcao_atual and opcao_atual in opcoes:
                    unidades_combo.set(opcao_atual)
                else:
                    unidades_combo.current(0)
                info_label.config(text=f"{len(unidades)} unidades disponíveis encontradas.", fg="#22c55e")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar unidades disponíveis:\n{e}")

        def salvar_reserva():
            try:
                nome_cliente = nome_cliente_entry.get().strip()
                telefone = telefone_entry.get().strip()
                email = email_entry.get().strip()
                data_inicio = data_inicio_entry.get().strip()
                data_fim = data_fim_entry.get().strip()
                selecionado = unidades_combo.current()
                erros = []
                foco_erro = None

                if not nome_cliente:
                    erros.append("- Nome do cliente é obrigatório.")
                    foco_erro = foco_erro or nome_cliente_entry
                if not telefone:
                    erros.append("- Telefone é obrigatório no ato da reserva.")
                    foco_erro = foco_erro or telefone_entry
                if not email:
                    erros.append("- Email é obrigatório no ato da reserva.")
                    foco_erro = foco_erro or email_entry
                if not data_inicio or not data_fim:
                    erros.append("- Datas de início e fim são obrigatórias.")
                    foco_erro = foco_erro or data_inicio_entry
                elif not datas_validas():
                    erros.append("- Data fim deve ser posterior à data início (AAAA-MM-DD).")
                    foco_erro = foco_erro or data_inicio_entry

                if selecionado < 0 or selecionado >= len(unidades_disponiveis_cache):
                    erros.append("- Selecione uma unidade disponível.")
                    foco_erro = foco_erro or unidades_combo

                if erros:
                    messagebox.showwarning(
                        "Corrigir Dados da Reserva",
                        "Existem campos inválidos. Corrija e tente novamente:\n\n" + "\n".join(erros),
                    )
                    if foco_erro:
                        foco_erro.focus_set()
                    return

                unidade_id, unidade_codigo, _nome, _andar, _tipo, _area_m2, _disp, _pm = (
                    unidades_disponiveis_cache[selecionado]
                )

                cliente_id = obter_ou_criar_cliente(nome_cliente, telefone, email)
                if not cliente_id:
                    messagebox.showerror("Erro", "Não foi possível obter ou criar o cliente automaticamente.")
                    return
                if validar_conflito_reserva(unidade_id, data_inicio, data_fim):
                    messagebox.showerror(
                        "Erro",
                        "Conflito detectado: unidade indisponível no período.\n"
                        "Ajuste datas/unidade e tente novamente (dados preenchidos foram mantidos).",
                    )
                    return

                sucesso, mensagem = criar_reserva(
                    cliente_id,
                    unidade_id,
                    data_inicio,
                    data_fim,
                    "PENDENTE",
                )

                if sucesso:
                    messagebox.showinfo("Sucesso", mensagem)
                    self.status_label.config(
                        text=f"Reserva criada para '{nome_cliente}' na unidade {unidade_codigo}."
                    )
                    self.atualizar_tudo_apos_reserva()
                    janela.destroy()
                else:
                    messagebox.showerror("Erro", mensagem)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar reserva:\n{e}")

        botoes_principais = tk.Frame(janela, bg=self.colors["panel"])
        botoes_principais.pack(pady=(4, 10))
        tk.Button(
            botoes_principais,
            text="Atualizar Unidades",
            command=carregar_unidades_disponiveis,
            bg="#334155",
            fg="white",
            activebackground="#1e293b",
            font=("Segoe UI", 10, "bold"),
            width=16,
            bd=0,
            relief="flat",
            cursor="hand2",
        ).pack(side="left", padx=(0, 10))
        tk.Button(
            botoes_principais,
            text="Salvar Reserva",
            command=salvar_reserva,
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            font=("Segoe UI", 10, "bold"),
            width=16,
            bd=0,
            relief="flat",
            cursor="hand2",
        ).pack(side="left")

        tk.Button(
            janela,
            text="Cancelar / Fechar",
            command=janela.destroy,
            bg="#7f1d1d",
            fg="white",
            activebackground="#991b1b",
            font=("Segoe UI", 10, "bold"),
            width=18,
            bd=0,
            relief="flat",
            cursor="hand2",
        ).pack(pady=(0, 8))


if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaCondominioApp(root)
    root.mainloop()