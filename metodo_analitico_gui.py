"""
Método Analítico para Programação Linear — Interface Gráfica
=============================================================
Resolve problemas de PL com 2 variáveis pelo método de
enumeração de vértices (método analítico).

Uso:  python metodo_analitico_gui.py
"""

import tkinter as tk
from tkinter import ttk
import traceback
import sympy as sp
from itertools import combinations


# ====================================================================
# LÓGICA DO MÉTODO ANALÍTICO
# ====================================================================
def resolver_pl(nome_x, nome_y, expr_obj, exprs_restr, sentido):
    """
    Resolve um problema de PL pelo método de enumeração de vértices.
    Retorna (melhor_vertice, lista_de_todos_vertices_avaliados).
    """
    x, y = sp.symbols([nome_x, nome_y], real=True)
    simbolos = {nome_x: x, nome_y: y}

    Z = sp.sympify(expr_obj, locals=simbolos)

    # Converte cada restrição para a forma "g(x,y) <= 0"
    restricoes = []
    for texto in exprs_restr:
        t = texto.replace("==", "=")
        achou = False
        for op in ("<=", ">=", "="):
            if op in t:
                esq, dir_ = t.split(op, 1)
                lhs = sp.sympify(esq, locals=simbolos)
                rhs = sp.sympify(dir_, locals=simbolos)
                if op == "<=":
                    restricoes.append(lhs - rhs)
                elif op == ">=":
                    restricoes.append(rhs - lhs)
                else:  # igualdade vira duas
                    restricoes.append(lhs - rhs)
                    restricoes.append(rhs - lhs)
                achou = True
                break
        if not achou:
            raise ValueError(f"Restrição sem operador (<=, >=, =): {texto!r}")

    # Não-negatividade implícita
    restricoes += [-x, -y]

    # Enumera vértices: interseção de pares de fronteiras
    candidatos = []
    for r1, r2 in combinations(restricoes, 2):
        try:
            sol = sp.solve([sp.Eq(r1, 0), sp.Eq(r2, 0)], (x, y), dict=True)
        except Exception:
            continue
        for s in sol:
            if x not in s or y not in s:
                continue
            xv, yv = s[x], s[y]
            if not (xv.is_real and yv.is_real):
                continue
            # Viável se satisfaz todas as restrições
            viavel = True
            for g in restricoes:
                if sp.simplify(g.subs({x: xv, y: yv})) > 1e-9:
                    viavel = False
                    break
            if viavel:
                candidatos.append((sp.nsimplify(xv), sp.nsimplify(yv)))

    # Remove duplicatas
    vertices_unicos = []
    vistos = set()
    for xv, yv in candidatos:
        chave = (round(float(xv), 8), round(float(yv), 8))
        if chave not in vistos:
            vistos.add(chave)
            vertices_unicos.append((xv, yv))

    if not vertices_unicos:
        return None, []

    # Avalia Z em cada vértice
    avaliados = [(v, sp.simplify(Z.subs({x: v[0], y: v[1]}))) for v in vertices_unicos]
    melhor = (max(avaliados, key=lambda a: float(a[1])) if sentido == "max"
              else min(avaliados, key=lambda a: float(a[1])))
    return melhor, avaliados


# ====================================================================
# INTERFACE GRÁFICA
# ====================================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("Método Analítico — Programação Linear")
        root.geometry("640x680")
        root.configure(padx=20, pady=15)

        style = ttk.Style()
        style.configure("Titulo.TLabel", font=("Segoe UI", 13, "bold"))

        # Cabeçalho
        ttk.Label(root, text="Resolva um problema de PL com 2 variáveis",
                  style="Titulo.TLabel").pack(anchor="w", pady=(0, 10))

        # Variáveis + sentido
        frm_vars = ttk.Frame(root)
        frm_vars.pack(fill="x", pady=4)
        ttk.Label(frm_vars, text="Variáveis:").pack(side="left")
        self.var1 = tk.Entry(frm_vars, width=6)
        self.var1.pack(side="left", padx=4)
        self.var2 = tk.Entry(frm_vars, width=6)
        self.var2.pack(side="left", padx=4)

        ttk.Label(frm_vars, text="     Objetivo:").pack(side="left")
        self.sentido = tk.StringVar(value="max")
        ttk.Radiobutton(frm_vars, text="Maximizar", value="max",
                        variable=self.sentido).pack(side="left", padx=2)
        ttk.Radiobutton(frm_vars, text="Minimizar", value="min",
                        variable=self.sentido).pack(side="left", padx=2)

        # Função objetivo
        ttk.Label(root, text="Função objetivo:  Z =").pack(anchor="w", pady=(12, 2))
        self.entry_obj = tk.Entry(root, font=("Consolas", 11))
        self.entry_obj.pack(fill="x")

        # Restrições
        ttk.Label(root, text="Restrições:").pack(anchor="w", pady=(12, 2))
        self.frame_restr = ttk.Frame(root)
        self.frame_restr.pack(fill="x")
        self.entries_restr = []
        for _ in range(3):
            self.add_restricao()

        frm_btns = ttk.Frame(root)
        frm_btns.pack(anchor="w", pady=4)
        ttk.Button(frm_btns, text="+ adicionar restrição",
                   command=self.add_restricao).pack(side="left", padx=2)
        ttk.Button(frm_btns, text="− remover última",
                   command=self.del_restricao).pack(side="left", padx=2)

        ttk.Label(root,
                  text="Dica: use * para multiplicar (ex: 3*x, não 3x). "
                       "Use <=, >= ou = nas restrições.",
                  foreground="gray").pack(anchor="w", pady=(8, 0))

        # Botão Resolver (tk.Button com cor — mais confiável que ttk em alguns sistemas)
        tk.Button(root, text="✓  RESOLVER", command=self.resolver,
                  font=("Segoe UI", 11, "bold"), bg="#4CAF50", fg="white",
                  activebackground="#45a049", relief="flat",
                  cursor="hand2").pack(pady=12, ipadx=30, ipady=6)

        # Caixa de saída
        ttk.Label(root, text="Resultado:").pack(anchor="w")
        self.saida = tk.Text(root, height=14, font=("Consolas", 10),
                             bg="#f5f5f5", fg="black", relief="flat", wrap="word",
                             insertbackground="black")
        self.saida.pack(fill="both", expand=True, pady=4)

    def add_restricao(self):
        entry = tk.Entry(self.frame_restr, font=("Consolas", 11))
        entry.pack(fill="x", pady=2)
        self.entries_restr.append(entry)

    def del_restricao(self):
        if self.entries_restr:
            self.entries_restr.pop().destroy()

    def resolver(self):
        self.saida.delete("1.0", "end")
        try:
            nome_x = self.var1.get().strip()
            nome_y = self.var2.get().strip()
            obj = self.entry_obj.get().strip()
            restrs = [e.get().strip() for e in self.entries_restr if e.get().strip()]

            # Validações
            faltando = []
            if not nome_x or not nome_y:
                faltando.append("nomes das variáveis")
            if not obj:
                faltando.append("função objetivo")
            if not restrs:
                faltando.append("pelo menos uma restrição")
            if faltando:
                self.saida.insert("end",
                                  "Faltam dados: " + ", ".join(faltando) + ".")
                return
            if nome_x == nome_y:
                self.saida.insert("end",
                                  "As duas variáveis precisam ter nomes diferentes.")
                return

            melhor, todos = resolver_pl(nome_x, nome_y, obj, restrs,
                                        self.sentido.get())

            if melhor is None:
                self.saida.insert("end",
                                  "Problema INVIÁVEL — região viável vazia.\n"
                                  "Verifique se as restrições não se contradizem.")
                return

            # Tabela de vértices
            self.saida.insert("end", "Vértices da região viável:\n")
            self.saida.insert("end", "-" * 45 + "\n")
            cab = f"({nome_x}, {nome_y})"
            self.saida.insert("end", f"{cab:<25}{'Z':>15}\n")
            for (xv, yv), z in todos:
                coord = f"({xv}, {yv})"
                self.saida.insert("end", f"{coord:<25}{str(z):>15}\n")

            # Solução ótima
            (xv, yv), z = melhor
            self.saida.insert("end", "\n" + "=" * 45 + "\n")
            self.saida.insert("end",
                              f"Solução ótima ({self.sentido.get()}):\n"
                              f"  {nome_x} = {xv}   (≈ {float(xv):.4f})\n"
                              f"  {nome_y} = {yv}   (≈ {float(yv):.4f})\n"
                              f"  Z = {z}   (≈ {float(z):.4f})\n")

        except Exception:
            self.saida.insert("end",
                              "Erro ao resolver. Verifique a sintaxe das expressões.\n\n")
            self.saida.insert("end", traceback.format_exc())


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
