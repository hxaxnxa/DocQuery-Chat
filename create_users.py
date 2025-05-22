from passlib.hash import sha256_crypt
import json

users = {
    "admin": sha256_crypt.hash("securepass123")
}
with open("users.json", "w") as f:
    json.dump(users, f)
print("users.json created with admin:securepass123")