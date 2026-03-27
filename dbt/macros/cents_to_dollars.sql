{% macro cents_to_dollars(column_name) %}
    round({{ column_name }}::number(18, 2) / 100, 2)
{% endmacro %}
