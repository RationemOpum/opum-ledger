import pendulum
from blacksheep.server.bindings.converters import TypeConverter, converters


class DateTimeConverter(TypeConverter):
    """Converter for pendulum DateTime objects."""

    def can_convert(self, expected_type) -> bool:
        return expected_type is str

    def convert(self, value: str, expected_type) -> pendulum.DateTime:
        return pendulum.from_format(
            value,
            "ddd, DD MMM YYYY HH:mm:ss z",
        )


converters.append(DateTimeConverter())
