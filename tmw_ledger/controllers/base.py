from blacksheep import FromHeader


class IfUnmodifiedSince(FromHeader[str]):
    name = "If-Unmodified-Since"


class IfMatch(FromHeader[str]):
    name = "If-Match"
