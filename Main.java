import java.time.LocalDate;
import java.util.*;

enum CarType {
    PRIVATE, TRUCK, BUS
}

class RadarObservation {
    private final String plateNumber;
    private final LocalDate date;
    private final CarType carType;
    private final int speed;
    private final boolean seatbeltFastened;

    public RadarObservation(String plateNumber, LocalDate date, CarType carType,
            int speed, boolean seatbeltFastened) {
        this.plateNumber = plateNumber;
        this.date = date;
        this.carType = carType;
        this.speed = speed;
        this.seatbeltFastened = seatbeltFastened;
    }

    public String getPlateNumber() {
        return plateNumber;
    }

    public LocalDate getDate() {
        return date;
    }

    public CarType getCarType() {
        return carType;
    }

    public int getSpeed() {
        return speed;
    }

    public boolean isSeatbeltFastened() {
        return seatbeltFastened;
    }
}

class Violation {
    private final String description;
    private final double fee;

    public Violation(String description, double fee) {
        this.description = description;
        this.fee = fee;
    }

    public String getDescription() {
        return description;
    }

    public double getFee() {
        return fee;
    }
}

interface ViolationRule {
    String getRuleName();

    Optional<Violation> evaluate(RadarObservation observation);
}

class SeatbeltRule implements ViolationRule {
    private static final double FEE = 100;

    @Override
    public String getRuleName() {
        return "SeatbeltRule";
    }

    @Override
    public Optional<Violation> evaluate(RadarObservation observation) {
        if (!observation.isSeatbeltFastened()) {
            return Optional.of(new Violation("Seatbelt not fastned", FEE));
        }
        return Optional.empty();
    }
}

class SpeedLimitRule implements ViolationRule {
    private final CarType carType;
    private final int maxSpeed;
    private final double fee;

    public SpeedLimitRule(CarType carType, int maxSpeed, double fee) {
        this.carType = carType;
        this.maxSpeed = maxSpeed;
        this.fee = fee;
    }

    @Override
    public String getRuleName() {
        return "SpeedLimitRule[" + carType + " > " + maxSpeed + "]";
    }

    @Override
    public Optional<Violation> evaluate(RadarObservation observation) {
        if (observation.getCarType() == carType && observation.getSpeed() > maxSpeed) {
            String desc = "speed of " + observation.getSpeed() +
                    " exceeded max allowed " + maxSpeed;
            return Optional.of(new Violation(desc, fee));
        }
        return Optional.empty();
    }
}

class Fine {
    private final String plateNumber;
    private final double totalAmount;
    private final List<Violation> violations;

    public Fine(String plateNumber, double totalAmount, List<Violation> violations) {
        this.plateNumber = plateNumber;
        this.totalAmount = totalAmount;
        this.violations = violations;
    }

    public String getPlateNumber() {
        return plateNumber;
    }

    public double getTotalAmount() {
        return totalAmount;
    }

    public List<Violation> getViolations() {
        return violations;
    }
}

class QuRadar {
    private final List<ViolationRule> rules;
    private final List<Fine> issuedFines = new ArrayList<>();
    private final Map<String, Integer> violatedRuleCounts = new LinkedHashMap<>();

    public QuRadar(List<ViolationRule> rules) {
        this.rules = new ArrayList<>(rules);
    }

    public void addRule(ViolationRule rule) {
        rules.add(rule);
    }

    public Optional<Fine> processObservation(RadarObservation observation) {
        List<Violation> violations = new ArrayList<>();

        for (ViolationRule rule : rules) {
            Optional<Violation> violation = rule.evaluate(observation);
            if (violation.isPresent()) {
                violations.add(violation.get());
                violatedRuleCounts.merge(rule.getRuleName(), 1, Integer::sum);
            }
        }

        if (violations.isEmpty()) {
            return Optional.empty();
        }

        double total = violations.stream().mapToDouble(Violation::getFee).sum();
        Fine fine = new Fine(observation.getPlateNumber(), total, violations);
        issuedFines.add(fine);
        printFine(fine);
        return Optional.of(fine);
    }

    private void printFine(Fine fine) {
        System.out.println("Traffic for car " + fine.getPlateNumber());
        System.out.println("Total amount: " + (int) fine.getTotalAmount() + " EGP");
        System.out.println("Violations:");
        for (Violation v : fine.getViolations()) {
            System.out.println("- " + v.getDescription() + " : " + (int) v.getFee() + " EGP");
        }
    }

    public Map<String, Double> getAllPossibleFines() {
        Map<String, Double> result = new LinkedHashMap<>();
        for (Fine fine : issuedFines) {
            result.merge(fine.getPlateNumber(), fine.getTotalAmount(), Double::sum);
        }
        return result;
    }

    public Map<String, Integer> getAllViolatedRules() {
        return new LinkedHashMap<>(violatedRuleCounts);
    }
}

public class Main {
    public static void main(String[] args) {
        List<ViolationRule> rules = new ArrayList<>();
        rules.add(new SeatbeltRule());
        rules.add(new SpeedLimitRule(CarType.TRUCK, 60, 300));
        rules.add(new SpeedLimitRule(CarType.PRIVATE, 80, 300));
        rules.add(new SpeedLimitRule(CarType.BUS, 70, 300));

        QuRadar radar = new QuRadar(rules);

        List<RadarObservation> observations = Arrays.asList(
                new RadarObservation("ABC1234", LocalDate.now(), CarType.PRIVATE, 94, false),
                new RadarObservation("XYZ777", LocalDate.now(), CarType.TRUCK, 55, true),
                new RadarObservation("TRK555", LocalDate.now(), CarType.TRUCK, 75, true),
                new RadarObservation("BUS111", LocalDate.now(), CarType.BUS, 65, false));

        for (RadarObservation obs : observations) {
            radar.processObservation(obs);
            System.out.println();
        }

        System.out.println("=== All possible fines ===");
        for (Map.Entry<String, Double> entry : radar.getAllPossibleFines().entrySet()) {
            System.out.println(entry.getKey() + " -> " + (int) (double) entry.getValue() + " EGP");
        }

        System.out.println();
        System.out.println("=== Violated rules count ===");
        for (Map.Entry<String, Integer> entry : radar.getAllViolatedRules().entrySet()) {
            System.out.println(entry.getKey() + " : " + entry.getValue());
        }
    }
}
