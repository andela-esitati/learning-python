class Celsius:
    def __init__(self, temperature=0):
        self.set_temperature(temperature)

    def to_farenheit(self):
        return (self.get_temperature() * 1.8) + 32

    def get_temperature(self):
        return self._temperature

    def set_temperature(self, value):
        if value < -273:
            raise ValueError("this temperature doesnt exist")
        else:
            self._temperature = value


man = Celsius(30)
man1 = Celsius(-10)
print man.to_farenheit()
print man1.to_farenheit()
print man.__dict__
