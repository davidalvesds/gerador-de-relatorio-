
import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import messagebox

import config
import dados
import excel_export
import relatorio


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Gerador de Entregas — Setrand")
        self.geometry("680x560")
        self.minsize(560, 420)

        self.base = None

        self._montar_interface()
        self._carregar_base_em_thread()


    def _montar_interface(self):
        frame_topo = tk.Frame(self, padx=14, pady=14)
        frame_topo.pack(fill="x")

        tk.Label(frame_topo, text="Município(s):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(
            frame_topo,
            text="(clique para escolher um; segure Ctrl para escolher vários)",
            font=("Segoe UI", 8), fg="#555555"
        ).pack(anchor="w", pady=(0, 6))

        frame_lista = tk.Frame(frame_topo)
        frame_lista.pack(fill="x")

        self.lista_municipios = tk.Listbox(
            frame_lista, selectmode="extended", height=8, exportselection=False
        )
        self.lista_municipios.pack(side="left", fill="both", expand=True)

        barra_lista = tk.Scrollbar(frame_lista, orient="vertical", command=self.lista_municipios.yview)
        barra_lista.pack(side="right", fill="y")
        self.lista_municipios.config(yscrollcommand=barra_lista.set)

        frame_botoes = tk.Frame(frame_topo)
        frame_botoes.pack(fill="x", pady=(10, 0))

        self.botao_gerar = tk.Button(
            frame_botoes, text="Gerar entrega(s)", command=self._gerar_clicado,
            bg="#2e6da4", fg="white", padx=12, pady=6, state="disabled"
        )
        self.botao_gerar.pack(side="left")

        self.botao_pasta = tk.Button(
            frame_botoes, text="Abrir pasta das entregas", command=self._abrir_pasta, padx=12, pady=6
        )
        self.botao_pasta.pack(side="left", padx=(8, 0))

        tk.Label(self, text="Andamento:", font=("Segoe UI", 10, "bold"), padx=14).pack(anchor="w", pady=(6, 0))

        frame_log = tk.Frame(self, padx=14, pady=4)
        frame_log.pack(fill="both", expand=True, pady=(4,14))
        

        self.texto_log = tk.Text(frame_log, height=16, state="disabled", wrap="word")
        self.texto_log.pack(side="left", fill="both", expand=True)

        barra_log = tk.Scrollbar(frame_log, orient="vertical", command=self.texto_log.yview)
        barra_log.pack(side="right", fill="y")
        self.texto_log.config(yscrollcommand=barra_log.set)


    def _log(self, texto):
        def _escrever():
            self.texto_log.config(state="normal")
            self.texto_log.insert("end", texto + "\n")
            self.texto_log.see("end")
            self.texto_log.config(state="disabled")
        self.after(0, _escrever)


    def _carregar_base_em_thread(self):
        self._log("Carregando lista de municípios, aguarde...")

        def _tarefa():
            try:
                base = dados.carregar_base(config)
                municipios = dados.listar_municipios(base)
            except Exception as e:
                self._log(f"ERRO ao carregar as planilhas: {e}")
                return

            def _finalizar():
                self.base = base
                for m in municipios:
                    self.lista_municipios.insert("end", m)
                self.botao_gerar.config(state="normal")
                self._log(f"Pronto. {len(municipios)} municípios encontrados nas planilhas.")

            self.after(0, _finalizar)

        threading.Thread(target=_tarefa, daemon=True).start()


    def _gerar_clicado(self):
        selecionados = [self.lista_municipios.get(i) for i in self.lista_municipios.curselection()]
        if not selecionados:
            messagebox.showinfo("Gerador de Entregas", "Escolha ao menos um município na lista.")
            return

        self.botao_gerar.config(state="disabled")

        def _tarefa():
            os.makedirs(config.PASTA_SAIDA, exist_ok=True)
            for municipio in selecionados:
                try:
                    dados_mun = dados.filtrar_municipio(self.base, municipio)
                    _painel, painel_final = dados.montar_painel(dados_mun)
                    blocos = relatorio.montar_dados_entregas(
                        self.base, dados_mun, config.ORDEM_PROGRAMAS, config.PROGRAMAS_EXCLUIR,
                        nome_programa_pro_estrada=config.NOME_PROGRAMA_PRO_ESTRADA,
                        ano_destaque_pro_estrada=config.ANO_DESTAQUE_PRO_ESTRADA,
                        nome_exibicao_alagoas_ponta_a_ponta=config.NOME_EXIBICAO_ALAGOAS_PONTA_A_PONTA,
                        texto_total_pro_estrada=config.TEXTO_TOTAL_PRO_ESTRADA,
                    )
                    caminho_docx = relatorio.gerar_docx(municipio, blocos, config.PASTA_SAIDA)
                    caminho_xlsx = excel_export.salvar_excel(municipio, dados_mun, painel_final, config.PASTA_SAIDA)
                    self._log(f"✔ {municipio}")
                    self._log(f"   Word:  {caminho_docx}")
                    self._log(f"   Excel: {caminho_xlsx}")
                except Exception as e:
                    self._log(f"✘ {municipio} — falhou: {e}")

            self.after(0, lambda: self.botao_gerar.config(state="normal"))

        threading.Thread(target=_tarefa, daemon=True).start()


    def _abrir_pasta(self):
        caminho = os.path.abspath(config.PASTA_SAIDA)
        try:
            if sys.platform.startswith("win"):
                os.startfile(caminho)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", caminho], check=False)
            else:
                subprocess.run(["xdg-open", caminho], check=False)
        except Exception as e:
            messagebox.showerror("Gerador de Entregas", f"Não consegui abrir a pasta:\n{caminho}\n\n{e}")


if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception:
        import traceback
        erro_completo = traceback.format_exc()

        try:
            messagebox.showerror(
                "Gerador de Entregas - Erro",
                "O programa encontrou um erro ao iniciar.\n\n"
                "Foi gravado um arquivo 'erro.log' na mesma pasta do programa "
                "com os detalhes."
            )
        except Exception:
            pass

        try:
            pasta = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
                else os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(pasta, "erro.log"), "w", encoding="utf-8") as f:
                f.write(erro_completo)
        except Exception:
            pass
