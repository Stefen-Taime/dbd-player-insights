{% macro date_spine(start_date, end_date) %}
    {{
        dbt_date.get_date_dimension(
            start_date,
            end_date
        )
    }}
{% endmacro %}
