class Product:
    def __init__(self, name, description, price, category_id):
        self.name = name
        self.description = description
        self.price = price
        self.category_id = category_id

    def save(self):
        # Code to save the product to the database
        pass

    @classmethod
    def get_by_id(cls, product_id):
        # Code to get a product by its ID
        pass

    @classmethod
    def get_all(cls):
        # Code to get all products
        pass

    @classmethod
    def get_by_category(cls, category_id):
        # Code to get products by category
        pass

    def update(self, **kwargs):
        # Code to update product attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def delete(self):
        # Code to delete the product from the database
        pass
