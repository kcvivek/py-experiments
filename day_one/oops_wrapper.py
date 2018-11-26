#!/usr/bin/python3

from employee import (
	Employee, 
	Tester, 
	Manager
	)

import sys
import datetime
import argparse
import time

if sys.version_info[0] < 3:
	print("This script is compatible with python3.x only")
	sys.exit(1)


parser = argparse.ArgumentParser(description="Manupulate the Employee class for learning properties & methods")
parser.add_argument('-s', '--string', metavar='', help="String seperated by - from which employee to be created")
# parser.add_argument('-l', '--length', metavar='', type=int, required=True, help="Just a dummply length")
group = parser.add_mutually_exclusive_group()
group.add_argument('-v', '--verbose', action='store_true', help='Print verbose output')
group.add_argument('-q', '--quite', action='store_true', help='run in quite mode')

args = parser.parse_args()


emp1 = Employee('Vivek', 'KC', 131960, 400000)
emp2 = Employee('Subi', 'Vivek', 290018, 30000)


#############################################################################

print ("Today is", time.strftime('%c'))
# print(emp1)

print (emp1.fullname)

emp1.update_name('Vishak Dev')

print (emp1.fullname)

tester1 = Tester('Hashmi', 'Jose', 190018, 40000, 'Manual', 'Cloud')

print (tester1.email)

# print (help(Tester))

mgr1 = Manager('Sanjiv', 'Keswani', 10018, 940000, 'Cloud', [emp1])

mgr1.add_emp(emp2)

mgr1.list_emps()

print (mgr1.salary)

mgr1.salary_raise()
print (mgr1.salary)

print (emp1.salary)
# Employee.raise_amount(1.08)
emp1.salary_raise()
print (emp1.salary)


emp4_str = ('Rane-A-1315-700000')

emp4 = Employee.from_string(emp4_str)

print (emp4.fullname, ":", emp4.email)
print ('{} {} {}'.format(emp4.fullname, ':', emp4.email))



date = datetime.date(2017, 7, 9)
print ("Date is %s and is_working day is: " % date, Employee.is_workingday(date))

print (date.weekday())



