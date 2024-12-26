from math import sin, cos, atan2, sqrt


type Vec = tuple[float, float]


def to_cartesian(r: float, theta: float) -> Vec:
    return (r * cos(theta), r * sin(theta))


def to_polar(x: float, y: float) -> tuple[float, float]:
    return (sqrt(x * x + y * y), atan2(y, x))


def add(v1: Vec, v2: Vec) -> Vec:
    return (v1[0] + v2[0], v1[1] + v2[1])


def sub(v1: Vec, v2: Vec) -> Vec:
    return (v1[0] - v2[0], v1[1] - v2[1])


def mult(s: float, v: Vec) -> Vec:
    return (s * v[0], s * v[1])


def length(vec: Vec) -> float:
    return sqrt(vec[0] ** 2 + vec[1] ** 2)

def rot90(x: float, y: float) -> Vec:
    return (-y, x)


def irot90(x: float, y: float) -> Vec:
    return (y, -x)
