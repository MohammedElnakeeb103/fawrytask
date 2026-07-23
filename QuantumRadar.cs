using System;
using System.Collections.Generic;
using System.Linq;

namespace QuantumRadarSystem
{
    public enum CarType
    {
        Private,
        Truck,
        Bus
    }

    public class RadarObservation
    {
        public string PlateNumber { get; }
        public DateTime Date { get; }
        public CarType CarType { get; }
        public int Speed { get; }
        public bool SeatbeltFastened { get; }

        public RadarObservation(string plateNumber, DateTime date, CarType carType,
                                 int speed, bool seatbeltFastened)
        {
            PlateNumber = plateNumber;
            Date = date;
            CarType = carType;
            Speed = speed;
            SeatbeltFastened = seatbeltFastened;
        }
    }

    public class Violation
    {
        public string Description { get; }
        public double Fee { get; }

        public Violation(string description, double fee)
        {
            Description = description;
            Fee = fee;
        }
    }

    public interface IViolationRule
    {
        string RuleName { get; }

        Violation? Evaluate(RadarObservation observation);
    }

    public class SeatbeltRule : IViolationRule
    {
        private const double Fee = 100;

        public string RuleName => "SeatbeltRule";

        public Violation? Evaluate(RadarObservation observation)
        {
            if (!observation.SeatbeltFastened)
            {
                return new Violation("Seatbelt not fastned", Fee);
            }
            return null;
        }
    }

    public class SpeedLimitRule : IViolationRule
    {
        private readonly CarType _carType;
        private readonly int _maxSpeed;
        private readonly double _fee;

        public SpeedLimitRule(CarType carType, int maxSpeed, double fee)
        {
            _carType = carType;
            _maxSpeed = maxSpeed;
            _fee = fee;
        }

        public string RuleName => $"SpeedLimitRule[{_carType} > {_maxSpeed}]";

        public Violation? Evaluate(RadarObservation observation)
        {
            if (observation.CarType == _carType && observation.Speed > _maxSpeed)
            {
                string desc = $"speed of {observation.Speed} exceeded max allowed {_maxSpeed}";
                return new Violation(desc, _fee);
            }
            return null;
        }
    }

    public class Fine
    {
        public string PlateNumber { get; }
        public double TotalAmount { get; }
        public List<Violation> Violations { get; }

        public Fine(string plateNumber, double totalAmount, List<Violation> violations)
        {
            PlateNumber = plateNumber;
            TotalAmount = totalAmount;
            Violations = violations;
        }
    }

    public class QuRadar
    {
        private readonly List<IViolationRule> _rules;
        private readonly List<Fine> _issuedFines = new();
        private readonly Dictionary<string, int> _violatedRuleCounts = new();

        public QuRadar(List<IViolationRule> rules)
        {
            _rules = new List<IViolationRule>(rules);
        }

        public void AddRule(IViolationRule rule)
        {
            _rules.Add(rule);
        }

        public Fine? ProcessObservation(RadarObservation observation)
        {
            var violations = new List<Violation>();

            foreach (var rule in _rules)
            {
                var violation = rule.Evaluate(observation);
                if (violation != null)
                {
                    violations.Add(violation);
                    _violatedRuleCounts[rule.RuleName] =
                        _violatedRuleCounts.GetValueOrDefault(rule.RuleName, 0) + 1;
                }
            }

            if (violations.Count == 0)
            {
                return null;
            }

            double total = violations.Sum(v => v.Fee);
            var fine = new Fine(observation.PlateNumber, total, violations);
            _issuedFines.Add(fine);
            PrintFine(fine);
            return fine;
        }

        private static void PrintFine(Fine fine)
        {
            Console.WriteLine($"Traffic for car {fine.PlateNumber}");
            Console.WriteLine($"Total amount: {(int)fine.TotalAmount} EGP");
            Console.WriteLine("Violations:");
            foreach (var v in fine.Violations)
            {
                Console.WriteLine($"- {v.Description} : {(int)v.Fee} EGP");
            }
        }

        public Dictionary<string, double> GetAllPossibleFines()
        {
            var result = new Dictionary<string, double>();
            foreach (var fine in _issuedFines)
            {
                result[fine.PlateNumber] = result.GetValueOrDefault(fine.PlateNumber, 0) + fine.TotalAmount;
            }
            return result;
        }

        public Dictionary<string, int> GetAllViolatedRules()
        {
            return new Dictionary<string, int>(_violatedRuleCounts);
        }
    }

    public static class Program
    {
        public static void Main()
        {
            var rules = new List<IViolationRule>
            {
                new SeatbeltRule(),
                new SpeedLimitRule(CarType.Truck, 60, 300),
                new SpeedLimitRule(CarType.Private, 80, 300),
                new SpeedLimitRule(CarType.Bus, 70, 300),
            };

            var radar = new QuRadar(rules);

            var observations = new List<RadarObservation>
            {
                new("ABC1234", DateTime.Today, CarType.Private, 94, false),
                new("XYZ777",  DateTime.Today, CarType.Truck,   55, true),
                new("TRK555",  DateTime.Today, CarType.Truck,   75, true),
                new("BUS111",  DateTime.Today, CarType.Bus,     65, false),
            };

            foreach (var obs in observations)
            {
                radar.ProcessObservation(obs);
                Console.WriteLine();
            }

            Console.WriteLine("=== All possible fines ===");
            foreach (var (plate, total) in radar.GetAllPossibleFines())
            {
                Console.WriteLine($"{plate} -> {(int)total} EGP");
            }

            Console.WriteLine();
            Console.WriteLine("=== Violated rules count ===");
            foreach (var (ruleName, count) in radar.GetAllViolatedRules())
            {
                Console.WriteLine($"{ruleName} : {count}");
            }
        }
    }
}
