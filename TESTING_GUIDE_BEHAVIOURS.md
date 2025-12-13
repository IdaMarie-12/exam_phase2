# Testing Behaviour Strategies: Complete Guide

## Table of Contents
1. [Why We Test Behaviours](#why-we-test-behaviours)
2. [Testing Approach Overview](#testing-approach-overview)
3. [Core Testing Concepts](#core-testing-concepts)
4. [Mock Objects Explained](#mock-objects-explained)
5. [Our Test Structure](#our-test-structure)
6. [Step-by-Step Breakdown](#step-by-step-breakdown)
7. [Running the Tests](#running-the-tests)
8. [TEORI: Unittest, Mocking og Patching](#teori-unittest-mocking-og-patching)

---

## Why We Test Behaviours

### The Problem Without Tests

Your simulation has **three behaviour strategies** that drive critical decisions:
- **GreedyDistanceBehaviour**: "Accept if pickup is close"
- **EarningsMaxBehaviour**: "Accept if money is good"
- **LazyBehaviour**: "Accept if I'm rested AND pickup is close"

**Without tests, problems like these go unnoticed:**
```
❌ Threshold bug: max_distance=5.0 but code checks < instead of <=
❌ Logic bug: LazyBehaviour checks OR instead of AND
❌ Type bug: Code crashes if someone passes wrong type
❌ Boundary bug: off-by-one error at distance=5.0
```

### What Happens with Tests

**With comprehensive tests:**
```
✅ Type validation caught immediately
✅ All edge cases verified (zero distance, boundary conditions)
✅ Each behaviour strategy tested independently
✅ Future changes don't break existing logic
```

---

## Testing Approach Overview

### Three Testing Levels (Pyramid)

```
        △ Integration Tests (Light)
       △△ Mock Tests (Heavy)
      △△△ Unit Tests (Core)
```

**What we're doing:**
1. **Unit Tests** - Test each behaviour in complete isolation
2. **Mock Tests** - Replace Driver/Offer objects with fakes (Mocks)
3. **Integration Tests** - Light integration with real Point class

**Why this order matters:**
- Start simple (unit tests) → Build complexity (mocks) → Verify integration
- If unit tests fail, know it's the behaviour itself
- If mocks pass but integration fails, know it's the interaction

---

## Core Testing Concepts

### 1. What is a Unit Test?

A **unit test** checks ONE component in isolation.

```
Component Being Tested: GreedyDistanceBehaviour.decide()
Input: driver, offer, time
Output: bool (True/False)
Test: Does it return True when distance <= threshold?
```

**Key principle**: Test the behaviour, nothing else.

### 2. What is a Mock Object?

A **mock** is a fake object that pretends to be real.

```python
# Real world:
driver = Driver(position=Point(0, 0), ...)  # Complex initialization
offer = Offer(driver, request, ...)          # Depends on other objects
# Cost: Slow, lots of dependencies

# Mock world:
driver = Mock()
driver.position = Point(0, 0)
# Cost: Fast, isolated, no dependencies
```

**Why mocks?**
- Your behaviour only needs Driver.position, not whole Driver class
- Mocks let you provide ONLY what's needed
- Tests run instantly (no full simulation)
- Tests are deterministic (same result every time)

### 3. What is Patching?

**Patching** replaces a real function with a fake one.

```python
# Real: random.choice() - unpredictable
with patch('random.choice') as mock_choice:
    mock_choice.return_value = "always accept"
    # Now random.choice is predictable for testing
```

**When to patch:**
- Random numbers (need determinism)
- Datetime (need control over time)
- External API calls (need to avoid real requests)

**We don't patch in this test file** (not needed for behaviours), but the pattern is shown in TESTING_STRATEGY.md.

---

## Mock Objects Explained

### Creating a Mock

```python
from unittest.mock import Mock

# Create a fake Driver
driver = Mock()

# Give it attributes
driver.position = Point(0, 0)
driver.idle_since = 5

# Access them like normal
print(driver.position)  # Point(0, 0)
```

### Configuring Return Values

```python
# Create a fake Offer
offer = Mock()

# Configure what reward_per_time() returns
offer.reward_per_time = Mock(return_value=15.0)

# Call it
result = offer.reward_per_time()  # Returns 15.0
```

### Verifying Mock Was Used

```python
# Create mock
my_mock = Mock()

# Use it
my_mock.some_method()
my_mock.some_method()

# Verify it was called twice
my_mock.some_method.assert_called()          # Was it called?
my_mock.some_method.assert_called_once()     # Called exactly once?
my_mock.some_method.assert_called_with(...)  # Called with args?
```

**In our tests**: We just create mocks with attributes. We don't verify they're called (simpler).

---

## Our Test Structure

### File: test_behaviours.py

```
test_behaviours.py
├── TestGreedyDistanceBehaviour (30+ tests)
│   ├── setUp() - Create mock objects
│   ├── Normal Cases
│   │   ├── test_accept_offer_at_exact_threshold
│   │   ├── test_accept_offer_within_distance
│   │   ├── test_reject_offer_beyond_distance
│   │   └── test_accept_zero_distance_offer
│   ├── Edge Cases
│   │   ├── test_very_large_distance_rejected
│   │   ├── test_small_threshold_rejects_nearby
│   │   └── test_large_threshold_accepts_far
│   └── Type Validation
│       ├── test_type_error_invalid_driver_type
│       ├── test_type_error_invalid_offer_type
│       ├── test_type_error_invalid_time_type
│       └── test_type_error_time_is_float
│
├── TestEarningsMaxBehaviour (20+ tests)
│   ├── setUp() - Create mock objects
│   ├── Normal Cases
│   ├── Edge Cases
│   └── Type Validation
│
├── TestLazyBehaviour (25+ tests)
│   ├── setUp() - Create mock objects
│   ├── Both Conditions Met
│   ├── Single Condition Fails
│   ├── Edge Cases (Boundary conditions)
│   └── Type Validation
│
└── TestBehaviourIntegration (Light integration)
    ├── Real Point class + Mocked Driver/Offer
    └── Verify real distance calculation works
```

### Test Naming Convention

```python
def test_<behavior>_<condition>_<expected_result>():
    """
    Test: <One-line description>
    
    Input: ...
    Expected: ...
    Why: ...
    """
```

**Example:**
```python
def test_accept_offer_at_exact_threshold(self):
    """Test: Accept offer when pickup distance equals max_distance.
    
    Input: distance = 5.0 (exactly at threshold)
    Expected: True (accept)
    
    Why: The condition is distance <= threshold, so equality should accept.
    """
```

---

## Step-by-Step Breakdown

### Step 1: Import Required Modules

```python
import unittest                          # Testing framework
from unittest.mock import Mock, patch    # Mock objects
from phase2.behaviours import (          # Classes to test
    GreedyDistanceBehaviour,
    EarningsMaxBehaviour,
    LazyBehaviour,
    LAZY_MAX_PICKUP_DISTANCE
)
from phase2.point import Point           # Real class for coordinates
```

**Why each import:**
- `unittest`: Provides TestCase class and assertions
- `Mock`: Creates fake objects
- `patch`: Replaces real functions (not used here but available)
- Classes: What we're testing
- `Point`: Real class we use in mocks

---

### Step 2: Create Test Class

```python
class TestGreedyDistanceBehaviour(unittest.TestCase):
    """Test suite for GreedyDistanceBehaviour strategy."""
```

**Key points:**
- Inherit from `unittest.TestCase`
- One test class per behaviour
- All test methods start with `test_`

---

### Step 3: Set Up Fixtures (Mock Objects)

```python
def setUp(self):
    """Create reusable mock objects for each test."""
    # Create the behaviour being tested
    self.behaviour = GreedyDistanceBehaviour(max_distance=5.0)
    
    # Create real Point (no mocking needed - pure math)
    self.driver_position = Point(0, 0)
    
    # Mock the Driver object
    self.driver = Mock()
    self.driver.position = self.driver_position
    
    # Mock the Request with pickup location
    self.request = Mock()
    self.request.pickup = Point(3, 4)
    
    # Mock the Offer
    self.offer = Mock()
    self.offer.request = self.request
```

**setUp() runs before EVERY test method**

Benefits:
1. **DRY (Don't Repeat Yourself)**: Mocks created once, reused
2. **Consistency**: Every test starts with same state
3. **Clarity**: Fixtures visible in one place
4. **Isolation**: Test can modify mocks without affecting others

---

### Step 4: Write Test Methods

```python
def test_accept_offer_at_exact_threshold(self):
    """Test: Accept offer when distance equals threshold."""
    # Arrange: Data is ready from setUp()
    # (distance = 5.0 from Point(3,4) to Point(0,0))
    
    # Act: Call the behaviour
    result = self.behaviour.decide(self.driver, self.offer, time=0)
    
    # Assert: Check result is correct
    self.assertTrue(result, "Should accept offer at exact threshold")
```

**AAA Pattern (Arrange-Act-Assert):**
1. **Arrange**: Set up test data (done in setUp)
2. **Act**: Call the code being tested
3. **Assert**: Check the result

**This pattern makes tests readable and maintainable.**

---

### Step 5: Test Multiple Cases

#### Normal Cases (Happy Path)
```python
def test_accept_offer_within_distance(self):
    """Test normal case: distance less than threshold."""
    self.request.pickup = Point(3, 0)  # Distance = 3.0
    result = self.behaviour.decide(self.driver, self.offer, time=0)
    self.assertTrue(result)
```

#### Edge Cases (Boundary Conditions)
```python
def test_accept_zero_distance_offer(self):
    """Test boundary: distance = 0."""
    self.request.pickup = Point(0, 0)
    result = self.behaviour.decide(self.driver, self.offer, time=0)
    self.assertTrue(result)

def test_reject_offer_beyond_distance(self):
    """Test boundary: distance > threshold."""
    self.request.pickup = Point(10, 0)
    result = self.behaviour.decide(self.driver, self.offer, time=0)
    self.assertFalse(result)
```

#### Type Validation
```python
def test_type_error_invalid_driver_type(self):
    """Test that TypeError is raised for wrong type."""
    with self.assertRaises(TypeError) as context:
        self.behaviour.decide("invalid_driver", self.offer, time=0)
    self.assertIn("requires Driver", str(context.exception))
```

**Pattern for exception testing:**
```python
with self.assertRaises(SomeError) as context:
    # Code that should raise exception
    function_call()

# Optionally verify error message
self.assertIn("expected text", str(context.exception))
```

---

### Step 6: Understand LazyBehaviour's AND Logic

**This is the trickiest test case:**

```python
def test_reject_not_idle_enough(self):
    """Reject if idle FAILS (even if distance is OK)."""
    # idle_duration = 5 (< 10 needed) → FAILS
    # distance = 2.0 (< 5.0) → OK
    # AND: FAIL ∧ OK = FAIL
    result = self.behaviour.decide(self.driver, self.offer, time=5)
    self.assertFalse(result)

def test_reject_distance_too_far(self):
    """Reject if distance FAILS (even if idle is OK)."""
    # idle_duration = 20 (>= 10) → OK
    # distance = 6.0 (>= 5.0) → FAILS
    # AND: OK ∧ FAIL = FAIL
    self.request.pickup = Point(6, 0)
    result = self.behaviour.decide(self.driver, self.offer, time=20)
    self.assertFalse(result)
```

**Key insight**: AND is strict - BOTH must pass.

---

## Running the Tests

### Run All Tests in Verbose Mode

```bash
cd exam_phase2
python -m unittest test.test_behaviours -v
```

**Output:**
```
test_accept_offer_at_exact_threshold (test.test_behaviours.TestGreedyDistanceBehaviour) ... ok
test_accept_offer_within_distance (test.test_behaviours.TestGreedyDistanceBehaviour) ... ok
test_reject_offer_beyond_distance (test.test_behaviours.TestGreedyDistanceBehaviour) ... ok
...

----------------------------------------------------------------------
Ran 75 tests in 0.023s

OK
```

### Run Specific Test Class

```bash
python -m unittest test.test_behaviours.TestGreedyDistanceBehaviour -v
```

### Run Specific Test Method

```bash
python -m unittest test.test_behaviours.TestGreedyDistanceBehaviour.test_accept_zero_distance_offer -v
```

### Run from Python File

```bash
python test/test_behaviours.py
```

---

## Best Practices Applied

### 1. **Test One Thing Per Test**
❌ Bad:
```python
def test_behaviour(self):
    result1 = self.behaviour.decide(driver, offer, time=0)
    result2 = self.behaviour.decide(driver, offer, time=10)
    self.assertTrue(result1)
    self.assertTrue(result2)
```

✅ Good:
```python
def test_accept_at_time_zero(self):
    result = self.behaviour.decide(driver, offer, time=0)
    self.assertTrue(result)

def test_accept_at_time_ten(self):
    result = self.behaviour.decide(driver, offer, time=10)
    self.assertTrue(result)
```

**Why**: If one fails, you know exactly which case failed.

### 2. **Use Descriptive Test Names**
❌ Bad: `test_case1()`
✅ Good: `test_accept_offer_at_exact_threshold()`

### 3. **Include Docstrings**
```python
def test_something(self):
    """Test: <What you're testing>
    
    Input: <What you provide>
    Expected: <What should happen>
    Why: <Why this matters>
    """
```

### 4. **Arrange-Act-Assert Pattern**
```python
def test_example(self):
    # Arrange (setup)
    # Act (call code)
    # Assert (verify)
```

### 5. **Test Edge Cases**
- Zero values
- Boundary conditions (==, <, >, <=, >=)
- Negative values
- Very large values
- Type errors

### 6. **Use Fixtures (setUp)**
Don't repeat mock creation in each test.

### 7. **Mock Only What's Needed**
✅ Mock Driver/Offer (complex, vary per test)
✅ Use real Point (simple, pure math)

---

## Summary

### Why This Approach Is Good

| Aspect | Benefit |
|--------|---------|
| **Unit Tests** | Isolate behaviour logic, catch bugs immediately |
| **Mocks** | No dependencies, fast execution, deterministic |
| **Type Validation** | Catch type errors before production |
| **Edge Cases** | Cover boundary conditions, off-by-one errors |
| **Descriptive Names** | Clear what's being tested |
| **Docstrings** | Why test matters, not just what |
| **AAA Pattern** | Readable test structure |

### Test Counts

```
TestGreedyDistanceBehaviour:   11 tests
TestEarningsMaxBehaviour:       12 tests
TestLazyBehaviour:             16 tests
TestBehaviourIntegration:       2 tests
─────────────────────────────────────
Total:                         41 tests
```

### Next Steps

1. **Run the tests**:
   ```bash
   python -m unittest test.test_behaviours -v
   ```

2. **Fix any failures** - They indicate bugs in behaviours.py

3. **Maintain tests** - When you change behaviour logic, tests should still pass

4. **Add more tests** - If you find a bug, write a test that catches it first

5. **Test other classes** - Apply same approach to Point, Request, Driver, etc.

---

## Quick Reference: unittest Assertions

| Assertion | Checks | Example |
|-----------|--------|---------|
| `assertTrue(x)` | x is True | `self.assertTrue(result)` |
| `assertFalse(x)` | x is False | `self.assertFalse(result)` |
| `assertEqual(a, b)` | a == b | `self.assertEqual(distance, 5.0)` |
| `assertNotEqual(a, b)` | a != b | `self.assertNotEqual(result, None)` |
| `assertRaises(Error)` | Exception raised | `with self.assertRaises(TypeError):` |
| `assertIn(a, b)` | a in b | `self.assertIn("error", message)` |
| `assertIsInstance(a, b)` | isinstance(a, b) | `self.assertIsInstance(obj, MyClass)` |
| `assertIsNone(x)` | x is None | `self.assertIsNone(result)` |

---

## Questions You Might Ask

### Q: Why mock Driver/Offer instead of using real ones?
A: Real classes have complex initialization with many dependencies. Mocks are simpler, faster, and more focused.

### Q: Why test type validation?
A: Your code explicitly checks types and raises TypeError. These are important contracts that should be tested.

### Q: What about testing the Policy or Simulation?
A: Those require heavier mocking/patching. Behaviours are simpler - perfect starting point. See TESTING_STRATEGY.md for those.

### Q: Can I modify these tests?
A: Yes! Tests should evolve with code. If you change behaviour logic, update tests. If you find a bug, write a test first.

### Q: What's considered "good" test coverage?
A: For behaviour classes, >80% is excellent. We're aiming for 100% by testing all cases.

---

## Conclusion

This test file demonstrates **professional testing practices**:
- ✅ Unit testing in isolation
- ✅ Mock objects for dependencies
- ✅ Type validation testing
- ✅ Edge case coverage
- ✅ Clear naming and documentation
- ✅ AAA pattern for readability

Use this as a template for testing other components (Point, Request, Driver, Simulation, etc.).

---

# TEORI: Unittest, Mocking og Patching (For Nybegyndere)

## Hvad er Unittest?

### Simpel Forklaring
En **unittest** er en test der checker at ét lille stykke kode virker rigtigt **helt af sig selv**.

### Analogi: Biltest
Forestil dig at teste en bils motor før den bygges ind i bilen:
- ❌ **Uden unittest**: Byg hele bilen, kør den, hvis den går i stykker ved du ikke om det er motoren, bremserne eller transmissionen
- ✅ **Med unittest**: Test kun motoren isoleret. Hvis den går i stykker ved du præcis hvad der er galt

### Real Eksempel fra Dit Kode

```python
# Hvad vi tester:
behaviour = GreedyDistanceBehaviour(max_distance=5.0)
result = behaviour.decide(driver, offer, time)

# Unittest: Returnerer den True når distance <= 5.0?
self.assertTrue(result)

# Unittest: Returnerer den False når distance > 5.0?
self.assertFalse(result)
```

### Hvad en God Unittest Skal Være

- ✅ Test KUN ÉN ting (en metode)
- ✅ Være hurtig (mindre end 1 sekund)
- ✅ Ikke afhænge af anden kode
- ✅ Give samme resultat hver gang (deterministisk)
- ✅ Have et navn der forklarer hvad den tester

### Hvorfor Unittests Er Vigtige

```
❌ Uden tests:
   - Bug i decide() går uopmærket hen
   - Tærskel logik kan være bagvendt (< istedet for <=)
   - Off-by-one fejl ved grænser (fx distance=5.0)
   - Type checking kan være brudt

✅ Med tests:
   - Bugs opdages straks
   - Fremtidige ændringer bryder ikke eksisterende logik
   - Tillid til at koden faktisk virker
   - Dokumentation af hvordan koden skal opføre sig
```

---

## Hvad er Mocking?

### Simpel Forklaring
En **mock** er et **falsk objekt** der opfører sig som et rigtigt objekt, men er meget enklere.

### Hvorfor Vi Skal Bruge Mocks

Når du tester `GreedyDistanceBehaviour.decide()` har den brug for:
- En rigtig `Driver` objekt (med position, idle_since, osv.)
- En rigtig `Offer` objekt (med request, reward, osv.)
- En rigtig `Request` objekt (med pickup og dropoff)
- En rigtig `Point` objekt (med distanceberegninger)

**Problemet:** At lave alle disse rigtige objekter er:
1. **Langsomt** - Masse initialization kode
2. **Kompliceret** - Hvert objekt afhænger af andre
3. **Skrøbeligt** - Hvis en ændres, går tests i stykker overalt
4. **Uforudsigeligt** - Tilfældig data kan blive genereret

### Mock-Løsningen

Istedet for rigtige objekter, lav **falske**:

```python
# Rigtig måde (kompliceret, langsom):
driver = Driver(
    id=1, 
    position=Point(0, 0), 
    idle_since=5,
    vehicle_type="car",
    rating=4.8,
    ...
)

# Mock måde (simpel, hurtig):
driver = Mock()
driver.position = Point(0, 0)  # Giv kun hvad vi skal bruge
driver.idle_since = 5
```

### Sådan Virker Mocks: Trin for Trin

```python
# Trin 1: Lav tom mock
driver = Mock()

# Trin 2: Tilføj attributter (den har dem ikke fra start!)
driver.position = Point(0, 0)
driver.idle_since = 5

# Trin 3: Brug den i test
distance = driver.position.distance_to(other_point)

# Trin 4: Resultat er forudsigeligt og hurtigt
```

### Real Eksempel: Greedy Behaviour Test

```python
def test_accept_offer_within_distance(self):
    # Arrange (Setup)
    behaviour = GreedyDistanceBehaviour(max_distance=5.0)
    
    # Lav falsk driver på origin
    driver = Mock()
    driver.position = Point(0, 0)  # Kun hvad vi skal bruge
    
    # Lav falsk offer med pickup 3 enheder væk
    offer = Mock()
    offer.request = Mock()
    offer.request.pickup = Point(3, 0)  # Pickup 3 enheder væk
    
    # Act (Kør testen)
    result = behaviour.decide(driver, offer, time=100)
    
    # Assert (Check resultat)
    self.assertTrue(result)  # Skal acceptere (3 <= 5)
```

### Mock med spec Parameter (Type Checking)

Pythons `isinstance()` funktion afviser plain Mocks:

```python
driver = Mock()
isinstance(driver, Driver)  # False! (Mock er ikke en Driver)

# Men med spec parameter:
driver = Mock(spec=Driver)
isinstance(driver, Driver)  # True! (Mock låtsas nu at være Driver)
```

**Hvorfor vi bruger det:** Behaviour klasser checker `isinstance(driver, Driver)`. Med `spec=Driver` passar mocks gennem denne check.

```python
def decide(self, driver, offer, time):
    if not isinstance(driver, Driver):
        raise TypeError("Not a Driver!")  # Afviser plain Mock()
    
    # Med Mock(spec=Driver), går denne check gennem ✅
```

### Hvad Mocks Kan Gøre

```python
# 1. Sæt attributter
mock.position = Point(0, 0)
mock.idle_since = 5

# 2. Sæt metoder til at returnere værdier
mock.reward_per_time = Mock(return_value=15.0)
mock.reward_per_time()  # Returnerer 15.0

# 3. Verify at de blev kaldt (avanceret)
mock.some_method.assert_called()
mock.some_method.assert_called_once()

# I vores tests: Vi bruger kun 1 og 2 (simpel mocking)
```

---

## Hvad er Patching?

### Simpel Forklaring
**Patching** erstatter midlertidigt en rigtig funktion med en falsk **under en test**.

### Hvorfor Patch?

Nogle ting er uforudsigelige:

```python
import random

# Rigtig kode (uforudsigelig):
choice = random.choice([1, 2, 3, 4, 5])  # Kan være hvad som helst!

# Test problem: Kan ikke teste alle muligheder
# Resultat ændrer sig hver gang - ikke deterministisk
```

**Patching løser det:** Erstat den tilfældige funktion med en kontrolleret falsk:

```python
from unittest.mock import patch

# Erstat random.choice med falsk der altid returnerer 1
with patch('random.choice') as mock_choice:
    mock_choice.return_value = 1
    
    choice = random.choice([1, 2, 3, 4, 5])
    assert choice == 1  # Altid 1, forudsigelig!
```

### Hvornår Man Skal Patch

Brug patching til ting du **ikke kan kontrollere**:

| Hvad | Hvorfor | Eksempel |
|------|---------|---------|
| **Random** | Uforudsigelig | `random.choice()`, `random.random()` |
| **Datetime** | Tiden ændrer sig | `datetime.now()`, `time.time()` |
| **Eksterne APIs** | Langsomt, kan fejle | Database kald, web requests |
| **File I/O** | Bieffekter | Læse filer, skrive logs |

### Patching Eksempel

```python
from unittest.mock import patch
from datetime import datetime

# Scenario: Test kode der afhænger af nutid
def should_accept_at_rush_hour():
    if datetime.now().hour >= 17:  # Efter 17:00
        return True
    return False

# Test med patching:
with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2023, 1, 1, 18, 0, 0)  # 18:00
    
    result = should_accept_at_rush_hour()
    assert result == True  # Forudsigelig!
```

### Hvorfor Vi Ikke Patcher i Denne Test File

Vores behaviour klasser er **deterministiske** (ingen random, datetime, eller eksterne kald):

```python
def decide(self, driver, offer, time):
    dist = driver.position.distance_to(offer.request.pickup)  # Ren matematik
    return dist <= self.max_distance  # Simpel sammenligning
```

Ingen tilfældige elementer = Ingen grund til at patche!

---

## Sammenligning: Unittest, Mocking og Patching

| Koncept | Hvad | Hvornår | Eksempel |
|---------|------|---------|---------|
| **Unittest** | Test framework, assertion metoder | Altid - test hver component | `self.assertTrue()`, `self.assertEqual()` |
| **Mocking** | Falske objekter der erstatter rigtige | Når test har afhængigheder | `Mock(spec=Driver)` til test af behaviour |
| **Patching** | Erstat funktioner midlertidigt | Når test usikre ting | `patch('random.choice')` for RNG |

### I Dette Projekt

- ✅ **Unittest**: Brugt meget (41 tests)
- ✅ **Mocking**: Brugt til Driver, Offer, Request objekter
- ❌ **Patching**: Ikke nødvendigt (behaviours er rene funktioner)

---

## Opsummering

### Unittest er vigtig fordi:
- Finder bugs før de går i produktion
- Dokumenterer hvordan kode skal virke
- Giver tillid til at ændringer ikke bryder noget
- Gør refactoring sikker

### Mocking er vigtig fordi:
- Isolerer koden du tester
- Gør tests hurtige
- Gør tests deterministiske
- Undgår afhængigheder der er svære at sætte op

### Patching er vigtig fordi:
- Kontrollerer uforudsigelige dele (random, datetime)
- Undgår external side effects (API kald, disk I/O)
- Gør tests pålidelige og repeatbare

**Tilsammen** giver disse tre teknikker dig evnen til at skrive tests der er:
- ✅ Hurtige
- ✅ Pålidelige
- ✅ Nemme at vedligeholde
- ✅ Nemmelige at forstå
