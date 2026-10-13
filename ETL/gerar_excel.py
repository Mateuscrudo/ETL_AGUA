import os
import pandas as pd


def gerar_excel(
    df,
    fotos=None,
    pasta_saida="SAIDA"
):
    """
    Gera o Excel consolidado com duas abas:

    BASE_AGUA -> base principal consolidada
    FOTOS     -> todos os links de fotos
    """

    os.makedirs(pasta_saida, exist_ok=True)

    caminho_excel = os.path.join(
        pasta_saida,
        "base_agua_consolidada.xlsx"
    )

    with pd.ExcelWriter(
        caminho_excel,
        engine="openpyxl"
    ) as writer:

        # =====================================================
        # ABA PRINCIPAL
        # =====================================================

        df.to_excel(
            writer,
            sheet_name="BASE_AGUA",
            index=False
        )

        # =====================================================
        # ABA FOTOS
        # =====================================================

        if fotos is not None:

            fotos.to_excel(
                writer,
                sheet_name="FOTOS",
                index=False
            )

        else:

            # Cria a aba mesmo quando não houver fotos
            pd.DataFrame(
                columns=[
                    "Matrícula",
                    "Foto",
                    "Origem",
                    "Tipo",
                    "Data do Registro",
                    "URL"
                ]
            ).to_excel(
                writer,
                sheet_name="FOTOS",
                index=False
            )

    return caminho_excel