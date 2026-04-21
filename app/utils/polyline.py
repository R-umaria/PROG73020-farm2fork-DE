from __future__ import annotations


def decode_polyline(encoded: str, *, precision: int = 6) -> list[tuple[float, float]]:
    """Decode a polyline string into (lat, lon) tuples.

    Valhalla uses 6 digits of decimal precision in its route shapes.
    """

    coordinates: list[tuple[float, float]] = []
    index = 0
    latitude = 0
    longitude = 0
    factor = 10 ** precision

    while index < len(encoded):
        result = 0
        shift = 0
        while True:
            byte = ord(encoded[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        latitude += ~(result >> 1) if result & 1 else result >> 1

        result = 0
        shift = 0
        while True:
            byte = ord(encoded[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        longitude += ~(result >> 1) if result & 1 else result >> 1

        coordinates.append((latitude / factor, longitude / factor))

    return coordinates
