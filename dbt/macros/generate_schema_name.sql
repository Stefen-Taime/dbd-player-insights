{% macro generate_schema_name(custom_schema_name, node) -%}
    {#
        Custom schema naming: use the custom schema name directly (no prefix).
        This avoids "dbt_<target_schema>_staging" and gives us clean schema names
        like STAGING, INTERMEDIATE, MARTS.
    #}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
