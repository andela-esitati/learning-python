class Parent():
	def __init__(self,last_name,eye_color):
		print ("Parent constructor called")
		self.last_name = last_name
		self.eye_color = eye_color

billy_cyrus = Parent("Cyrus","blue")
print billy_cyrus.last_name

class Child(Parent):
	def __init__(self,last_name,eye_color,number_of_toys):
		print "Child constructor called"
		""" To initiliaze the values we are inheriting from class parent
		we should reuse class parent's __init__method """
		Parent.__init__(self,last_name,eye_color)
		# Initialize number of toys
		self.number_of_toys = number_of_toys

miley_cyrus = Child("Cyrus","blue",5)
print miley_cyrus.last_name
print miley_cyrus.number_of_toys