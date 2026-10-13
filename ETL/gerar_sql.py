import sqlite3
import pandas as pd
from pathlib import Path
import sys

ROOT_ETLS = Path(__file__).resolve().parents[2]
if str(ROOT_ETLS) not in sys.path:
    sys.path.insert(0, str(ROOT_ETLS))

from config_central import ETLS


def gerar_sql(
    df,
    fotos=None,
    pasta_saida=None
):
    """
    Gera o banco SQLite da base de água.

    Tabelas:
        agua  -> dados consolidados
        fotos -> links das fotos
    """

    # =====================================================
    # 1. CONFIGURAÇÃO
    # =====================================================

    pasta_saida = (
        ETLS["agua"]["saida"]
        if pasta_saida is None
        else Path(pasta_saida)
    )

    pasta_saida.mkdir(
        exist_ok=True
    )

    caminho_db = (
        ETLS["agua"]["sqlite"]
        if pasta_saida == ETLS["agua"]["saida"]
        else Path(pasta_saida) / "base_agua.db"
    )

    # =====================================================
    # 2. CONEXÃO
    # =====================================================

    conexao = sqlite3.connect(
        caminho_db
    )

    try:

        # =================================================
        # 3. PREPARA BASE PRINCIPAL
        # =================================================

        agua = df.copy()

        # SQLite trabalha melhor com nomes simples
        agua = agua.rename(
            columns={
                "Matrícula": "matricula",
                "Endereço": "endereco",
                "Bairro": "bairro",
                "Status Adesão": "status_adesao",
                "Data Adesão": "data_adesao",
                "Situação Backoffice": "situacao_backoffice",
                "Data do Registro": "data_registro",
                "Equipe Exec.": "equipe_exec",
                "Agente": "agente",
                "Latitude": "latitude",
                "Longitude": "longitude",
                "Nome Cliente": "nome_cliente",
                "Telefone": "telefone",
                "Quantidade de Visitas": "quantidade_visitas",
                "Origem dos Dados": "origem_dos_dados"
            }
        )

        # =================================================
        # 4. GRAVA TABELA ÁGUA
        # =================================================

        agua.to_sql(
            "agua",
            conexao,
            if_exists="replace",
            index=False
        )

        # =================================================
        # 5. GRAVA TABELA FOTOS
        # =================================================

        if fotos is not None:

            tabela_fotos = fotos.copy()

            tabela_fotos = tabela_fotos.rename(
                columns={
                    "Matrícula": "matricula",
                    "Foto 1": "foto_1",
                    "Foto 2": "foto_2",
                    "Foto 3": "foto_3",
                    "Foto 4": "foto_4",
                    "Foto 5": "foto_5",
                    "Foto 6": "foto_6",
                    "Foto 7": "foto_7",
                    "Foto 8": "foto_8",
                    "Foto 9": "foto_9",
                    "Foto 10": "foto_10"
                }
            )

            tabela_fotos.to_sql(
                "fotos",
                conexao,
                if_exists="replace",
                index=False
            )

        else:

            pd.DataFrame(
                columns=["matricula"]
            ).to_sql(
                "fotos",
                conexao,
                if_exists="replace",
                index=False
            )

        # =================================================
        # 6. ÍNDICES
        # =================================================

        conexao.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_agua_matricula
            ON agua(matricula)
            """
        )

        conexao.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_fotos_matricula
            ON fotos(matricula)
            """
        )

        conexao.commit()

    finally:

        conexao.close()

    return caminho_db