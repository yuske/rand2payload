import math
import struct

from z3 import And, BitVecVal, LShR, ULE


def constraint_exact_double(calc, obs, browser):
    """Constrains the mantissa bits to exactly match a Math.random() double."""
    if browser == 'chrome':
        known = struct.unpack('<Q', struct.pack('d', obs + 1.0))[0] & ((1 << 52) - 1)
        mantissa = LShR(calc, 12)
        return mantissa == BitVecVal(known, 64)
    if browser in ('firefox', 'safari'):
        known = int(obs * (1 << 53))
        mask = (1 << 53) - 1
        mantissa = calc & BitVecVal(mask, 64)
        return mantissa == BitVecVal(known, 64)
    raise ValueError('Unsupported browser: %s' % browser)


def constraint_rounded(scale):
    """Constraint factory for observations like round(Math.random() * scale)."""

    def _constraint(calc, observation, browser):
        if not (isinstance(observation, int) and 0 <= observation <= scale):
            raise ValueError(f'Observation {observation!r} must be int in [0, {scale}]')
        bits = 52 if browser == 'chrome' else 53
        total = 1 << bits
        lower = max(0, math.ceil((observation - 0.5) * total / scale))
        upper = min(total - 1, math.floor((observation + 0.5) * total / scale) - 1)
        if upper < lower:
            return False
        if browser == 'chrome':
            mantissa = LShR(calc, 12)
        elif browser in ('firefox', 'safari'):
            mantissa = calc & BitVecVal((1 << bits) - 1, 64)
        else:
            raise ValueError('Unsupported browser: %s' % browser)
        return And(ULE(BitVecVal(lower, 64), mantissa), ULE(mantissa, BitVecVal(upper, 64)))

    return _constraint


__all__ = [
    name
    for name, value in globals().items()
    if callable(value) and getattr(value, '__module__', None) == __name__
]
