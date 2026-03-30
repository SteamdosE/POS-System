class Customer:
    def __init__(self, name, email, phone):
        self.name = name
        self.email = email
        self.phone = phone

    def save(self):
        # Logic to save the customer data to a database
        pass

    @classmethod
    def get_by_id(cls, customer_id):
        # Logic to retrieve a customer by their ID from the database
        pass

    @classmethod
    def get_by_email(cls, email):
        # Logic to retrieve a customer by their email from the database
        pass

    @classmethod
    def get_all(cls):
        # Logic to retrieve all customers from the database
        pass

    def update(self):
        # Logic to update customer data in the database
        pass

    def delete(self):
        # Logic to delete the customer from the database
        pass