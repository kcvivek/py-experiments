
out = [0]*10000

def main():
	x = int(input("Enter a number: "))
	print(fib(x))

	#print(out)


def fib(num):

	if num <= 1:
		return num

	if (out[num-1] == 0):
		out[num-1] = fib(num-1)
	if (out[num-2] == 0):
		out[num-2] = fib(num-2)
	out[num] = out[num-2] + out[num-1]

	return out[num]



if __name__ == '__main__':
	main()

