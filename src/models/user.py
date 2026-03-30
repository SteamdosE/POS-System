class User:
    def __init__(self, username, password, email, role):
        self.username = username
        self.password = password
        self.email = email
        self.role = role

    def save(self):
        # code to save user to the database
        pass

    @classmethod
    def get_by_id(cls, user_id):
        # code to retrieve user by ID from the database
        pass

    @classmethod
    def get_by_username(cls, username):
        # code to retrieve user by username from the database
        pass

    @classmethod
    def get_all(cls):
        # code to retrieve all users from the database
        pass

    def update(self):
        # code to update user in the database
        pass

    def delete(self):
        # code to delete user from the database
        pass