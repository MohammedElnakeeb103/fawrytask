"""
============================================================================
QuRadar - Quantum Traffic Radar System (Python version)
============================================================================
This module models a smart traffic radar unit that receives observations
from a physical roadside radar/camera device (plate number, date, car
type, measured speed, and seatbelt status) and evaluates them against a
configurable, pluggable set of traffic rules (ViolationRule).

AI model used: the physical radar's raw sensor stream (video/LIDAR) is
assumed to be pre-processed by an ANPR (Automatic Number Plate
Recognition) pipeline based on a YOLOv8 object-detection model (to locate
and classify the vehicle as Private/Truck/Bus and to locate the driver
region) combined with a CRNN (Convolutional Recurrent Neural Network) +
CTC-decoder OCR model that reads the plate characters. A lightweight CNN
image classifier is used to detect whether the seatbelt is fastened from
the cropped driver-seat region. QuRadar itself does not run this AI model;
it only consumes the already-structured output (RadarObservation) that
these models produce, keeping the rule-evaluation logic independent from
the perception layer.

Design notes (extensibility):
- QuRadar is completely decoupled from the concrete traffic rules. It only
  depends on the ViolationRule interface (an abstract base class here).
- New rules (e.g. "motorcycle must not exceed 50", "no phone usage", ...)
  can be added by simply creating a new class that implements
  ViolationRule and registering an instance with QuRadar - no change to
  QuRadar's source code is required (Open/Closed Principle).
- Each observation can trigger zero or more violations; each violation
  carries its own fine amount, and QuRadar aggregates them into a single
  Fine per observation.
============================================================================
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional, List, Dict


class CarType(Enum):
    """The type of vehicle detected by the radar's perception model."""
    PRIVATE = "Private"
    TRUCK = "Truck"
    BUS = "Bus"


@dataclass(frozen=True)
class RadarObservation:
    """Raw structured data produced by the physical radar device / its AI
    perception pipeline for a single passing vehicle."""
    plate_number: str
    obs_date: date
    car_type: CarType
    speed: int
    seatbelt_fastened: bool


@dataclass(frozen=True)
class Violation:
    """A single rule violation with its human-readable description and fee."""
    description: str
    fee: float


class ViolationRule(ABC):
    """Contract every traffic rule must implement. QuRadar only ever talks
    to this interface, so adding a new rule never requires touching QuRadar."""

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """A short unique name used for reporting violated-rule counts."""
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, observation: RadarObservation) -> Optional[Violation]:
        """Returns a Violation if the observation breaks this rule, else None."""
        raise NotImplementedError


class SeatbeltRule(ViolationRule):
    """Rule: seatbelt must be fastened, regardless of car type."""
    FEE = 100

    @property
    def rule_name(self) -> str:
        return "SeatbeltRule"

    def evaluate(self, observation: RadarObservation) -> Optional[Violation]:
        if not observation.seatbelt_fastened:
            return Violation("Seatbelt not fastned", self.FEE)
        return None


class SpeedLimitRule(ViolationRule):
    """Generic speed-limit rule for a given car type. New speed limits (or
    new car types) can be introduced just by instantiating this class again
    with different parameters - no code change needed elsewhere."""

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
    """The aggregated result of all violations found for one observation."""
    plate_number: str
    total_amount: float
    violations: List[Violation] = field(default_factory=list)


class QuRadar:
    """QuRadar - see module docstring for the full system description.
    Holds a pluggable list of ViolationRule instances and evaluates each
    incoming RadarObservation against all of them."""

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

    # Example: adding a brand new rule at runtime, no QuRadar changes needed
    # radar.add_rule(SpeedLimitRule(CarType.BUS, 70, 250))

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
