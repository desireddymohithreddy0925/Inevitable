from buggy import add_numbers, Calculator
import time

def test_add_numbers_pass():
    # Intentional bug in buggy.py: subtracts instead of adding. 
    # This assert will fail, creating a failed test case.
    assert add_numbers(2, 3) == 5

def test_calculator_pass():
    # This will pass
    calc = Calculator()
    assert calc.multiply(2, 3) == 6

def test_timeout():
    # This will time out if limit is 1s
    time.sleep(2)
    assert True
