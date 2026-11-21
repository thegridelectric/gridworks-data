-- A stored reading in the unit a column wants: value / scale is in
-- base_unit (a gridworks.unit_scale row); the CASE converts between the
-- bases one quantity arrives in. NULL where no conversion is stated.
CREATE OR REPLACE FUNCTION gridworks.in_unit(
    value float,
    scale bigint,
    base_unit text,
    target text)
    RETURNS float
    IMMUTABLE
    LANGUAGE 'sql'
RETURN CASE
    WHEN base_unit = target THEN value / scale
    WHEN base_unit = 'C' AND target = 'F' THEN gridworks.c2f(value / scale)
    WHEN base_unit = 'F' AND target = 'C' THEN gridworks.f2c(value / scale)
    WHEN base_unit = 'Wh' AND target = 'kWh' THEN value / scale / 1000
    WHEN base_unit = 'kWh' AND target = 'Wh' THEN value / scale * 1000
END;
