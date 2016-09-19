import unittest

def calculate_addition_string(expression):
    numbers = expression.split('+')
    total = 0
    for number in numbers:
        total += int(number)
    return total

class TestAdditionMethods(unittest.TestCase):
    def test_only_zero(self):
        self.assertEqual(calculate_addition_string("0"),0)
        
    def test_zero_plus_zero(self):
        self.assertEqual(calculate_addition_string("0+0"),0)
        
    def test_only_one(self):
        self.assertEqual(calculate_addition_string("1"),1)

    def test_one_plus_one(self):
        self.assertEqual(calculate_addition_string("1+1"),2)
        
    def test_ten_plus_ten(self):
        self.assertEqual(calculate_addition_string("10+10"),20)

    def test_only_hundred(self):
        self.assertEqual(calculate_addition_string("100"),100)

    def test_hundred_plus_hundred(self):
        self.assertEqual(calculate_addition_string("100+100"),200)

    def negative_test_hundred_plus_hundred(self):
        self.assertEqual(calculate_addition_string("-100+-100"),-200)
        
if __name__ == '__main__':
    unittest.main()