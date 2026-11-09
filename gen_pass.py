from getpass import getpass

import bcrypt


if __name__ == "__main__":
    password = getpass("Prometheus password: ").encode("utf-8")
    if not 1 <= len(password) <= 72:
        raise SystemExit("Enter a password between 1 and 72 UTF-8 bytes.")
    print(bcrypt.hashpw(password, bcrypt.gensalt()).decode("ascii"))
