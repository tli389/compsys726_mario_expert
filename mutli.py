import subprocess

# The UPI value to use
upi = 'tli389'  # Replace with the actual UPI value you want to use

# Number of times to run the command
num_iterations = 1  # Replace with the desired number of iterations

for i in range(num_iterations):
    # Construct the command
    command = f'python run.py --upi {upi}'
    
    # Run the command
    print(f'Running iteration {i+1}/{num_iterations}: {command}')
    subprocess.run(command, shell=True)