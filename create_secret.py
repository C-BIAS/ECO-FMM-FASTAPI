# Step 1: Import required module
import secrets

# Step 2: Generate a secret token using secrets.token_hex
new_secret_token = secrets.token_hex(32)

# Step 3: Output the generated token to console
print(f"Generated SECRET_TOKEN: {new_secret_token}")

# Save the generated token to .env file
with open('.env', 'w') as f:
    f.write(f"SECRET_TOKEN={new_secret_token}\n")
