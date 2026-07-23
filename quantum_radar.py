from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional, List, Dict


class CarType(Enum):
    PRIVATE = "Private"
    TRUCK = "Truck"
    BUS = "Bus"


@dataclass(frozen=True)
class RadarObservation:
    plate_number: str
    obs_date: date
    car_type: CarType
    speed: int
    seatbelt_fastened: bool


@dataclass(frozen=True)
class Violation:
    description: str
    fee: float


class ViolationRule(ABC):
    @property
    @abstractmethod
    def rule_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, observation: RadarObservation) -> Optional[Violation]:
        raise NotImplementedError


class SeatbeltRule(ViolationRule):
    FEE = 100

    @property
    def rule_name(self) -> str:
        return "SeatbeltRule"

    def evaluate(self, observation: RadarObservation) -> Optional[Violation]:
        if not observation.seatbelt_fastened:
            return Violation("Seatbelt not fastned", self.FEE)
        return None


class SpeedLimitRule(ViolationRule):
    def __init__(self, car_type: CarType, max_speed: int, fee: float):
        self.car_type = car_type
        self.max_speed = max_speed
        self.fee = fee

    @property
    def rule_name(self) -> str:
        return f"SpeedLimitRule[{self.car_type.name} > {self.max_speed}]"

    def evaluate(self, observation: RadarObservation) -> Optional[Violation]:
        if observation.car_type == self.car_type and observation.speed > self.max_speed:
            desc = f"speed of {observation.speed} exceeded max allowed {self.max_speed}"
            return Violation(desc, self.fee)
        return None


@dataclass
class Fine:
    plate_number: str
    total_amount: float
    violations: List[Violation] = field(default_factory=list)


class QuRadar:

    def __init__(self, rules: List[ViolationRule]):
        self._rules: List[ViolationRule] = list(rules)
        self._issued_fines: List[Fine] = []
        self._violated_rule_counts: Dict[str, int] = {}

    def add_rule(self, rule: ViolationRule) -> None:
        """Allows adding a rule at runtime without modifying this class."""
        self._rules.append(rule)

    def process_observation(self, observation: RadarObservation) -> Optional[Fine]:
        """Evaluates one observation against all registered rules, prints
        and stores a Fine if any violation is found."""
        violations: List[Violation] = []

        for rule in self._rules:
            violation = rule.evaluate(observation)
            if violation is not None:
                violations.append(violation)
                self._violated_rule_counts[rule.rule_name] = (
                    self._violated_rule_counts.get(rule.rule_name, 0) + 1
                )

        if not violations:
            return None

        total = sum(v.fee for v in violations)
        fine = Fine(observation.plate_number, total, violations)
        self._issued_fines.append(fine)
        self._print_fine(fine)
        return fine

    @staticmethod
    def _print_fine(fine: Fine) -> None:
        print(f"Traffic for car {fine.plate_number}")
        print(f"Total amount: {int(fine.total_amount)} EGP")
        print("Violations:")
        for v in fine.violations:
            print(f"- {v.description} : {int(v.fee)} EGP")

    def get_all_possible_fines(self) -> Dict[str, float]:
        """Returns plate number -> total fine amount owed, across all observations."""
        result: Dict[str, float] = {}
        for fine in self._issued_fines:
            result[fine.plate_number] = result.get(fine.plate_number, 0) + fine.total_amount
        return result

    def get_all_violated_rules(self) -> Dict[str, int]:
        """Returns rule name -> number of times it was violated."""
        return dict(self._violated_rule_counts)


def main() -> None:
    """Demonstrates QuRadar in action."""
    rules: List[ViolationRule] = [
        SeatbeltRule(),
        SpeedLimitRule(CarType.TRUCK, 60, 300),
        SpeedLimitRule(CarType.PRIVATE, 80, 300),
        SpeedLimitRule(CarType.BUS, 70, 300),
    ]

    radar = QuRadar(rules)

    observations = [
        RadarObservation("ABC1234", date.today(), CarType.PRIVATE, 94, False),
        RadarObservation("XYZ777", date.today(), CarType.TRUCK, 55, True),
        RadarObservation("TRK555", date.today(), CarType.TRUCK, 75, True),
        RadarObservation("BUS111", date.today(), CarType.BUS, 65, False),
    ]

    for obs in observations:
        radar.process_observation(obs)
        print()

    print("=== All possible fines ===")
    for plate, total in radar.get_all_possible_fines().items():
        print(f"{plate} -> {int(total)} EGP")

    print()
    print("=== Violated rules count ===")
    for rule_name, count in radar.get_all_violated_rules().items():
        print(f"{rule_name} : {count}")


if __name__ == "__main__":
    main()
