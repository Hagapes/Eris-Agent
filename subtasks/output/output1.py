
import random
import string

def generate_random_code():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return code

random_code = generate_random_code()
print(random_code)
