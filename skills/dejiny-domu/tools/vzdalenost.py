"""Vzdálenost dvou bodů v km (rovinná aproximace, na desítky km stačí)."""
import math


def km(lat, lon, lat2, lon2):
    return math.hypot((lon2 - lon) * 111.32 * math.cos(math.radians(lat)), (lat2 - lat) * 111.32)
