def sign_up():
    print(input("new account+: "))
    
    names = []
    passwords = []

    name = input("your name: ")
    password = input("your password: ")

    if len(password) < 8:
        print("Password not strong, it must be at least 8 characters.")
        sign_up()
        return
    else:
        print("Account created successfully.")

    names.append(name)
    passwords.append(password)

    def password_change():
        change_password = input("Change password? (yes/no): ").lower()

        if change_password == "yes":
            last_password = input("Your current password: ")

            if last_password == passwords[0]:
                new_password = input("Your new password: ")

                if len(new_password) < 8:
                    print("Your new password is not strong.")
                    password_change()
                else:
                    passwords[0] = new_password
                    print("Password changed successfully.")
            else:
                print("Incorrect current password.")

    password_change()

    def sign_out():
        exit_choice = input("Do you want to log out? (yes/no): ").lower()
        if exit_choice == "yes":
            print("Logged out. Goodbye!")

    sign_out()

sign_up() 
