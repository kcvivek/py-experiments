class Employee(object):

	emp_raise = 1.02

	"""
	Initializes the object with these variables, attributes
	"""
	def __init__(self, firstname, lastname, id, salary):
		self.firstname = firstname
		self.lastname = lastname
		self.id = id
		self.salary = salary
		self.email = "{0}.{1}@example.com".format(firstname, lastname).lower()

	"""
	This helps to call this method like an attribute (that's without () )
	If this is not defined, to get the fullname, you have to execute emp1.fullname()
	Now, just emp1.fullname is enough
	"""
	@property
	def fullname(self):
		return "{0} {1}".format(self.firstname, self.lastname)

	def __repr__(self):
		"""
		Use to print your objects
		"""
		return "{0} {1} {2}".format(self.__class__, self.firstname, self.lastname)

	def __str__(self):
		"""
		This is a way to format objects, if you wanted to print it. 
		Got first priority over __repr__ (mean, if both defined, this gets precedence)
		"""
		return "This is for: {0} {1}".format(self.firstname, self.lastname)


	def update_name(self, name):
		first, last = name.split(' ')
		self.firstname = first
		self.lastname = last


	def salary_raise(self):
		self.salary = self.emp_raise * self.salary


	"""
	This decorator modifes the raise_amount defined in the present class (Employee)
	Call like: Employee.raise_amount(1.06)
	"""
	@classmethod
	def raise_amount(cls, amount):
		cls.emp_raise = amount


	"""
	This method modify the class capability (Employee)
	So, with this you can create a new employee from dash seperated string, like
	(Firstname-lastname-id-pay)
	"""
	@classmethod
	def from_string(cls, str):
		firstname, lastname, id, salary = str.split('-')
		return cls(firstname, lastname, id, salary)


	"""
	This method should be used wherever we don't refer to class name or instance name
	In below function we are not using any class or object defined in this module
	"""
	@staticmethod
	def is_workingday(day):
		if day.weekday() == 5 or day.weekday() == 6:
			return False
		else:
			return True


class Tester(Employee):
	def __init__(self, firstname, lastname, id, salary, type, dept):
		"""
		Let the parent class(Employee) handle the common attributes, don't need to duplicate
		This is helpful if you have __init__ for both the parent and child class
		Child class is going to inherit all the attributes, methods of parent class 
		(unless there is one locally defined)
		"""
		# Below format is only for python 3
		super().__init__(firstname, lastname, id, salary)
		
		# For python 2.x, it should be =>
		# super(Tester, self).__init__(firstname, lastname, id, salary)

		# Below works for both python 2.x and 3.x : rarely used though
		# Employee.__init__(self, firstname, lastname, id, salary)
		self.type = type
		self.dept = dept


class Manager(Employee):
	""" Override default raise amout"""
	emp_raise = 1.05

	def __init__(self, firstname, lastname, id, salary, dept, employees=None):
		super().__init__(firstname, lastname, id, salary)
		if employees is None:
			print("No employees initially")
			self.employees = []
		else:
			print("Adding", employees)
			self.employees = employees

	def add_emp(self, employee=None):
		self.employees.append(employee)

	def remove_emp(self, employee=None):
		self.employee.remove(employee) 


	def list_emps(self):
		if self.employees:
			print ('{} manages following employees'.format(self.fullname))
			for emp in self.employees:
				print('--', emp.fullname)
		else:
			print ('{} does not manage anybody yet'.format(self.fullname))


if __name__ == '__main__':
	print ("Sorry, this is a class file, you must import to use it")