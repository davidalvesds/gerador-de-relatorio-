# Gerador de Entregas

Aplicativo desktop em Python que gera, para qualquer município, um relatório de **entregas** em Word (`.docx`) e um painel de apoio em Excel (`.xlsx`), a partir das planilhas de acompanhamento de obras da Secretaria de Estado de Transportes e Desenvolvimento Urbano de Alagoas (SETRAND).

Você abre o programa, escolhe um ou vários municípios na lista e clica em **Gerar entrega(s)**. Não é preciso abrir o RStudio, o Excel ou um terminal.

## O que ele faz

- Lê duas planilhas Excel uma responsável pela 'Minha cidade linda' e 'PRÓ ESTRADA'.
- Junta os programas em uma base única por município:
  - Minha Cidade Linda, 1ª e 2ª etapa
  - Alagoas de Ponta a Ponta (Implantação Asfáltica)
  - Outras Obras
  - Pró-Estrada
- Gera, por município:
  - `Entregas - <Município>.docx`: relatório narrativo com as obras, valores, extensões e anos de conclusão.
  - `PAINEL_<MUNICIPIO>.xlsx`: resumo por programa e detalhamento obra a obra.

## Regras do relatório em Word

- Programas sem obras no município não aparecem.
- A situação da obra não é exibida.
- Campos vazios ou zerados (extensão, quantidade de ruas, urbanização) não são exibidos.
- **Implantação Asfáltica** aparece como "Implementações - Alagoas de Ponta a Ponta."
- Obras de Minha Cidade Linda sem etapa definida aparecem como "Implementação de Paralelepípedo".
- **Pró-Estrada** mostra só as obras do ano em destaque, mais uma linha com o total acumulado de todos os anos. O total não é contado duas vezes no investimento do município.
- A última linha traz o **Investimento total no município**.

## Estrutura do projeto

```
.
├── app.py                          # Interface gráfica (tkinter)
├── config.py                       # Configurações e caminhos das planilhas
├── dados.py                        # Leitura e tratamento das planilhas
├── relatorio.py                    # Monta o relatório e gera o Word
├── excel_export.py                 # Gera o painel em Excel
├── Instalar Pacotes.bat            # Instala as dependências (pip)
├── Abrir Gerador de Entregas.bat   # Abre o programa (com Python instalado)
├── Gerar Executavel.bat            # Compila um .exe único (PyInstaller)
├── COMO USAR - Leia-me.txt         # Guia para quem não programa e passo a passo para gerar p .exe
```

### Código

| Arquivo | Função |
|---|---|
| `app.py` | Janela principal: lista de municípios com seleção múltipla, botões "Gerar entrega(s)" e "Abrir pasta das entregas", e um log de andamento. A leitura das planilhas e a geração dos arquivos rodam em threads separadas, então a janela não trava. Se o programa falhar ao abrir, grava um `erro.log` ao lado dele. |
| `config.py` | Caminhos das planilhas e da pasta de saída (lidos do `config.ini`, que é criado na primeira execução). Também guarda as configurações avançadas: abas ignoradas, ordem dos programas, nomes de exibição, ano em destaque do Pró-Estrada e o texto da linha de total acumulado. |
| `dados.py` | Lê as abas de cada programa e padroniza tudo em uma base única. Resolve os problemas das planilhas reais: cabeçalho na 2ª linha, células mescladas, nomes de coluna diferentes entre abas, abas de resumo sem município e valores zerados. Também calcula o painel por programa. |
| `relatorio.py` | Aplica as regras de exibição de cada programa e escreve o `.docx` com `python-docx`. Não precisa de Word nem de Pandoc instalado. |
| `excel_export.py` | Gera o `PAINEL_<MUNICIPIO>.xlsx` com `openpyxl`: aba `PAINEL_RESUMO` (totais por programa) e aba `DETALHAMENTO` (uma linha por obra), com formatação de moeda. |

### Scripts `.bat` (Windows)

| Arquivo | Função |
|---|---|
| `Instalar Pacotes.bat` | Roda `pip install pandas openpyxl python-docx`. Só é necessário uma vez por computador. |
| `Abrir Gerador de Entregas.bat` | Localiza o Python instalado e abre o `app.py`. Funciona também em pastas de rede. |
| `Gerar Executavel.bat` | Usa o PyInstaller para gerar `dist\GeradorDeEntregas.exe`, que roda em qualquer Windows sem instalar nada. |

### Guias em texto

- `COMO USAR - Leia-me.txt`: instalação, uso e solução de problemas para quem não programa. E, também, como compilar o `.exe`.

## Requisitos

- Windows
- Python 3.10 ou superior
- Dependências: `pandas`, `openpyxl`, `python-docx`



## Como usar

### Opção A: com Python instalado

1. Instale o Python e marque **Add python.exe to PATH**.
2. Dê dois cliques em `Instalar Pacotes.bat` (uma vez).
3. Dê dois cliques em `Abrir Gerador de Entregas.bat`.

Ou, pelo terminal:

```bash
python app.py
```

### Opção B: um único `.exe`

1. Em um computador com Python, dê dois cliques em `Gerar Executavel.bat`.
2. Copie `dist\GeradorDeEntregas.exe` para qualquer computador. Não precisa de Python.

Se for rodar o `.bat` pelo prompt, coloque o nome entre aspas, porque ele tem espaço: `"Gerar Executavel.bat"`.

## Configuração

Na primeira execução é criado um `config.ini` ao lado do programa, que pode ser editado no Bloco de Notas:

```ini
[caminhos]
arquivo_mcl = <caminho do arquivo .xlsx>
arquivo_pro_estrada = <caminho do arquivo .xlsx>
pasta_saida = .
```

- `pasta_saida = .` significa a mesma pasta do programa.
- Em `config.py` ficam as configurações avançadas, como `ANO_DESTAQUE_PRO_ESTRADA`, `TEXTO_TOTAL_PRO_ESTRADA`, `ABAS_MCL_IGNORAR` e `ORDEM_PROGRAMAS`.


## Dados

As planilhas de origem **não** fazem parte deste repositório. Os dados são internos e ficam fora do controle de versão.


## Tecnologias

Python · pandas · openpyxl · python-docx · tkinter · PyInstaller
