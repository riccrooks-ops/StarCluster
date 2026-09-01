from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

DIRECTIONS: tuple[tuple[int, int], ...] = (
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
)


@dataclass(frozen=True, slots=True, order=True)
class HexCoord:
    q: int
    r: int

    @property
    def s(self) -> int:
        return -self.q - self.r

    def distance_to(self, other: "HexCoord") -> int:
        return (abs(self.q - other.q) + abs(self.r - other.r) + abs(self.s - other.s)) // 2

    def length(self) -> int:
        return self.distance_to(HexCoord(0, 0))

    def neighbors(self) -> tuple["HexCoord", ...]:
        return tuple(HexCoord(self.q + dq, self.r + dr) for dq, dr in DIRECTIONS)


@dataclass(frozen=True, slots=True)
class HexMap:
    radius: int
    cells: tuple[HexCoord, ...]
    cell_set: frozenset[HexCoord]

    @classmethod
    def create_hexagon(cls, radius: int) -> "HexMap":
        if radius < 0:
            raise ValueError("radius cannot be negative")
        cells = tuple(
            HexCoord(q, r)
            for q in range(-radius, radius + 1)
            for r in range(-radius, radius + 1)
            if HexCoord(q, r).length() <= radius
        )
        return cls(radius, cells, frozenset(cells))

    def contains(self, c: HexCoord) -> bool:
        return c in self.cell_set

    def is_boundary(self, c: HexCoord) -> bool:
        return self.contains(c) and c.length() == self.radius

    def neighbors_of(self, c: HexCoord) -> tuple[HexCoord, ...]:
        if not self.contains(c):
            raise ValueError(f"coordinate outside map: {c}")
        return tuple(n for n in c.neighbors() if self.contains(n))


class RangeOrder(str, Enum):
    HOLD = "Hold"
    CLOSE = "Close"
    OPEN = "Open"
    MAINTAIN = "MaintainPreferredRange"


@dataclass(frozen=True, slots=True)
class TacticalOrderPlan:
    range_order: RangeOrder
    desired_range: int | None = None
    reason: str = ""


@dataclass(frozen=True, slots=True)
class FiniteTacticalMove:
    origin: HexCoord
    destination: HexCoord
    path: tuple[HexCoord, ...]
    final_range: int
    closest_approach: int
    farthest_separation: int
    movement_hexes: int
    ended_on_boundary: bool
    requested_order: RangeOrder
    desired_range: int | None


def resolve_search_toward_center(map_: HexMap, origin: HexCoord, available_movement: int) -> FiniteTacticalMove:
    if not map_.contains(origin):
        raise ValueError("origin outside map")
    if available_movement < 0:
        raise ValueError("available movement cannot be negative")
    plan = TacticalOrderPlan(RangeOrder.CLOSE, None, "pre-contact centerward search")
    if available_movement == 0 or origin == HexCoord(0, 0):
        path = (origin,)
    else:
        # Match EncounterSearchMovementResolver: minimum length, then maximum
        # interior margin (redundant after length, retained for parity), then Q/R.
        destination = min(
            map_.neighbors_of(origin),
            key=lambda cell: (cell.length(), -(map_.radius - cell.length()), cell.q, cell.r),
        )
        path = (origin, destination)
    destination = path[-1]
    # Search does not know target. These range values are placeholders and are
    # replaced by the encounter consumer, which has authoritative geometry.
    return FiniteTacticalMove(
        origin, destination, path, 0, 0, 0, len(path) - 1,
        map_.is_boundary(destination), plan.range_order, plan.desired_range,
    )


def _direction_penalty(order: RangeOrder, initial_range: int, candidate_range: int) -> int:
    if order == RangeOrder.CLOSE and candidate_range > initial_range:
        return 1
    if order == RangeOrder.OPEN and candidate_range < initial_range:
        return 1
    return 0


def _desired_error(plan: TacticalOrderPlan, initial_range: int, available: int, candidate_range: int) -> int:
    if plan.desired_range is not None:
        desired = plan.desired_range
    elif plan.range_order == RangeOrder.CLOSE:
        desired = max(0, initial_range - available)
    elif plan.range_order == RangeOrder.OPEN:
        desired = initial_range + available
    else:
        desired = initial_range
    return abs(candidate_range - desired)


def _path_score(plan: TacticalOrderPlan, range_to_target: int) -> int:
    if plan.range_order == RangeOrder.CLOSE:
        return range_to_target
    if plan.range_order == RangeOrder.OPEN:
        return -range_to_target
    if plan.range_order == RangeOrder.MAINTAIN and plan.desired_range is not None:
        return abs(range_to_target - plan.desired_range)
    return 0


def _relative_tie(
    origin: HexCoord, target: HexCoord, candidate: HexCoord,
    tie_break_reference: HexCoord | None = None,
) -> tuple[int, int, int]:
    """Rotation-invariant local tie break.

    The old global Q/R tie break changes under a 180-degree physical mirror.
    Dot/cross values of the target vector and candidate displacement are
    invariant when both vectors rotate 180 degrees, so physically mirrored
    encounters choose physically mirrored destinations.
    """
    vq, vr = target.q - origin.q, target.r - origin.r
    if vq == 0 and vr == 0 and tie_break_reference is not None:
        vq, vr = tie_break_reference.q - origin.q, tie_break_reference.r - origin.r
    if vq == 0 and vr == 0:
        # Generic callers without an encounter-bearing reference retain a
        # deterministic fallback. CP126 full-map encounters always supply a
        # physical entry-bearing reference, so this fallback is not used there.
        vq, vr = -origin.q, -origin.r
    wq, wr = candidate.q - origin.q, candidate.r - origin.r
    cross = vq * wr - vr * wq
    # Twice the Euclidean dot product in an axial basis with 60-degree axes.
    dot2 = 2 * vq * wq + vq * wr + vr * wq + 2 * vr * wr
    return (abs(cross), cross, -dot2)


def resolve_finite_movement(
    map_: HexMap,
    origin: HexCoord,
    target: HexCoord,
    available_movement: int,
    plan: TacticalOrderPlan,
    tie_break_reference: HexCoord | None = None,
) -> FiniteTacticalMove:
    if not map_.contains(origin) or not map_.contains(target):
        raise ValueError("origin/target outside map")
    if available_movement < 0:
        raise ValueError("available movement cannot be negative")
    initial_range = origin.distance_to(target)
    if available_movement == 0 or plan.range_order == RangeOrder.HOLD:
        path = (origin,)
    else:
        candidates = [cell for cell in map_.cells if origin.distance_to(cell) <= available_movement]
        destination = min(
            candidates,
            key=lambda cell: (
                _direction_penalty(plan.range_order, initial_range, cell.distance_to(target)),
                _desired_error(plan, initial_range, available_movement, cell.distance_to(target)),
                -(map_.radius - cell.length()),
                origin.distance_to(cell),
                *_relative_tie(origin, target, cell, tie_break_reference),
            ),
        )
        path_list = [origin]
        current = origin
        while current != destination:
            remaining = current.distance_to(destination)
            next_cell = min(
                (cell for cell in map_.neighbors_of(current) if cell.distance_to(destination) == remaining - 1),
                key=lambda cell: (
                    _path_score(plan, cell.distance_to(target)),
                    -(map_.radius - cell.length()),
                    *_relative_tie(current, target, cell, tie_break_reference),
                ),
            )
            path_list.append(next_cell)
            current = next_cell
        path = tuple(path_list)
    destination = path[-1]
    ranges = tuple(cell.distance_to(target) for cell in path)
    return FiniteTacticalMove(
        origin=origin,
        destination=destination,
        path=path,
        final_range=destination.distance_to(target),
        closest_approach=min(ranges),
        farthest_separation=max(ranges),
        movement_hexes=len(path) - 1,
        ended_on_boundary=map_.is_boundary(destination),
        requested_order=plan.range_order,
        desired_range=plan.desired_range,
    )


@dataclass(frozen=True, slots=True)
class MissileAdvance:
    origin: HexCoord
    target: HexCoord
    destination: HexCoord
    path: tuple[HexCoord, ...]
    distance_traveled_this_phase: int
    total_distance_traveled: int
    terminal: bool
    range_exhausted: bool


def advance_missile_finite_map(
    map_: HexMap,
    origin: HexCoord,
    target: HexCoord,
    speed: int,
    maximum_travel: int,
    distance_already_traveled: int = 0,
) -> MissileAdvance:
    """Advance a missile toward the target's current finite-map coordinate.

    The current target coordinate is authoritative each phase. Equal shortest
    next-hex choices use the same target-relative, rotation-invariant tie break
    as ship movement so a physical 180-degree mirror remains a physical mirror.
    """
    if not map_.contains(origin) or not map_.contains(target):
        raise ValueError("origin/target outside map")
    if speed < 0 or maximum_travel < 0 or distance_already_traveled < 0:
        raise ValueError("negative missile movement inputs")
    remaining = max(0, maximum_travel - distance_already_traveled)
    budget = min(speed, remaining)
    current = origin
    path = [origin]
    moved = 0
    for _ in range(budget):
        if current == target:
            break
        current_distance = current.distance_to(target)
        current = min(
            (cell for cell in map_.neighbors_of(current) if cell.distance_to(target) == current_distance - 1),
            key=lambda cell: _relative_tie(current, target, cell),
        )
        path.append(current)
        moved += 1
    total = distance_already_traveled + moved
    distance = current.distance_to(target)
    exhausted = distance > 0 and total >= maximum_travel
    return MissileAdvance(
        origin, target, current, tuple(path), moved, total,
        terminal=(distance == 0), range_exhausted=exhausted,
    )
