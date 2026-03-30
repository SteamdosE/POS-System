class Payment:
    def __init__(self, sale_id, amount, payment_method):
        self.sale_id = sale_id
        self.amount = amount
        self.payment_method = payment_method

    def save(self):
        # Code to save the payment record in the database
        pass

    @classmethod
    def get_by_id(cls, payment_id):
        # Code to retrieve a payment record by its ID
        pass

    @classmethod
    def get_by_sale(cls, sale_id):
        # Code to retrieve payment records by sale ID
        pass

    @classmethod
    def get_all(cls):
        # Code to retrieve all payment records
        pass

    def update(self, amount=None, payment_method=None):
        # Code to update the payment record
        if amount:
            self.amount = amount
        if payment_method:
            self.payment_method = payment_method
        pass

    def delete(self):
        # Code to delete the payment record
        pass
