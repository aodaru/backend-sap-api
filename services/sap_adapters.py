"""Adaptadores independientes y puertos SAP para ME12 y VK12."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Union

from services.sap_errors import SapBusinessError, SapIntegrationError, SapNavigationError, SapSessionUnavailableError


# ---------------------------------------------------------------------------
# Helpers para navegación COM real de ME12
# ---------------------------------------------------------------------------

_DESDE_IDS = (
    "wnd[0]/usr/ctxtRV13A-DATAB", "wnd[0]/usr/txtRV13A-DATAB",
    "wnd[1]/usr/ctxtRV13A-DATAB", "wnd[1]/usr/txtRV13A-DATAB",
    "wnd[2]/usr/ctxtRV13A-DATAB", "wnd[2]/usr/txtRV13A-DATAB",
    "wnd[0]/usr/ctxtSVALU-LOW", "wnd[0]/usr/txtSVALU-LOW",
    "wnd[1]/usr/ctxtSVALU-LOW", "wnd[1]/usr/txtSVALU-LOW",
    "wnd[2]/usr/ctxtSVALU-LOW", "wnd[2]/usr/txtSVALU-LOW",
)

_HASTA_IDS = (
    "wnd[0]/usr/ctxtRV13A-DATBI", "wnd[0]/usr/txtRV13A-DATBI",
    "wnd[1]/usr/ctxtRV13A-DATBI", "wnd[1]/usr/txtRV13A-DATBI",
    "wnd[2]/usr/ctxtRV13A-DATBI", "wnd[2]/usr/txtRV13A-DATBI",
    "wnd[0]/usr/ctxtSVALU-HIGH", "wnd[0]/usr/txtSVALU-HIGH",
    "wnd[1]/usr/ctxtSVALU-HIGH", "wnd[1]/usr/txtSVALU-HIGH",
    "wnd[2]/usr/ctxtSVALU-HIGH", "wnd[2]/usr/txtSVALU-HIGH",
)


def _wait_for_control(session: Any, control_id: str, timeout: float = 5.0) -> Any:
    """Reintenta ``findById`` hasta que el control exista o se agote *timeout*."""
    start = time.time()
    attempts = 0
    while time.time() - start < timeout:
        try:
            return session.findById(control_id)
        except Exception:
            attempts += 1
            time.sleep(0.2)
    raise TimeoutError(
        f"Control '{control_id}' no encontrado tras {timeout}s ({attempts} intentos)"
    )


def _fill_date_field(session: Any, field_type: str, value: str) -> None:
    """Llena un campo de fecha (``desde``/``hasta``) probando múltiples IDs."""
    ids = _DESDE_IDS if field_type == "desde" else _HASTA_IDS
    for field_id in ids:
        try:
            session.findById(field_id).Text = value
            return
        except Exception:
            pass


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
    """Puerto de scripting ME12 — SAP GUI Scripting COM real.

    Flujo reproduido de ``sap_client.py._procesar_registro`` (líneas 225-466).
    """

    CONDITION_ROW = 2  # 0-based, fila de condición en la tabla SAP

    # -- navegación principal ----------------------------------------------- #

    def navigate(self, session: Any, row: Dict[str, Any]) -> None:
        """Navega ME12: abre, valida, entra a condiciones, modifica precio, guarda."""
        try:
            self._navigate_me12(session, row)
        except (SapNavigationError, SapBusinessError):
            raise
        except Exception as exc:
            raise SapNavigationError() from exc

    def _navigate_me12(self, session: Any, row: Dict[str, Any]) -> None:
        # PASO 1: Abrir ME12
        session.findById("wnd[0]/tbar[0]/okcd").Text = "/nME12"
        session.findById("wnd[0]").SendVKey(0)
        time.sleep(0.5)

        # PASO 2: Proveedor
        session.findById("wnd[0]/usr/ctxtEINA-LIFNR").Text = str(row["LIFNR"])

        # PASO 3: Material
        session.findById("wnd[0]/usr/ctxtEINA-MATNR").Text = str(row["MATNR"])

        # PASO 4: Org. compras con SetFocus + CaretPosition
        org_compras = str(row["EKORG"])
        field = session.findById("wnd[0]/usr/ctxtEINE-EKORG")
        field.SetFocus
        field.CaretPosition = len(org_compras)
        field.Text = org_compras

        # PASO 5: Validar con Enter
        session.findById("wnd[0]").SendVKey(0)
        time.sleep(0.5)

        # PASO 5b: Dar foco a la ventana
        try:
            session.findById("wnd[0]").SetFocus
        except Exception:
            pass
        time.sleep(0.3)

        # PASO 6: Redimensionar panel
        try:
            session.findById("wnd[0]").resizeWorkingPane(105, 25, False)
        except Exception:
            pass
        time.sleep(0.3)

        # PASO 6b: Confirmar/Refrescar antes de abrir condiciones
        session.findById("wnd[0]").SendVKey(0)
        time.sleep(0.5)

        # PASO 7: Abrir condiciones — F8 (SendVKey 8)
        session.findById("wnd[0]").SendVKey(8)
        time.sleep(0.5)

        # PASO 8: Manejar popup "Períodos de validez de condiciones"
        time.sleep(1.0)
        popup_detected = False
        popup_text = ""
        try:
            wnd1 = session.findById("wnd[1]")
            popup_text = wnd1.Text
            popup_detected = True
        except Exception:
            pass

        if popup_detected:
            if "validez" in popup_text.lower():
                # Crear nuevo período con F7
                session.findById("wnd[1]").SendVKey(7)
                time.sleep(1.0)

                valid_from = str(row.get("VALID_FROM", ""))
                valid_to = str(row.get("VALID_TO", ""))

                _fill_date_field(session, "desde", valid_from)
                _fill_date_field(session, "hasta", valid_to)

                # Confirmar fechas — Enter en la ventana superior
                time.sleep(0.3)
                for wnd_id in ("wnd[2]", "wnd[1]"):
                    try:
                        session.findById(wnd_id).SendVKey(0)
                        time.sleep(0.3)
                        break
                    except Exception:
                        pass
            else:
                # Popup desconocido — intentar Enter
                try:
                    session.findById("wnd[1]").SendVKey(0)
                    time.sleep(0.3)
                except Exception:
                    pass

        # PASO 9: Modificar precio en tabla de condiciones
        precio_id = (
            "wnd[0]/usr/tblSAPMV13ATCTRL_D0201/"
            "txtKONP-KBETR[{},0]".format(self.CONDITION_ROW)
        )
        precio_field = _wait_for_control(session, precio_id, timeout=10.0)
        precio_field.Text = str(row["PRICE"])
        time.sleep(0.3)

        # PASO 10: Guardar — F11 (SendVKey 11)
        session.findById("wnd[0]").SendVKey(11)
        time.sleep(1.0)

        # PASO 11: Verificar status bar
        status_bar = ""
        try:
            status_bar = session.findById("wnd[0]/sbar").Text
        except Exception:
            pass

        if "error" in status_bar.lower():
            raise SapBusinessError("SAP rechazó la fila")

    # -- interfaz TransactionPort ------------------------------------------ #

    def read_messages(self, session: Any) -> List[Any]:
        """Lee mensajes de la status bar de SAP."""
        try:
            text = session.findById("wnd[0]/sbar").Text
            if text:
                return [{"type": "S", "text": text}]
        except Exception:
            pass
        return []

    def confirm_result(self, session: Any) -> bool:
        """Confirmación post-navegación; la validación real ocurre en *navigate*."""
        return True


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
        try:
            return await self._run_rows(session, rows)
        except SapIntegrationError:
            raise
        except Exception as exc:
            raise SapNavigationError() from exc


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
