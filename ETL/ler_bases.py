import pandas as pd
from pathlib import Path

from config_central import ETLS


# =========================================================
# CONFIGURAÇÃO
# =========================================================

ENTRADA = ETLS["agua"]["entrada"]
COLUNAS_BASE_PRINCIPAL = {
    "Matrícula",
    "Data Adesão",
    "Qtd. Tentat.",
    "Endereço",
    "Comunidade",
    "Status Adesão",
}

COLUNAS_BASE_ATUALIZADA = {
    "Matricula",
    "Data do registro",
    "Situação Campo",
    "Endereço ",
    "Bairro",
}


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def localizar_base(palavra):
    """
    Procura na pasta ENTRADA um arquivo Excel
    cujo nome contenha a palavra informada.
    """

    arquivos = [
        p for p in ENTRADA.iterdir()
        if p.is_file()
        and p.suffix.lower() in {".xlsx", ".xlsm", ".xls"}
    ]

    encontrados = [
        p for p in arquivos
        if palavra.upper() in p.stem.upper()
    ]

    if not encontrados:
        raise FileNotFoundError(
            f"Nenhuma base contendo '{palavra}' foi encontrada em:\n"
            f"{ENTRADA}"
        )

    if len(encontrados) > 1:
        nomes = "\n".join(
            f" - {p.name}"
            for p in encontrados
        )

        raise RuntimeError(
            f"Foram encontradas várias bases contendo "
            f"'{palavra}':\n{nomes}"
        )

    return encontrados[0]


# =========================================================
# LEITURA DAS BASES
# =========================================================

def ler_bases():

    # -----------------------------------------------------
    # Localiza arquivos
    # -----------------------------------------------------

    base_principal_path = localizar_base("BASE_AG")
    base_atualizada_path = localizar_base("EXPORTACAO")

    print(
        f"📘 Base principal encontrada: "
        f"{base_principal_path.name}"
    )

    print(
        f"📗 Base atualizada encontrada: "
        f"{base_atualizada_path.name}"
    )

    # -----------------------------------------------------
    # Lê os arquivos
    # -----------------------------------------------------

    base_principal = pd.read_excel(base_principal_path)
    base_atualizada = pd.read_excel(base_atualizada_path)

    faltantes_principal = sorted(
        COLUNAS_BASE_PRINCIPAL - set(base_principal.columns)
    )
    faltantes_atualizada = sorted(
        COLUNAS_BASE_ATUALIZADA - set(base_atualizada.columns)
    )

    if faltantes_principal:
        raise ValueError(
            f"Colunas ausentes na base principal "
            f"'{base_principal_path.name}': {faltantes_principal}"
        )
    if faltantes_atualizada:
        raise ValueError(
            f"Colunas ausentes na base atualizada "
            f"'{base_atualizada_path.name}': {faltantes_atualizada}"
        )

    tentativas = pd.to_numeric(
        base_principal["Qtd. Tentat."],
        errors="coerce",
    )
    valores_invalidos = (
        base_principal["Qtd. Tentat."].notna()
        & tentativas.isna()
    )
    if valores_invalidos.any():
        raise TypeError(
            "A coluna 'Qtd. Tentat.' da base principal contém "
            f"{int(valores_invalidos.sum())} valores não numéricos."
        )

    # -----------------------------------------------------
    # Mostra informações básicas
    # -----------------------------------------------------

    print()
    print(
        f"📊 Registros Base Principal: "
        f"{len(base_principal):,}"
    )

    print(
        f"📊 Registros Base Atualizada: "
        f"{len(base_atualizada):,}"
    )

    print()
    print("📋 Colunas Base Principal:")
    for coluna in base_principal.columns:
        print(f"   - {coluna}")

    print()
    print("📋 Colunas Base Atualizada:")
    for coluna in base_atualizada.columns:
        print(f"   - {coluna}")

    return (
        base_principal,
        base_atualizada,
        base_principal_path,
        base_atualizada_path
    )