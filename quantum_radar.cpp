#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <map>
#include <optional>
#include <numeric>

enum class CarType
{
    Private,
    Truck,
    Bus
};

std::string carTypeToString(CarType type)
{
    switch (type)
    {
    case CarType::Private:
        return "Private";
    case CarType::Truck:
        return "Truck";
    case CarType::Bus:
        return "Bus";
    }
    return "Unknown";
}

struct RadarObservation
{
    std::string plateNumber;
    std::string date;
    CarType carType;
    int speed;
    bool seatbeltFastened;
};

struct Violation
{
    std::string description;
    double fee;
};

class ViolationRule
{
public:
    virtual ~ViolationRule() = default;

    virtual std::string ruleName() const = 0;

    virtual std::optional<Violation> evaluate(const RadarObservation &observation) const = 0;
};

class SeatbeltRule : public ViolationRule
{
public:
    static constexpr double FEE = 100;

    std::string ruleName() const override { return "SeatbeltRule"; }

    std::optional<Violation> evaluate(const RadarObservation &observation) const override
    {
        if (!observation.seatbeltFastened)
        {
            return Violation{"Seatbelt not fastned", FEE};
        }
        return std::nullopt;
    }
};

class SpeedLimitRule : public ViolationRule
{
public:
    SpeedLimitRule(CarType carType, int maxSpeed, double fee)
        : carType_(carType), maxSpeed_(maxSpeed), fee_(fee) {}

    std::string ruleName() const override
    {
        return "SpeedLimitRule[" + carTypeToString(carType_) + " > " + std::to_string(maxSpeed_) + "]";
    }

    std::optional<Violation> evaluate(const RadarObservation &observation) const override
    {
        if (observation.carType == carType_ && observation.speed > maxSpeed_)
        {
            std::string desc = "speed of " + std::to_string(observation.speed) +
                               " exceeded max allowed " + std::to_string(maxSpeed_);
            return Violation{desc, fee_};
        }
        return std::nullopt;
    }

private:
    CarType carType_;
    int maxSpeed_;
    double fee_;
};

struct Fine
{
    std::string plateNumber;
    double totalAmount;
    std::vector<Violation> violations;
};

class QuRadar
{
public:
    explicit QuRadar(std::vector<std::shared_ptr<ViolationRule>> rules)
        : rules_(std::move(rules)) {}

    /** Allows adding a rule at runtime without modifying this class. */
    void addRule(const std::shared_ptr<ViolationRule> &rule)
    {
        rules_.push_back(rule);
    }

    /** Evaluates one observation against all registered rules, prints and
     *  stores a Fine if any violation is found. */
    std::optional<Fine> processObservation(const RadarObservation &observation)
    {
        std::vector<Violation> violations;

        for (const auto &rule : rules_)
        {
            auto violation = rule->evaluate(observation);
            if (violation.has_value())
            {
                violations.push_back(*violation);
                violatedRuleCounts_[rule->ruleName()]++;
            }
        }

        if (violations.empty())
        {
            return std::nullopt;
        }

        double total = std::accumulate(violations.begin(), violations.end(), 0.0,
                                       [](double sum, const Violation &v)
                                       { return sum + v.fee; });

        Fine fine{observation.plateNumber, total, violations};
        issuedFines_.push_back(fine);
        printFine(fine);
        return fine;
    }

    std::map<std::string, double> getAllPossibleFines() const
    {
        std::map<std::string, double> result;
        for (const auto &fine : issuedFines_)
        {
            result[fine.plateNumber] += fine.totalAmount;
        }
        return result;
    }

    /** Returns rule name -> number of times it was violated. */
    std::map<std::string, int> getAllViolatedRules() const
    {
        return violatedRuleCounts_;
    }

private:
    static void printFine(const Fine &fine)
    {
        std::cout << "Traffic for car " << fine.plateNumber << "\n";
        std::cout << "Total amount: " << static_cast<int>(fine.totalAmount) << " EGP\n";
        std::cout << "Violations:\n";
        for (const auto &v : fine.violations)
        {
            std::cout << "- " << v.description << " : " << static_cast<int>(v.fee) << " EGP\n";
        }
    }

    std::vector<std::shared_ptr<ViolationRule>> rules_;
    std::vector<Fine> issuedFines_;
    std::map<std::string, int> violatedRuleCounts_;
};

int main()
{
    std::vector<std::shared_ptr<ViolationRule>> rules;
    rules.push_back(std::make_shared<SeatbeltRule>());
    rules.push_back(std::make_shared<SpeedLimitRule>(CarType::Truck, 60, 300));
    rules.push_back(std::make_shared<SpeedLimitRule>(CarType::Private, 80, 300));
    rules.push_back(std::make_shared<SpeedLimitRule>(CarType::Bus, 70, 300));

    QuRadar radar(rules);

    std::vector<RadarObservation> observations = {
        {"ABC1234", "2026-07-23", CarType::Private, 94, false},
        {"XYZ777", "2026-07-23", CarType::Truck, 55, true},
        {"TRK555", "2026-07-23", CarType::Truck, 75, true},
        {"BUS111", "2026-07-23", CarType::Bus, 65, false}};

    for (const auto &obs : observations)
    {
        radar.processObservation(obs);
        std::cout << "\n";
    }

    std::cout << "=== All possible fines ===\n";
    for (const auto &[plate, total] : radar.getAllPossibleFines())
    {
        std::cout << plate << " -> " << static_cast<int>(total) << " EGP\n";
    }

    std::cout << "\n=== Violated rules count ===\n";
    for (const auto &[ruleName, count] : radar.getAllViolatedRules())
    {
        std::cout << ruleName << " : " << count << "\n";
    }

    return 0;
}
