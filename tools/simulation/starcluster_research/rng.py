MASK64 = (1 << 64) - 1


def fnv1a64(text: str) -> int:
    h = 14695981039346656037
    for b in text.encode('utf-8'):
        h ^= b
        h = (h * 1099511628211) & MASK64
    return h


class XorShift64:
    __slots__ = ('state',)
    def __init__(self, seed: int):
        self.state = seed & MASK64 or 0x9E3779B97F4A7C15

    def next_u64(self) -> int:
        x = self.state
        x ^= (x << 13) & MASK64
        x ^= x >> 7
        x ^= (x << 17) & MASK64
        self.state = x & MASK64
        return self.state

    def randint(self, low: int, high: int) -> int:
        if high < low:
            raise ValueError('invalid randint bounds')
        return low + self.next_u64() % (high - low + 1)

    def d100(self) -> int:
        return 1 + self.next_u64() % 100

    def random(self) -> float:
        return self.next_u64() / float(1 << 64)


def derive_seed(master: int, *parts: object) -> int:
    state = master & MASK64
    for part in parts:
        state ^= fnv1a64(str(part))
        state = (state * 0x9E3779B97F4A7C15) & MASK64
        state ^= state >> 29
    return state or 0xD1B54A32D192ED03
