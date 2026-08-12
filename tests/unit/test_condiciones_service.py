"""
Tests unitarios para services/condiciones_service.py.

Verifica la lógica de validación VK12:
- Constantes de validación (flujos, campos, valores)
- Funciones auxiliares (_solo_numeros, _is_numeric)
- _validate_field (validación individual de campos)
"""

import pytest

from services.condiciones_service import (
    FLOW_FIELDS,
    REQUIRED_COLUMNS,
    VALID_CAN_DISTR,
    VALID_FLOWS,
    VALID_ORG_VENTA,
    VALID_RAMO,
    VALID_SECTOR,
    VALID_UNIDAD_MEDIDA,
    _is_numeric,
    _solo_numeros,
    _validate_field,
    get_template_path,
)


# ============================================================
# Tests para constantes
# ============================================================


class TestValidationConstants:
    """Tests para las constantes de validación VK12."""

    def test_required_columns_has_9(self):
        """Test: REQUIRED_COLUMNS tiene 9 columnas."""
        assert len(REQUIRED_COLUMNS) == 9

    def test_required_columns_content(self):
        """Test: REQUIRED_COLUMNS contiene las columnas esperadas."""
        expected = [
            "MATERIAL",
            "UNIDAD_DE_MEDIDA",
            "IMPORTE",
            "GRUPO_ARTICULO",
            "ORG_VENTA",
            "CAN_DISTR",
            "SECTOR",
            "RAMO",
            "TIPO_MODIFICACION",
        ]
        assert REQUIRED_COLUMNS == expected

    def test_valid_flows_count(self):
        """Test: Hay 4 flujos válidos."""
        assert len(VALID_FLOWS) == 4

    def test_valid_flows_content(self):
        """Test: Los flujos válidos son los esperados."""
        expected = {
            "mat_orgvent_candistr",
            "orgvent_candistr_gpoart",
            "orgvent_candistr_sec_ramo_mat",
            "orgven_candist_sec_gpoart",
        }
        assert VALID_FLOWS == expected

    def test_flow_fields_keys_match_flows(self):
        """Test: FLOW_FIELDS tiene una entrada para cada flujo válido."""
        assert set(FLOW_FIELDS.keys()) == VALID_FLOWS

    def test_valid_org_venta(self):
        """Test: VALID_ORG_VENTA contiene solo 1000."""
        assert VALID_ORG_VENTA == {"1000"}

    def test_valid_can_distr(self):
        """Test: VALID_CAN_DISTR tiene 5 valores."""
        assert len(VALID_CAN_DISTR) == 5
        assert "10" in VALID_CAN_DISTR
        assert "50" in VALID_CAN_DISTR

    def test_valid_sector(self):
        """Test: VALID_SECTOR tiene 5 valores."""
        assert len(VALID_SECTOR) == 5

    def test_valid_ramo(self):
        """Test: VALID_RAMO tiene 5 valores."""
        assert len(VALID_RAMO) == 5
        assert "ZDET" in VALID_RAMO

    def test_valid_unidad_medida(self):
        """Test: VALID_UNIDAD_MEDIDA tiene valores comunes."""
        assert "UN" in VALID_UNIDAD_MEDIDA
        assert "KG" in VALID_UNIDAD_MEDIDA
        assert "ST" in VALID_UNIDAD_MEDIDA


# ============================================================
# Tests para _solo_numeros
# ============================================================


class TestSoloNumeros:
    """Tests para la función _solo_numeros."""

    def test_pure_digits_true(self):
        """Test: Retorna True para solo dígitos."""
        assert _solo_numeros("123456") is True

    def test_letters_false(self):
        """Test: Retorna False si hay letras."""
        assert _solo_numeros("ABC123") is False

    def test_mixed_false(self):
        """Test: Retorna False para mixto."""
        assert _solo_numeros("12.34") is False

    def test_empty_string(self):
        """Test: String vacío retorna False."""
        assert _solo_numeros("") is False

    def test_spaces_around(self):
        """Test: Espacios alrededor se ignoran."""
        assert _solo_numeros("  123  ") is True

    def test_integer_input(self):
        """Test: Acepta enteros."""
        assert _solo_numeros(123) is True

    def test_special_chars(self):
        """Test: Caracteres especiales retornan False."""
        assert _solo_numeros("123-456") is False
        assert _solo_numeros("123456!") is False


# ============================================================
# Tests para _is_numeric
# ============================================================


class TestIsNumeric:
    """Tests para la función _is_numeric."""

    def test_integer_string(self):
        """Test: String de entero es numérico."""
        assert _is_numeric("123") is True

    def test_decimal_string(self):
        """Test: String decimal es numérico."""
        assert _is_numeric("123.45") is True

    def test_negative_number(self):
        """Test: Número negativo es numérico."""
        assert _is_numeric("-123") is True

    def test_letters(self):
        """Test: Letras no son numéricas."""
        assert _is_numeric("abc") is False

    def test_empty(self):
        """Test: String vacío no es numérico."""
        assert _is_numeric("") is False

    def test_none_value(self):
        """Test: None no es numérico."""
        assert _is_numeric(None) is False

    def test_integer_input(self):
        """Test: Integer es numérico."""
        assert _is_numeric(123) is True

    def test_float_input(self):
        """Test: Float es numérico."""
        assert _is_numeric(123.45) is True


# ============================================================
# Tests para _validate_field
# ============================================================


class TestValidateField:
    """Tests para la función _validate_field."""

    # --- MATERIAL ---
    def test_material_valid(self):
        """Test: MATERIAL válido (solo números)."""
        result = _validate_field("MATERIAL", "12345678", 2)
        assert result is None

    def test_material_with_letters(self):
        """Test: MATERIAL con letras retorna error."""
        result = _validate_field("MATERIAL", "ABC12345", 2)
        assert result is not None
        assert "letras" in result.lower() or "caracteres" in result.lower()

    def test_material_empty(self):
        """Test: MATERIAL vacío retorna error."""
        result = _validate_field("MATERIAL", "", 2)
        assert result is not None

    def test_material_none(self):
        """Test: MATERIAL None retorna error."""
        result = _validate_field("MATERIAL", None, 2)
        assert result is not None

    # --- IMPORTE ---
    def test_importe_valid(self):
        """Test: IMPORTE numérico válido."""
        result = _validate_field("IMPORTE", "100.50", 2)
        assert result is None

    def test_importe_not_numeric(self):
        """Test: IMPORTE no numérico retorna error."""
        result = _validate_field("IMPORTE", "abc", 2)
        assert result is not None
        assert "numérico" in result.lower()

    def test_importe_none(self):
        """Test: IMPORTE None retorna error."""
        result = _validate_field("IMPORTE", None, 2)
        assert result is not None

    # --- ORG_VENTA ---
    def test_org_venta_valid(self):
        """Test: ORG_VENTA válida (1000)."""
        result = _validate_field("ORG_VENTA", "1000", 2)
        assert result is None

    def test_org_venta_invalid(self):
        """Test: ORG_VENTA inválida retorna error."""
        result = _validate_field("ORG_VENTA", "2000", 2)
        assert result is not None
        assert "1000" in result

    # --- CAN_DISTR ---
    def test_can_distr_valid(self):
        """Test: CAN_DISTR válida."""
        result = _validate_field("CAN_DISTR", "10", 2)
        assert result is None

    def test_can_distr_invalid(self):
        """Test: CAN_DISTR inválida retorna error."""
        result = _validate_field("CAN_DISTR", "99", 2)
        assert result is not None

    # --- SECTOR ---
    def test_sector_valid(self):
        """Test: SECTOR válido."""
        result = _validate_field("SECTOR", "10", 2)
        assert result is None

    def test_sector_invalid(self):
        """Test: SECTOR inválido retorna error."""
        result = _validate_field("SECTOR", "99", 2)
        assert result is not None

    # --- RAMO ---
    def test_ramo_valid(self):
        """Test: RAMO válido."""
        result = _validate_field("RAMO", "ZDET", 2)
        assert result is None

    def test_ramo_invalid(self):
        """Test: RAMO inválido retorna error."""
        result = _validate_field("RAMO", "XXXX", 2)
        assert result is not None

    def test_ramo_case_insensitive(self):
        """Test: RAMO es case-insensitive."""
        result = _validate_field("RAMO", "zdet", 2)
        assert result is None

    # --- GRUPO_ARTICULO ---
    def test_grupo_articulo_valid(self):
        """Test: GRUPO_ARTICULO válido (9 dígitos)."""
        result = _validate_field("GRUPO_ARTICULO", "123456789", 2)
        assert result is None

    def test_grupo_articulo_wrong_length(self):
        """Test: GRUPO_ARTICULO con longitud incorrecta retorna error."""
        result = _validate_field("GRUPO_ARTICULO", "12345", 2)
        assert result is not None
        assert "9 caracteres" in result

    def test_grupo_articulo_with_letters(self):
        """Test: GRUPO_ARTICULO con letras retorna error."""
        result = _validate_field("GRUPO_ARTICULO", "12345678A", 2)
        assert result is not None

    # --- UNIDAD_DE_MEDIDA ---
    def test_unidad_medida_valid(self):
        """Test: UNIDAD_DE_MEDIDA válida."""
        result = _validate_field("UNIDAD_DE_MEDIDA", "UN", 2)
        assert result is None

    def test_unidad_medida_invalid(self):
        """Test: UNIDAD_DE_MEDIDA inválida retorna error."""
        result = _validate_field("UNIDAD_DE_MEDIDA", "ZZ", 2)
        assert result is not None

    # --- Generic ---
    def test_none_value_returns_error(self):
        """Test: Cualquier campo con None retorna error."""
        for field in [
            "MATERIAL",
            "ORG_VENTA",
            "CAN_DISTR",
            "SECTOR",
            "RAMO",
            "UNIDAD_DE_MEDIDA",
        ]:
            result = _validate_field(field, None, 2)
            assert result is not None, f"Campo {field} debería retornar error con None"

    def test_nan_string_returns_error(self):
        """Test: Valor 'nan' retorna error."""
        result = _validate_field("MATERIAL", "nan", 2)
        assert result is not None

    def test_row_number_in_error(self):
        """Test: El número de fila aparece en el mensaje de error."""
        result = _validate_field("MATERIAL", "ABC", 5)
        assert "5" in result


# ============================================================
# Tests para get_template_path
# ============================================================


class TestGetTemplatePathCondiciones:
    """Tests para get_template_path en condiciones_service."""

    def test_returns_path_object(self):
        """Test: Retorna un objeto Path."""
        from pathlib import Path

        path = get_template_path()
        assert isinstance(path, Path)

    def test_ends_with_correct_name(self):
        """Test: Termina con el nombre correcto."""
        path = get_template_path()
        assert path.name == "condiciones_template.xlsx"
