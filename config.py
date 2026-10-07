# config.py

import configparser
import os
import sys


def _pasta_do_programa():
    """Pasta onde o programa 'mora' de verdade: a pasta do .exe, se já
    estiver compilado (PyInstaller), ou a pasta destes scripts .py,
    se estiver rodando direto em Python."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


PASTA_PROGRAMA = _pasta_do_programa()
CAMINHO_CONFIG_INI = os.path.join(PASTA_PROGRAMA, "config.ini")

_PADRAO_ARQUIVO_MCL = (
    r"\\ctcppt\E\OneDrive\Servidor SETRAND\18 ACOMPANHAMENTO DE OBRAS"
    r"\MINHA CIDADE LINDA, PONTA A PONTA E PRÓ ESTRADA\MCL E PAP.xlsx"
)
_PADRAO_ARQUIVO_PRO_ESTRADA = (
    r"\\ctcppt\E\OneDrive\Servidor SETRAND\18 ACOMPANHAMENTO DE OBRAS"
    r"\MINHA CIDADE LINDA, PONTA A PONTA E PRÓ ESTRADA\PRÓ ESTRADA - ATUAL.xlsx"
)


def _criar_config_ini_padrao():
    cp = configparser.ConfigParser()
    cp["caminhos"] = {
        "arquivo_mcl": _PADRAO_ARQUIVO_MCL,
        "arquivo_pro_estrada": _PADRAO_ARQUIVO_PRO_ESTRADA,
        "pasta_saida": ".",
    }
    try:
        with open(CAMINHO_CONFIG_INI, "w", encoding="utf-8") as f:
            f.write(
                "; Arquivo de configuracao do Gerador de Entregas.\n"
                "; Pode editar com o Bloco de Notas. Depois de salvar, feche e\n"
                "; abra o programa de novo para valer.\n"
                "; \"pasta_saida = .\" significa \"a mesma pasta onde esta este arquivo\".\n\n"
            )
            cp.write(f)
    except OSError as e:
        print(f"Aviso: não consegui criar '{CAMINHO_CONFIG_INI}' ({e}). Usando valores padrão.")
    return cp


def _carregar_config_ini():
    cp = configparser.ConfigParser()
    if not os.path.exists(CAMINHO_CONFIG_INI):
        return _criar_config_ini_padrao()
    try:
        cp.read(CAMINHO_CONFIG_INI, encoding="utf-8")
    except OSError as e:
        print(f"Aviso: não consegui ler '{CAMINHO_CONFIG_INI}' ({e}). Usando valores padrão.")
    return cp


_cp = _carregar_config_ini()

ARQUIVO_MCL = _cp.get("caminhos", "arquivo_mcl", fallback=_PADRAO_ARQUIVO_MCL)
ARQUIVO_PRO_ESTRADA = _cp.get("caminhos", "arquivo_pro_estrada", fallback=_PADRAO_ARQUIVO_PRO_ESTRADA)

_pasta_saida_bruta = _cp.get("caminhos", "pasta_saida", fallback=".")
if os.path.isabs(_pasta_saida_bruta):
    PASTA_SAIDA = _pasta_saida_bruta
else:

    PASTA_SAIDA = os.path.normpath(os.path.join(PASTA_PROGRAMA, _pasta_saida_bruta))



ABA_PRO_ESTRADA = "Resumo Consolidado"
NOME_PROGRAMA_PRO_ESTRADA = "Pró-Estrada"
ABA_IMPLANTACAO_ASFALTICA = "Implantação Asfáltica"


ABA_RESUMO_SEMANAL_MCL = "RES. SEMANAL MCL"


ABA_PARALELEPIPEDO_MCL = "Implantação em Paralelepípedo"


ABAS_MCL_IGNORAR = [
    "PLANILHA GERAL",
    "CONVÊNIOS",
    "MCL 03",
    "CONFERÊNCIA CONTRATOS",
    "RES. OBRAS DIVERSAS",
    "URBANIZAÇÃO",
    "PLANILHA RESUMO",
    "RESUMO MCL3",
    "RESUMO",
    "RES. SEMANAL ASF",
    "Curva de Crescimento",
    "RECAPEAMENTO",
]


ORDEM_PROGRAMAS = None


NOME_EXIBICAO_ALAGOAS_PONTA_A_PONTA = "Implementações - Alagoas de Ponta a Ponta."


NOME_EXIBICAO_MCL_SEM_ETAPA = "Implementação de Paralelepípedo"


ANO_DESTAQUE_PRO_ESTRADA = "2026"


TEXTO_TOTAL_PRO_ESTRADA = "Total acumulado do programa Pró-Estrada"


PROGRAMAS_EXCLUIR = ["RESUMO MCL3"]
