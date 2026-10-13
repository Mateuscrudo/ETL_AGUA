"""Cria BASE_AG e EXPORTACAO inteiramente sintéticos."""
from pathlib import Path
import pandas as pd
from openpyxl import load_workbook

def gerar_demo():
    root=Path(__file__).resolve().parent/'ENTRADA';root.mkdir(parents=True,exist_ok=True)
    paths=[root/'BASE_AG_FICTICIA.xlsx',root/'EXPORTACAO_FICTICIA.xlsx']
    if any(p.exists() for p in paths): raise FileExistsError('Amostras já existem.')
    p=pd.DataFrame([
        ['DEM1001','01/10/2026',2,'Rua Fictícia A, 10','Bairro Exemplo','Adesão executada','Pessoa Fictícia A','00000000000','Equipe Fictícia A','Galeria'],
        ['DEM1002','02/10/2026',1,'Rua Fictícia B, 20','Bairro Exemplo','Cancelado','Pessoa Fictícia B','00000000000','Equipe Fictícia B',None],
    ],columns=['Matrícula','Data Adesão','Qtd. Tentat.','Endereço','Comunidade','Status Adesão','Nome Cliente','Telefone','Equipe Exec.','Fotos'])
    a=pd.DataFrame([
        ['DEM1001','03/10/2026','Adesão executada','Rua Fictícia A, 11','Bairro Exemplo','Pessoa Fictícia A','00000000000','Agente Fictício A','Conferido','https://example.invalid/agua1.png','https://example.invalid/registro1','REG-DEMO-1'],
        ['DEM1003','04/10/2026','Não visitado','Rua Fictícia C, 30','Bairro Exemplo','Pessoa Fictícia C','00000000000','Agente Fictício C','Pendente','https://example.invalid/agua3.png',None,'REG-DEMO-3'],
        ['DEM1003','05/10/2026','Adesão executada','Rua Fictícia C, 31','Bairro Exemplo','Pessoa Fictícia C','00000000000','Agente Fictício C','Conferido','https://example.invalid/agua3.png',None,'REG-DEMO-4'],
    ],columns=['Matricula','Data do registro','Situação Campo','Endereço ','Bairro','Nome Cliente','Telefone','Nome do agente ','Situação Backoffice','Foto demo','Link Backoffice','Code Deep'])
    p.to_excel(paths[0],index=False)
    wb=load_workbook(paths[0]);wb.active['J2'].hyperlink='https://example.invalid/galeria_agua1';wb.save(paths[0]);wb.close()
    a.to_excel(paths[1],index=False)
    print('Entradas fictícias de Água criadas.')

if __name__=='__main__': gerar_demo()
