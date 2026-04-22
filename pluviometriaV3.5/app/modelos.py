from dataclasses import dataclass
from typing import Optional


@dataclass
class Medicao:
    """Representa uma medição consolidada antes da persistência no banco local."""

    data_hora: str
    pulsos: int
    chuva_intervalo_mm: float
    chuva_acumulada_mm: float


@dataclass
class MedicaoPersistida:
    """Representa uma medição já persistida no SQLite local."""

    id: int
    data_hora: str
    pulsos: int
    chuva_intervalo_mm: float
    chuva_acumulada_mm: float
    status_sync: str
    tentativas_envio: int
    criado_em: str
    enviado_em: Optional[str]
    ultimo_erro: Optional[str]