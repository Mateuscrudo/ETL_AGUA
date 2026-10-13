from pathlib import Path
from datetime import datetime
import pandas as pd 
import os

from config_central import ETLS
from ETL.ler_bases import ler_bases
from ETL.consolidar import consolidar
from ETL.gerar_excel import gerar_excel
from ETL.gerar_sql import gerar_sql
# =========================================================
# CONFIGURAÇÃO DO LOG
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

PASTA_SAIDA = ETLS["agua"]["saida"]

PASTA_SAIDA.mkdir(
    parents=True,
    exist_ok=True
)

data_execucao = datetime.now().strftime("%Y-%m-%d")

ARQUIVO_LOG = (
    PASTA_SAIDA /
    f"etl_agua_{data_execucao}.log"
)


# =========================================================
# FUNÇÃO DE LOG
# =========================================================

def log(mensagem=""):
    print(mensagem)

    with open(
        ARQUIVO_LOG,
        "a",
        encoding="utf-8"
    ) as arquivo:
        arquivo.write(mensagem + "\n")


# =========================================================
# MAIN
# =========================================================

def main():

    inicio = datetime.now()

    try:

        log("=" * 60)
        log("=== ETL ÁGUA ===")
        log("=" * 60)

        log(
            f"🕒 Início: "
            f"{inicio.strftime('%d/%m/%Y %H:%M:%S')}"
        )

        # =================================================
        # 1. LER BASES
        # =================================================

        (
            base_principal,
            base_atualizada,
            base_principal_path,
            base_atualizada_path
        ) = ler_bases()

        log("")
        log(
            f"📘 Base principal: "
            f"{base_principal_path.name}"
        )

        log(
            f"📗 Base atualizada: "
            f"{base_atualizada_path.name}"
        )

        log("")
        log(
            f"📊 Registros Base Principal: "
            f"{len(base_principal):,}".replace(",", ".")
        )

        log(
            f"📊 Registros Base Atualizada: "
            f"{len(base_atualizada):,}".replace(",", ".")
        )
        log(
            f"📈 Métricas de entrada | "
            f"principal={len(base_principal):,} | "
            f"atualizada={len(base_atualizada):,}"
        )

        # =================================================
        # 2. CONSOLIDAÇÃO
        # =================================================

        log("")
        log("🔄 Consolidando bases...")


        resultado, fotos = consolidar(
            base_principal,
            base_atualizada,
            caminho_base_fotos=base_principal_path
        )


        if os.environ.get("EXECUCAO_AGENTE") != "1":
            input("\nPressione ENTER para encerrar...")

        # =================================================
        # GERAÇÃO DO EXCEL
        # =================================================

        caminho_excel = gerar_excel(
            resultado,
            fotos=fotos,
            pasta_saida=str(PASTA_SAIDA)
        )

        # =================================================
        # GERAÇÃO DO SQL
        # =================================================

        caminho_sql = gerar_sql(
            resultado,
            fotos=fotos
        )

        log(f"🗄️ Banco SQL gerado:{caminho_sql}")

        log(f"📊 Excel gerado: {caminho_excel}")

        # =================================================
        # AUDITORIA DAS MATRÍCULAS PRESENTES NAS DUAS BASES
        # =================================================

        log("")
        log("=" * 60)
        log("=== AUDITORIA ===")
        log("=" * 60)

        # Normaliza as matrículas apenas para comparação
        matriculas_principal = set(
            base_principal["Matrícula"]
            .dropna()
            .map(lambda v: "" if pd.isna(v) else str(v).strip())
            .tolist()
        )

        matriculas_atualizada = set(
            base_atualizada["Matricula"]
            .dropna()
            .map(lambda v: "" if pd.isna(v) else str(v).strip())
            .tolist()
        )

        matriculas_ambas = sorted(
            matriculas_principal &
            matriculas_atualizada
        )

        log(
            f"🔄 Matrículas presentes nas duas bases: "
            f"{len(matriculas_ambas)}"
        )

        # -------------------------------------------------
        # DETALHAMENTO
        # -------------------------------------------------

        for matricula in matriculas_ambas:

            registros_principal = base_principal[
                base_principal["Matrícula"]
                .map(lambda v: "" if pd.isna(v) else str(v).strip())
                == matricula
            ]

            registros_atualizada = base_atualizada[
                base_atualizada["Matricula"]
                .map(lambda v: "" if pd.isna(v) else str(v).strip())
                == matricula
            ]

            # Data da BASE_AG
            datas_principal = pd.to_datetime(
                registros_principal["Data Adesão"],
                errors="coerce",
                dayfirst=True
            )

            # Data do APPDEEP
            datas_atualizada = pd.to_datetime(
                registros_atualizada["Data do registro"],
                errors="coerce",
                dayfirst=True
            )

            data_principal = (
                datas_principal.max()
                if not datas_principal.dropna().empty
                else None
            )

            data_atualizada = (
                datas_atualizada.max()
                if not datas_atualizada.dropna().empty
                else None
            )

            log("")
            log(f"Matrícula: {matricula}")

            log(
                "   BASE_AG: "
                f"{data_principal}"
            )

            log(
                "   APPDEEP:   "
                f"{data_atualizada}"
            )
        # =================================================
        # AUDITORIA DE DUPLICIDADES INTERNAS
        # =================================================

        log("")
        log("=" * 60)
        log("=== DUPLICIDADES INTERNAS ===")
        log("=" * 60)

        # -------------------------------------------------
        # BASE AGUA
        # -------------------------------------------------

        principal_matricula = (
            base_principal["Matrícula"]
            .dropna()
            .map(lambda valor: str(valor).strip())
        )

        duplicadas_principal = (
            principal_matricula[
                principal_matricula.duplicated(
                    keep=False
                )
            ]
        )

        duplicadas_principal_unicas = sorted(
            duplicadas_principal.unique() # type: ignore
        )

        log("")
        log(
            f"📘 Matrículas duplicadas na BASE_AG: "
            f"{len(duplicadas_principal_unicas)}"
        )

        if duplicadas_principal_unicas:

            for matricula in duplicadas_principal_unicas:

                quantidade = (
                    duplicadas_principal
                    == matricula
                ).sum()

                log(
                    f"   - {matricula}: "
                    f"{quantidade} registros"
                )

        # -------------------------------------------------
        # APPDEEP
        # -------------------------------------------------

        atualizada_matricula = (
            base_atualizada["Matricula"]
            .dropna()
            .astype(str)
            .str.strip() # type: ignore
        )

        duplicadas_atualizada = (
            atualizada_matricula[
                atualizada_matricula.duplicated(
                    keep=False
                )
            ]
        )

        duplicadas_atualizada_unicas = sorted(
            duplicadas_atualizada.unique()
        )

        log("")
        log(
            f"📗 Matrículas duplicadas no APPDEEP: "
            f"{len(duplicadas_atualizada_unicas)}"
        )

        if duplicadas_atualizada_unicas:

            for matricula in duplicadas_atualizada_unicas:

                quantidade = (
                    duplicadas_atualizada
                    == matricula
                ).sum()

                log(
                    f"   - {matricula}: "
                    f"{quantidade} registros"
                )
        # =================================================
        # 3. RESULTADO
        # =================================================

        log("")
        log("=" * 60)
        log("=== RESULTADO ===")
        log("=" * 60)

        log(
            f"📊 Matrículas consolidadas: "
            f"{len(resultado):,}".replace(",", ".")
        )

        # =================================================
        # 4. ORIGEM DOS DADOS
        # =================================================

        if "Origem dos Dados" in resultado.columns:

            log("")
            log("📌 Origem dos dados:")

            origem = (
                resultado["Origem dos Dados"]
                .value_counts(dropna=False)
            )

            for nome, quantidade in origem.items():

                log(
                    f"   - {nome}: "
                    f"{quantidade:,}".replace(",", ".")
                )

        # =================================================
        # 5. FINAL
        # =================================================

        fim = datetime.now()
        duracao = fim - inicio

        log("")
        log("=" * 60)
        log("=== CONSOLIDAÇÃO CONCLUÍDA ===")
        log("=" * 60)

        log(
            f"🕒 Fim: "
            f"{fim.strftime('%d/%m/%Y %H:%M:%S')}"
        )

        log(
            f"⏱️ Tempo de execução: "
            f"{duracao}"
        )

        log(
            f"📄 Log salvo em: "
            f"{ARQUIVO_LOG}"
        )
        log(
            f"STATUS=SUCESSO | registros={len(resultado):,} | "
            f"fotos={len(fotos):,}"
        )

    except Exception as erro:

        fim = datetime.now()
        duracao = fim - inicio

        log("")
        log("=" * 60)
        log("=== ERRO DURANTE O ETL ===")
        log("=" * 60)

        log(
            f"❌ {type(erro).__name__}: {erro}"
        )

        log(
            f"⏱️ Tempo até o erro: "
            f"{duracao}"
        )

        log(
            f"📄 Log salvo em: "
            f"{ARQUIVO_LOG}"
        )

        raise


# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == "__main__":
    main()