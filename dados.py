# dados.py


import re
import unicodedata
import pandas as pd


PALAVRAS_CHAVE = {
    "MUNICIPIO": ["MUNICIPIO", "CIDADE"],
    "MUNICIPIO_INICIAL": ["MUNICIPIO INICIAL", "MUNICIPIO DE INICIO", "MUNICIPIO INICIO"],
    "MUNICIPIO_FINAL": ["MUNICIPIO FINAL", "MUNICIPIO DE TERMINO", "MUNICIPIO TERMINO", "MUNICIPIO FIM"],
    "ANO_CONCLUSAO_TXT": ["ANO DE CONCLUSAO", "ANO CONCLUSAO", "ANO"],
    "OBRA": ["OBRA", "OBJETO", "TRECHO"],
    "SITUACAO": ["SITUACAO DA OBRA", "SITUACAO", "STATUS"],
    "VALOR_PREVISTO": ["VALOR PREVISTO", "VALOR TOTAL", "PREVISTO", "CONTRATADO"],
    "VALOR_EXECUTADO": ["VALOR EXECUTADO", "VALOR MEDIDO", "VALOR PAGO", "VALOR INVESTIDO",
                        "INVESTIMENTO", "EXECUTADO", "MEDIDO", "PAGO", "INVESTIDO"],
    "EXT_PREVISTA": ["EXTENSAO PREVISTA", "EXTENSAO PROJETADA", "KM PREVISTO"],
    "EXT_EXECUTADA": ["EXTENSAO EXECUTADA", "EXTENSAO (KM)", "EXTENSAO", "KM EXECUTADO"],
    "QTD_RUAS_EXECUTADAS": ["QUANTIDADE DE RUAS EXECUTADAS", "QUANTIDADE DE VIAS",
                            "QUANTIDADE DE RUAS", "RUAS"],
    "ETAPA_OBRA": ["ETAPA"],
    "DATA_CONCLUSAO": ["DATA DE CONCLUSAO", "CONCLUSAO DA OBRA", "CONCLUSAO"],
    "OBSERVACAO": ["OBSERVACOES", "OBSERVACAO"],
    "URBANIZACAO_CONCLUIDA": ["URBANIZACAO CONCLUIDA", "URBANIZACAO"],
}

OVERRIDES = {}


# FUNÇÕES AUXILIARES

def normalizar(texto):
    """Maiúscula, sem acento, sem espaço duplicado. Usada para comparar
    nomes de forma tolerante a diferenças de digitação."""
    if texto is None:
        return ""
    if isinstance(texto, float) and pd.isna(texto):
        return ""
    texto = str(texto)
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto.upper()


def achar_coluna(nomes, palavras):
    nomes_norm = [normalizar(n) for n in nomes]
    palavras_norm = [normalizar(p) for p in palavras]

    for p in palavras_norm:
        for i, n in enumerate(nomes_norm):
            if n == p:
                return i

    for p in sorted(palavras_norm, key=len, reverse=True):
        for i, n in enumerate(nomes_norm):
            if p and len(n) <= 60 and p in n:
                return i

    return None


def resolver_coluna(aba, campo, nomes, palavras):
    override_nome = OVERRIDES.get(aba, {}).get(campo)
    if override_nome is not None:
        if override_nome in nomes:
            return nomes.index(override_nome)
        print(f"Aviso: override '{override_nome}' para '{campo}' na aba '{aba}' não encontrado.")
    return achar_coluna(nomes, palavras)


def nome_coluna(nomes, idx):
    return "-" if idx is None else str(nomes[idx])


def extrair_coluna(df, idx, tipo="texto"):
    if idx is None:
        return pd.Series([None] * len(df), index=df.index)
    col = df.iloc[:, idx]
    if tipo == "numero":
        return pd.to_numeric(col, errors="coerce")
    return col.apply(lambda x: None if pd.isna(x) else str(x).strip())


def extrair_data(df, idx):
    if idx is None:
        return pd.Series([pd.NaT] * len(df), index=df.index)
    col = df.iloc[:, idx]
    convertida = pd.to_datetime(col, errors="coerce")
    if convertida.notna().sum() == 0:
        numerica = pd.to_numeric(col, errors="coerce")
        if numerica.notna().sum() > 0:
            convertida = pd.to_datetime(numerica, unit="D", origin="1899-12-30", errors="coerce")
    return convertida


def parece_texto_categorico(serie):
    vals = [str(v).strip() for v in serie if v is not None and str(v).strip() != ""]
    if not vals:
        return True
    acertos = sum(1 for v in vals if re.search(r"[A-Za-zÀ-ÿ]", v))
    return (acertos / len(vals)) >= 0.5


def soma_ou_na(serie):
    s = serie.dropna()
    return None if len(s) == 0 else s.sum()


def extrair_ano_texto(serie_bruta):
    def _extrai(v):
        if v is None:
            return None
        v = str(v).strip()
        m = re.search(r"[0-9]{4}", v)
        return m.group(0) if m else (v if v != "" else None)
    return serie_bruta.apply(_extrai)


def _filtrar_com_investimento(df):
    return df[df["VALOR_EXECUTADO"].notna() & (df["VALOR_EXECUTADO"] > 0)].reset_index(drop=True)


def extrair_numero_etapa(serie):
    def _extrai(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        m = re.search(r"[0-9]+", str(v))
        return int(m.group(0)) if m else None
    return serie.apply(_extrai)


# LEITURA 

def processar_aba_mcl(caminho, aba, nome_programa=None):
    nome_programa = nome_programa or aba
    try:
        df = pd.read_excel(caminho, sheet_name=aba)
    except Exception as e:
        print(f"Falha ao ler a aba '{aba}' de '{caminho}': {e}")
        return None

    if df is None or len(df) == 0:
        return None

    nomes = list(df.columns)
    col_mun = resolver_coluna(aba, "MUNICIPIO", nomes, PALAVRAS_CHAVE["MUNICIPIO"])
    if col_mun is None:
        print(f"Aba '{aba}' ignorada: coluna de município não encontrada.")
        return None

    col_obra = resolver_coluna(aba, "OBRA", nomes, PALAVRAS_CHAVE["OBRA"])
    col_situacao = resolver_coluna(aba, "SITUACAO", nomes, PALAVRAS_CHAVE["SITUACAO"])
    col_vprev = resolver_coluna(aba, "VALOR_PREVISTO", nomes, PALAVRAS_CHAVE["VALOR_PREVISTO"])
    col_vexec = resolver_coluna(aba, "VALOR_EXECUTADO", nomes, PALAVRAS_CHAVE["VALOR_EXECUTADO"])
    col_extprev = resolver_coluna(aba, "EXT_PREVISTA", nomes, PALAVRAS_CHAVE["EXT_PREVISTA"])
    col_extexec = resolver_coluna(aba, "EXT_EXECUTADA", nomes, PALAVRAS_CHAVE["EXT_EXECUTADA"])
    col_ruas = resolver_coluna(aba, "QTD_RUAS_EXECUTADAS", nomes, PALAVRAS_CHAVE["QTD_RUAS_EXECUTADAS"])
    col_etapa = resolver_coluna(aba, "ETAPA_OBRA", nomes, PALAVRAS_CHAVE["ETAPA_OBRA"])
    col_data = resolver_coluna(aba, "DATA_CONCLUSAO", nomes, PALAVRAS_CHAVE["DATA_CONCLUSAO"])

    situacao_valores = extrair_coluna(df, col_situacao)
    if col_situacao is not None and not parece_texto_categorico(situacao_valores):
        print(f"Aviso [aba '{aba}']: coluna '{nome_coluna(nomes, col_situacao)}' "
              f"ignorada como SITUAÇÃO por conter números, não texto.")
        situacao_valores = pd.Series([None] * len(df), index=df.index)

    print(f"  [MCL] [{aba}] MUNICIPIO='{nomes[col_mun]}' | OBRA='{nome_coluna(nomes, col_obra)}' | "
          f"SITUACAO='{nome_coluna(nomes, col_situacao)}' | VALOR_EXEC='{nome_coluna(nomes, col_vexec)}' | "
          f"EXT_EXEC='{nome_coluna(nomes, col_extexec)}' | QTD_RUAS='{nome_coluna(nomes, col_ruas)}' | "
          f"ETAPA='{nome_coluna(nomes, col_etapa)}' | DATA='{nome_coluna(nomes, col_data)}'")

    resultado = pd.DataFrame({
        "MUNICIPIO": extrair_coluna(df, col_mun),
        "OBRA": extrair_coluna(df, col_obra),
        "SITUACAO": situacao_valores,
        "VALOR_PREVISTO": extrair_coluna(df, col_vprev, "numero"),
        "VALOR_EXECUTADO": extrair_coluna(df, col_vexec, "numero"),
        "EXT_PREVISTA": extrair_coluna(df, col_extprev, "numero"),
        "EXT_EXECUTADA": extrair_coluna(df, col_extexec, "numero"),
        "QTD_RUAS_EXECUTADAS": extrair_coluna(df, col_ruas, "numero"),
        "ETAPA_OBRA": extrair_coluna(df, col_etapa, "numero"),
        "DATA_CONCLUSAO": extrair_data(df, col_data),
        "ANO_CONCLUSAO_TXT": None,
        "LOTE": None,
        "PROGRAMA": nome_programa,
    })
    resultado = resultado[
        resultado["MUNICIPIO"].notna() & (resultado["MUNICIPIO"].astype(str).str.strip() != "")
    ].reset_index(drop=True)
    resultado = _filtrar_com_investimento(resultado)
    return resultado




def processar_implantacao_asfaltica(caminho, aba, nome_programa=None):
    nome_programa = nome_programa or aba
    try:
        df = pd.read_excel(caminho, sheet_name=aba)
    except Exception as e:
        print(f"Falha ao ler a aba '{aba}' de '{caminho}': {e}")
        return None

    if df is None or len(df) == 0:
        return None

    nomes = list(df.columns)
    col_mun_ini = resolver_coluna(aba, "MUNICIPIO_INICIAL", nomes, PALAVRAS_CHAVE["MUNICIPIO_INICIAL"])
    col_mun_fim = resolver_coluna(aba, "MUNICIPIO_FINAL", nomes, PALAVRAS_CHAVE["MUNICIPIO_FINAL"])

    if col_mun_ini is None or col_mun_fim is None:
        print(f"Aba '{aba}' ignorada: coluna(s) de município inicial/final não encontrada(s).")
        return None

    col_obra = resolver_coluna(aba, "OBRA", nomes, PALAVRAS_CHAVE["OBRA"])
    col_situacao = resolver_coluna(aba, "SITUACAO", nomes, PALAVRAS_CHAVE["SITUACAO"])
    col_vprev = resolver_coluna(aba, "VALOR_PREVISTO", nomes, PALAVRAS_CHAVE["VALOR_PREVISTO"])
    col_vexec = resolver_coluna(aba, "VALOR_EXECUTADO", nomes, PALAVRAS_CHAVE["VALOR_EXECUTADO"])
    col_extprev = resolver_coluna(aba, "EXT_PREVISTA", nomes, PALAVRAS_CHAVE["EXT_PREVISTA"])
    col_extexec = resolver_coluna(aba, "EXT_EXECUTADA", nomes, PALAVRAS_CHAVE["EXT_EXECUTADA"])
    col_ruas = resolver_coluna(aba, "QTD_RUAS_EXECUTADAS", nomes, PALAVRAS_CHAVE["QTD_RUAS_EXECUTADAS"])
    col_etapa = resolver_coluna(aba, "ETAPA_OBRA", nomes, PALAVRAS_CHAVE["ETAPA_OBRA"])
    col_data = resolver_coluna(aba, "DATA_CONCLUSAO", nomes, PALAVRAS_CHAVE["DATA_CONCLUSAO"])

    situacao_valores = extrair_coluna(df, col_situacao)
    if col_situacao is not None and not parece_texto_categorico(situacao_valores):
        print(f"Aviso [aba '{aba}']: coluna '{nome_coluna(nomes, col_situacao)}' "
              f"ignorada como SITUAÇÃO por conter números, não texto.")
        situacao_valores = pd.Series([None] * len(df), index=df.index)

    print(f"  [MCL] [{aba}] MUN_INICIAL='{nomes[col_mun_ini]}' | MUN_FINAL='{nomes[col_mun_fim]}' | "
          f"OBRA='{nome_coluna(nomes, col_obra)}' | SITUACAO='{nome_coluna(nomes, col_situacao)}'")

    base_trecho = pd.DataFrame({
        "MUNICIPIO_INICIAL": extrair_coluna(df, col_mun_ini),
        "MUNICIPIO_FINAL": extrair_coluna(df, col_mun_fim),
        "OBRA": extrair_coluna(df, col_obra),
        "SITUACAO": situacao_valores,
        "VALOR_PREVISTO": extrair_coluna(df, col_vprev, "numero"),
        "VALOR_EXECUTADO": extrair_coluna(df, col_vexec, "numero"),
        "EXT_PREVISTA": extrair_coluna(df, col_extprev, "numero"),
        "EXT_EXECUTADA": extrair_coluna(df, col_extexec, "numero"),
        "QTD_RUAS_EXECUTADAS": extrair_coluna(df, col_ruas, "numero"),
        "ETAPA_OBRA": extrair_coluna(df, col_etapa, "numero"),
        "DATA_CONCLUSAO": extrair_data(df, col_data),
        "ANO_CONCLUSAO_TXT": None,
        "LOTE": None,
        "PROGRAMA": nome_programa,
    })
    base_trecho = base_trecho[
        base_trecho["MUNICIPIO_INICIAL"].notna() &
        (base_trecho["MUNICIPIO_INICIAL"].astype(str).str.strip() != "")
    ].copy()

    base_trecho["_mun_ini_norm"] = base_trecho["MUNICIPIO_INICIAL"].apply(normalizar)
    base_trecho["_mun_fim_norm"] = base_trecho["MUNICIPIO_FINAL"].fillna(
        base_trecho["MUNICIPIO_INICIAL"]
    ).apply(normalizar)

    linhas_iguais = base_trecho[base_trecho["_mun_ini_norm"] == base_trecho["_mun_fim_norm"]].copy()
    linhas_iguais["MUNICIPIO"] = linhas_iguais["MUNICIPIO_INICIAL"]

    linhas_diferentes = base_trecho[base_trecho["_mun_ini_norm"] != base_trecho["_mun_fim_norm"]].copy()
    linhas_diferentes_ini = linhas_diferentes.copy()
    linhas_diferentes_ini["MUNICIPIO"] = linhas_diferentes_ini["MUNICIPIO_INICIAL"]
    linhas_diferentes_fim = linhas_diferentes.copy()
    linhas_diferentes_fim["MUNICIPIO"] = linhas_diferentes_fim["MUNICIPIO_FINAL"]

    resultado = pd.concat([linhas_iguais, linhas_diferentes_ini, linhas_diferentes_fim], ignore_index=True)
    resultado = resultado.drop(columns=["_mun_ini_norm", "_mun_fim_norm", "MUNICIPIO_INICIAL", "MUNICIPIO_FINAL"])
    colunas_ordem = ["MUNICIPIO"] + [c for c in resultado.columns if c != "MUNICIPIO"]
    resultado = resultado[colunas_ordem].reset_index(drop=True)
    resultado = _filtrar_com_investimento(resultado)
    return resultado




def processar_resumo_consolidado(caminho, aba, nome_programa):
    try:
        df = pd.read_excel(caminho, sheet_name=aba)
    except Exception as e:
        print(f"Falha ao ler a aba '{aba}' de '{caminho}': {e}")
        return None

    if df is None or len(df) == 0:
        return None

    nomes = list(df.columns)
    col_mun = resolver_coluna(aba, "MUNICIPIO", nomes, PALAVRAS_CHAVE["MUNICIPIO"])
    col_ano_concl = resolver_coluna(aba, "ANO_CONCLUSAO_TXT", nomes, PALAVRAS_CHAVE["ANO_CONCLUSAO_TXT"])
    col_ext = resolver_coluna(aba, "EXT_EXECUTADA", nomes, PALAVRAS_CHAVE["EXT_EXECUTADA"])
    col_ruas = resolver_coluna(aba, "QTD_RUAS_EXECUTADAS", nomes, PALAVRAS_CHAVE["QTD_RUAS_EXECUTADAS"])
    col_inv = resolver_coluna(aba, "VALOR_EXECUTADO", nomes, PALAVRAS_CHAVE["VALOR_EXECUTADO"])

    if col_mun is None:
        print(f"Aba '{aba}' ignorada: coluna de município não encontrada.")
        return None

    print(f"  [PRO-ESTRADA] [{aba}] MUNICIPIO='{nomes[col_mun]}' | ANO='{nome_coluna(nomes, col_ano_concl)}' | "
          f"EXT_EXEC='{nome_coluna(nomes, col_ext)}' | QTD_RUAS='{nome_coluna(nomes, col_ruas)}' | "
          f"INVESTIMENTO='{nome_coluna(nomes, col_inv)}'")

    ano_bruto = extrair_coluna(df, col_ano_concl)
    ano_valor = extrair_ano_texto(ano_bruto)

    resultado = pd.DataFrame({
        "MUNICIPIO": extrair_coluna(df, col_mun),
        "OBRA": None,
        "SITUACAO": None,
        "VALOR_PREVISTO": None,
        "VALOR_EXECUTADO": extrair_coluna(df, col_inv, "numero"),
        "EXT_PREVISTA": None,
        "EXT_EXECUTADA": extrair_coluna(df, col_ext, "numero"),
        "QTD_RUAS_EXECUTADAS": extrair_coluna(df, col_ruas, "numero"),
        "ETAPA_OBRA": None,
        "DATA_CONCLUSAO": pd.NaT,
        "ANO_CONCLUSAO_TXT": ano_valor,
        "LOTE": None,
        "PROGRAMA": nome_programa,
    })

    resultado = resultado[
        resultado["MUNICIPIO"].notna() &
        (resultado["MUNICIPIO"].astype(str).str.strip() != "") &
        (resultado["MUNICIPIO"].apply(normalizar) != "TOTAL")
    ]
    resultado = _filtrar_com_investimento(resultado.reset_index(drop=True))
    return resultado



def processar_urbanizacao_semanal_mcl(caminho, aba):
    try:
        df = pd.read_excel(caminho, sheet_name=aba, skiprows=1)
    except Exception as e:
        print(f"Falha ao ler a aba '{aba}' de '{caminho}': {e}")
        return None

    if df is None or len(df) == 0:
        return None

    nomes = list(df.columns)
    col_mun = resolver_coluna(aba, "MUNICIPIO", nomes, PALAVRAS_CHAVE["MUNICIPIO"])
    col_urb = resolver_coluna(aba, "URBANIZACAO_CONCLUIDA", nomes, PALAVRAS_CHAVE["URBANIZACAO_CONCLUIDA"])
    col_etapa = resolver_coluna(aba, "ETAPA_OBRA", nomes, PALAVRAS_CHAVE["ETAPA_OBRA"])

    if col_mun is None or col_urb is None:
        faltando = "município" if col_mun is None else "'Urbanização Concluída'"
        print(f"Aba '{aba}' ignorada para Urbanização Concluída: coluna de {faltando} não encontrada "
              f"(confira se o cabeçalho está mesmo na 2ª linha da planilha).")
        return None

    print(f"  [URBANIZACAO] [{aba}] MUNICIPIO='{nomes[col_mun]}' | "
          f"URBANIZACAO_CONCLUIDA='{nomes[col_urb]}' | ETAPA='{nome_coluna(nomes, col_etapa)}'")

    municipio_bruto = extrair_coluna(df, col_mun)
    municipio_preenchido = municipio_bruto.ffill()

    resultado = pd.DataFrame({
        "MUNICIPIO_NORM": municipio_preenchido.apply(normalizar),
        "ETAPA_OBRA": extrair_numero_etapa(extrair_coluna(df, col_etapa)),
        "URBANIZACAO_CONCLUIDA": extrair_coluna(df, col_urb),
    })
    resultado = resultado[resultado["MUNICIPIO_NORM"] != ""].reset_index(drop=True)

    resultado = resultado.drop_duplicates(subset=["MUNICIPIO_NORM", "ETAPA_OBRA"], keep="first")
    return resultado


#monta a base completa 

def _extrair_etapa_do_programa(programa):
    p = normalizar(programa)
    if "MINHA CIDADE LINDA" not in p and "MCL" not in p:
        return None
    m = re.search(r"[0-9]", p)
    return int(m.group(0)) if m else None


def _remapear_etapa_paralelepipedo(df):
    """A aba de Implantação em Paralelepípedo traz as etapas 1 e 2 juntas
    numa coluna 'Etapa' — aqui a gente separa isso em programas
    'Minha Cidade Linda 1ª Etapa' / '2ª Etapa'. Linhas sem etapa
    definida (0 ou em branco) ficam num grupo à parte, para não sumir
    nem se misturar com uma etapa errada."""
    def _nome_programa(etapa):
        if etapa == 1:
            return "Minha Cidade Linda 1ª Etapa"
        if etapa == 2:
            return "Minha Cidade Linda 2ª Etapa"
        return "Minha Cidade Linda (sem etapa definida)"

    df = df.copy()
    df["PROGRAMA"] = df["ETAPA_OBRA"].apply(_nome_programa)
    return df


def carregar_base(config):
    """Lê as duas planilhas inteiras e devolve a base combinada de
    todos os municípios, já com a Urbanização Concluída cruzada nas
    linhas do Minha Cidade Linda. É a parte mais demorada (lê os dois
    arquivos de Excel inteiros) — chame só uma vez e reaproveite o
    resultado."""

    import os
    if not os.path.exists(config.ARQUIVO_MCL):
        raise FileNotFoundError(f"Arquivo não encontrado: '{config.ARQUIVO_MCL}'. Verifique ARQUIVO_MCL em config.py.")

    print(f"Lendo planilha MCL: {config.ARQUIVO_MCL}")
    abas_mcl = pd.ExcelFile(config.ARQUIVO_MCL).sheet_names
    print(f"Arquivo MCL: {len(abas_mcl)} abas encontradas.")
    print("Mapeamento de colunas detectado por aba:")


    aba_urbanizacao_real = next(
        (a for a in abas_mcl if normalizar(a) == normalizar(config.ABA_RESUMO_SEMANAL_MCL)), None
    )
    urbanizacao_semanal = pd.DataFrame(columns=["MUNICIPIO_NORM", "ETAPA_OBRA", "URBANIZACAO_CONCLUIDA"])
    if aba_urbanizacao_real is None:
        print(f"Aviso: aba '{config.ABA_RESUMO_SEMANAL_MCL}' não encontrada. "
              f"A coluna Urbanização Concluída ficará vazia.")
    else:
        resultado_urb = processar_urbanizacao_semanal_mcl(config.ARQUIVO_MCL, aba_urbanizacao_real)
        if resultado_urb is not None:
            urbanizacao_semanal = resultado_urb

    abas_ignorar_norm = {normalizar(a) for a in config.ABAS_MCL_IGNORAR}

    partes_mcl = []
    for aba in abas_mcl:
        if normalizar(aba) in abas_ignorar_norm:
            continue  
        if normalizar(aba) == normalizar(config.ABA_IMPLANTACAO_ASFALTICA):
            r = processar_implantacao_asfaltica(config.ARQUIVO_MCL, aba)
        elif normalizar(aba) == normalizar(config.ABA_RESUMO_SEMANAL_MCL):
            r = None 
        elif normalizar(aba) == normalizar(config.ABA_PARALELEPIPEDO_MCL):
            r = processar_aba_mcl(config.ARQUIVO_MCL, aba)
            if r is not None and len(r) > 0:
                r = _remapear_etapa_paralelepipedo(r)
        else:
            r = processar_aba_mcl(config.ARQUIVO_MCL, aba)
        if r is not None and len(r) > 0:
            partes_mcl.append(r)

    base_mcl = pd.concat(partes_mcl, ignore_index=True) if partes_mcl else pd.DataFrame()

    base_pro_estrada = pd.DataFrame()
    if not os.path.exists(config.ARQUIVO_PRO_ESTRADA):
        print(f"Aviso: arquivo Pró-Estrada não encontrado: '{config.ARQUIVO_PRO_ESTRADA}'. "
              f"Seguindo apenas com os dados do MCL.")
    else:
        print(f"Lendo planilha Pró-Estrada: {config.ARQUIVO_PRO_ESTRADA}")
        abas_pe = pd.ExcelFile(config.ARQUIVO_PRO_ESTRADA).sheet_names
        if config.ABA_PRO_ESTRADA not in abas_pe:
            print(f"Aviso: aba '{config.ABA_PRO_ESTRADA}' não encontrada em '{config.ARQUIVO_PRO_ESTRADA}'. "
                  f"Abas disponíveis: {', '.join(abas_pe)}.")
        else:
            r = processar_resumo_consolidado(config.ARQUIVO_PRO_ESTRADA, config.ABA_PRO_ESTRADA,
                                              config.NOME_PROGRAMA_PRO_ESTRADA)
            if r is not None:
                base_pro_estrada = r

    base = pd.concat([base_mcl, base_pro_estrada], ignore_index=True)
    if len(base) == 0:
        raise ValueError("Nenhuma linha válida foi extraída de nenhum dos dois arquivos. "
                          "Verifique os caminhos e nomes de aba/coluna.")

    base["MUNICIPIO_NORM"] = base["MUNICIPIO"].apply(normalizar)


    base["_ETAPA_PROGRAMA"] = base["PROGRAMA"].apply(_extrair_etapa_do_programa)

    if len(urbanizacao_semanal) == 0:
        base["URBANIZACAO_CONCLUIDA"] = None
    elif urbanizacao_semanal["ETAPA_OBRA"].notna().any():

        urbanizacao_com_etapa = urbanizacao_semanal[urbanizacao_semanal["ETAPA_OBRA"].notna()]
        base = base.merge(
            urbanizacao_com_etapa,
            left_on=["MUNICIPIO_NORM", "_ETAPA_PROGRAMA"],
            right_on=["MUNICIPIO_NORM", "ETAPA_OBRA"],
            how="left",
            suffixes=("", "_urb"),
        )
        if "ETAPA_OBRA_urb" in base.columns:
            base = base.drop(columns=["ETAPA_OBRA_urb"])
    else:
        base = base.merge(
            urbanizacao_semanal[["MUNICIPIO_NORM", "URBANIZACAO_CONCLUIDA"]],
            on="MUNICIPIO_NORM",
            how="left",
        )
        base.loc[base["_ETAPA_PROGRAMA"].isna(), "URBANIZACAO_CONCLUIDA"] = None

    base = base.drop(columns=["_ETAPA_PROGRAMA"])
    return base


def listar_municipios(base):
    return sorted(base["MUNICIPIO"].dropna().unique().tolist())


def filtrar_municipio(base, municipio):
    """A partir da base completa, devolve só as linhas do município
    pedido, já com o ANO_CONCLUSAO calculado (data de conclusão na
    maioria dos programas; no Pró-Estrada, vem direto da coluna ANO)."""

    municipio = (municipio or "").strip()
    if municipio == "":
        raise ValueError("Informe um nome de município válido.")

    alvo_norm = normalizar(municipio)
    dados_mun = base[base["MUNICIPIO_NORM"] == alvo_norm].copy()

    if len(dados_mun) == 0:
        disponiveis = listar_municipios(base)
        prefixo = alvo_norm[:4]
        sugestoes = [m for m in disponiveis if prefixo in normalizar(m)] if prefixo else []
        msg = f"Nenhum registro encontrado para '{municipio}'."
        if sugestoes:
            msg += f" Municípios parecidos: {', '.join(sugestoes)}"
        raise ValueError(msg)

    dados_mun = dados_mun.drop(columns=["MUNICIPIO_NORM"]).reset_index(drop=True)

    def _ano_final(row):
        if row["ANO_CONCLUSAO_TXT"]:
            return row["ANO_CONCLUSAO_TXT"]
        if pd.notna(row["DATA_CONCLUSAO"]):
            return str(row["DATA_CONCLUSAO"].year)
        return None

    dados_mun["ANO_CONCLUSAO"] = dados_mun.apply(_ano_final, axis=1)
    dados_mun = dados_mun.drop(columns=["DATA_CONCLUSAO", "ANO_CONCLUSAO_TXT"])

    print(f"Encontrados {len(dados_mun)} registros para '{municipio}'.")
    return dados_mun


def montar_painel(dados_mun):
    """Monta o painel-resumo (uma linha por programa, com totais) igual
    ao que vai para a aba PAINEL_RESUMO do Excel."""

    def _ano_mais_recente(serie):
        anos = [int(v) for v in serie if v is not None and re.fullmatch(r"[0-9]{4}", str(v))]
        return max(anos) if anos else None

    linhas = []
    for programa, grupo in dados_mun.groupby("PROGRAMA", sort=False):
        linhas.append({
            "PROGRAMA": programa,
            "OBRAS": len(grupo),
            "VALOR_PREVISTO": soma_ou_na(grupo["VALOR_PREVISTO"]),
            "VALOR_EXECUTADO": soma_ou_na(grupo["VALOR_EXECUTADO"]),
            "EXT_PREVISTA": soma_ou_na(grupo["EXT_PREVISTA"]),
            "EXT_EXECUTADA": soma_ou_na(grupo["EXT_EXECUTADA"]),
            "QTD_RUAS_EXECUTADAS": soma_ou_na(grupo["QTD_RUAS_EXECUTADAS"]),
            "ANO_CONCLUSAO_MAIS_RECENTE": _ano_mais_recente(grupo["ANO_CONCLUSAO"]),
        })

    painel = pd.DataFrame(linhas).sort_values("VALOR_EXECUTADO", ascending=False, na_position="last")

    total_geral = {
        "PROGRAMA": "TOTAL GERAL",
        "OBRAS": painel["OBRAS"].sum(),
        "VALOR_PREVISTO": soma_ou_na(painel["VALOR_PREVISTO"]),
        "VALOR_EXECUTADO": soma_ou_na(painel["VALOR_EXECUTADO"]),
        "EXT_PREVISTA": soma_ou_na(painel["EXT_PREVISTA"]),
        "EXT_EXECUTADA": soma_ou_na(painel["EXT_EXECUTADA"]),
        "QTD_RUAS_EXECUTADAS": soma_ou_na(painel["QTD_RUAS_EXECUTADAS"]),
        "ANO_CONCLUSAO_MAIS_RECENTE": (
            max([v for v in painel["ANO_CONCLUSAO_MAIS_RECENTE"] if v is not None], default=None)
        ),
    }

    painel_final = pd.concat([painel, pd.DataFrame([total_geral])], ignore_index=True)
    return painel, painel_final
