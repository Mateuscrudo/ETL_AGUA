"""Configuração independente desta cópia; não referencia o app interno."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent
ETLS = {'agua': {
    'entrada': ROOT / 'ENTRADA',
    'saida': ROOT / 'SAIDA_AGUA',
    'sqlite': ROOT / 'SAIDA_AGUA' / 'base_agua.db',
}}
