"""Adaptadores independientes y puertos SAP para ME12 y VK12."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Union

from services.sap_errors import SapBusinessError, SapNavigationError, SapSessionUnavailableError


@dataclass
class RowResult:
    row: int
    success: bool
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransactionResult:
    processed: int
    successful: int
    failed: int
    rows: List[RowResult]
    message: str

    def as_dict(self) -> Dict[str, Any]:
        return {"processed": self.processed, "successful": self.successful, "failed": self.failed,
                "rows": [r.__dict__ for r in self.rows], "message": self.message}


class TransactionPort(Protocol):
    """Puerto para navegación, mensajes y confirmación de un flujo SAP."""

    def navigate(self, session: Any, row: Dict[str, Any]) -> None: ...
    def read_messages(self, session: Any) -> List[Any]: ...
    def confirm_result(self, session: Any) -> bool: ...


class Me12SapPort:
    """Puerto de scripting específico de ME12."""

    def navigate(self, session: Any, row: Dict[str, Any]) -> None:
        if hasattr(session, "execute_transaction"):
            session.execute_transaction("ME12", row)
            return
        session.start_transaction("ME12")
        if hasattr(session, "set_fields"):
            session.set_fields(row)
        else:
            for key, value in row.items():
                session.set_field(key, value)
        if hasattr(session, "submit"):
            session.submit()
        else:
            session.press("ENTER")
        if hasattr(session, "save"):
            session.save()

    def read_messages(self, session: Any) -> List[Any]:
        return list(session.get_messages()) if hasattr(session, "get_messages") else []

    def confirm_result(self, session: Any) -> bool:
        return bool(session.read_row_result()) if hasattr(session, "read_row_result") else True


class Vk12SapPort:
    """Puerto de scripting específico de VK12."""

    def navigate(self, session: Any, row: Dict[str, Any]) -> None:
        if hasattr(session, "execute_transaction"):
            session.execute_transaction("VK12", row)
            return
        session.start_transaction("VK12")
        if hasattr(session, "set_fields"):
            session.set_fields(row)
        else:
            for key, value in row.items():
                session.set_field(key, value)
        if hasattr(session, "submit"):
            session.submit()
        else:
            session.press("ENTER")
        if hasattr(session, "save"):
            session.save()

    def read_messages(self, session: Any) -> List[Any]:
        return list(session.get_messages()) if hasattr(session, "get_messages") else []

    def confirm_result(self, session: Any) -> bool:
        return bool(session.read_row_result()) if hasattr(session, "read_row_result") else True


class _Adapter:
    transaction = ""

    def __init__(self, action: Optional[Callable[[Any, Dict[str, Any]], Union[Awaitable[Any], Any]]],
                 port: TransactionPort) -> None:
        self._action = action
        self._port = port

    async def _run_rows(self, session: Any, rows: Sequence[Mapping[str, Any]]) -> TransactionResult:
        if session is None:
            raise SapSessionUnavailableError()
        results: List[RowResult] = []
        for index, row in enumerate(rows, start=2):
            try:
                mapped = self.map_row(row)
                if self._action:
                    value = self._action(session, mapped)
                    if hasattr(value, "__await__"):
                        await value
                else:
                    self._port.navigate(session, mapped)
                    for message in self._port.read_messages(session):
                        message_type = getattr(message, "type", None) or (
                            message.get("type") if isinstance(message, dict) else ""
                        )
                        if str(message_type).upper() in {"E", "A", "X"}:
                            raise SapBusinessError("SAP rechazó la fila")
                    if not self._port.confirm_result(session):
                        raise SapBusinessError("SAP no confirmó la fila")
                results.append(RowResult(index, True, "OK", mapped))
            except SapBusinessError as exc:
                results.append(RowResult(index, False, exc.public_message))
            except SapNavigationError:
                raise
            except Exception as exc:
                raise SapNavigationError() from exc
        successful = sum(result.success for result in results)
        return TransactionResult(len(results), successful, len(results) - successful, results,
                                 f"{self.transaction} ejecutado exitosamente")

    def map_row(self, row: Mapping[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class Me12Adapter(_Adapter):
    """Traduce exclusivamente filas del template de costos a ME12."""

    transaction = "ME12"

    def __init__(self, action: Optional[Callable[[Any, Dict[str, Any]], Union[Awaitable[Any], Any]]] = None,
                 port: Optional[TransactionPort] = None) -> None:
        super().__init__(action, port or Me12SapPort())

    def map_row(self, row: Mapping[str, Any]) -> Dict[str, Any]:
        if str(row.get("Org_Compras", "")) != "1000":
            raise SapBusinessError("EKORG inválida")
        return {"MATNR": row.get("Material"), "LIFNR": row.get("Proveedor"), "EKORG": "1000",
                "INFNR_TYPE": row.get("Tipo_Info"), "KSCHL": row.get("Tipo_Condicion"),
                "PRICE": row.get("Nuevo_Precio"), "WAERS": row.get("Moneda"),
                "PRICE_UNIT": row.get("Unidad_Precio"), "MEINS": row.get("Unidad_Medida"),
                "VALID_FROM": row.get("Valido_Desde"), "VALID_TO": row.get("Valido_Hasta")}

    async def execute(self, session: Any, rows: Sequence[Mapping[str, Any]]) -> TransactionResult:
        return await self._run_rows(session, rows)


class Vk12Adapter(_Adapter):
    """Traduce exclusivamente filas del template de condiciones a VK12."""

    transaction = "VK12"

    def __init__(self, action: Optional[Callable[[Any, Dict[str, Any]], Union[Awaitable[Any], Any]]] = None,
                 port: Optional[TransactionPort] = None) -> None:
        super().__init__(action, port or Vk12SapPort())

    def map_row(self, row: Mapping[str, Any]) -> Dict[str, Any]:
        return {"MATNR": row.get("MATERIAL"), "MEINS": row.get("UNIDAD_DE_MEDIDA"),
                "KBETR": row.get("IMPORTE"), "MATKL": row.get("GRUPO_ARTICULO"),
                "VKORG": "1000", "VTWEG": row.get("CAN_DISTR"), "SPART": row.get("SECTOR"),
                "BRACO": row.get("RAMO"), "FLOW": row.get("TIPO_MODIFICACION")}

    async def execute(self, session: Any, rows: Sequence[Mapping[str, Any]]) -> TransactionResult:
        return await self._run_rows(session, rows)


TRANSACTION_ADAPTERS = {"ME12": Me12Adapter, "VK12": Vk12Adapter}


def select_adapter(transaction: str, **kwargs: Any) -> _Adapter:
    """Selecciona explícitamente una transacción registrada."""
    try:
        return TRANSACTION_ADAPTERS[transaction.upper()](**kwargs)
    except KeyError as exc:
        raise ValueError(f"Transacción no soportada: {transaction}") from exc
