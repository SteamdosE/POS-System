"""
Receipt Generation Module for POS System
"""
from datetime import datetime
from ..config import *

class Receipt:
    """Generate professional POS receipts"""
    
    def __init__(self, sale_id, items, subtotal, tax, total, discount=0, payment_method="cash"):
        self.sale_id = sale_id
        self.items = items
        self.subtotal = subtotal
        self.tax = tax
        self.total = total
        self.discount = discount
        self.payment_method = payment_method
        self.timestamp = datetime.now()
    
    def generate_text_receipt(self):
        """Generate text-based receipt for display/printing"""
        lines = []
        lines.append("=" * 50)
        lines.append("POS SYSTEM - RECEIPT".center(50))
        lines.append("=" * 50)
        lines.append("")
        
        # Store info
        lines.append("Store: Main Branch")
        lines.append(f"Date: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Receipt #: {self.sale_id}")
        lines.append("")
        
        # Items
        lines.append("-" * 50)
        lines.append(f"{'Item':<25} {'Qty':>8} {'Price':>16}")
        lines.append("-" * 50)
        
        for item in self.items:
            name = item['name'][:24]
            qty = item['qty']
            unit_price = item['price']
            total_price = qty * unit_price
            lines.append(f"{name:<25} {qty:>8} {total_price:>16.2f}")
        
        lines.append("-" * 50)
        lines.append(f"{'Subtotal':<34} {self.subtotal:>15.2f}")
        
        if self.discount > 0:
            lines.append(f"{'Discount':<34} {self.discount:>15.2f}")
        
        tax_label = f"Tax ({TAX_RATE*100:.0f}%)"
        lines.append(f"{tax_label:<34} {self.tax:>15.2f}")
        
        lines.append("=" * 50)
        lines.append(f"{'TOTAL':<34} {self.total:>15.2f}")
        lines.append("=" * 50)
        lines.append("")
        
        # Payment info
        lines.append(f"Payment Method: {self.payment_method.upper()}")
        lines.append("")
        lines.append("Thank you for your purchase!")
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    def generate_html_receipt(self):
        """Generate HTML receipt for printing/email"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .receipt {{ max-width: 400px; margin: 0 auto; border: 1px solid #000; padding: 20px; }}
                .header {{ text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 10px; }}
                .store-info {{ text-align: center; font-size: 12px; margin-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 5px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ font-weight: bold; }}
                .total {{ font-weight: bold; font-size: 16px; }}
                .footer {{ text-align: center; font-size: 12px; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="receipt">
                <div class="header">POS SYSTEM - RECEIPT</div>
                <div class="store-info">
                    <p>Store: Main Branch</p>
                    <p>Date: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Receipt #: {self.sale_id}</p>
                </div>
                
                <table>
                    <tr>
                        <th>Item</th>
                        <th>Qty</th>
                        <th>Price</th>
                    </tr>
        """
        
        for item in self.items:
            total_price = item['qty'] * item['price']
            html += f"""
                    <tr>
                        <td>{item['name']}</td>
                        <td>{item['qty']}</td>
                        <td>{total_price:.2f}</td>
                    </tr>
            """
        
        html += f"""
                </table>
                
                <table>
                    <tr>
                        <td>Subtotal</td>
                        <td>{self.subtotal:.2f}</td>
                    </tr>
        """
        
        if self.discount > 0:
            html += f"""
                    <tr>
                        <td>Discount</td>
                        <td>{self.discount:.2f}</td>
                    </tr>
            """
        
        html += f"""
                    <tr>
                        <td>Tax ({TAX_RATE*100:.0f}%)</td>
                        <td>{self.tax:.2f}</td>
                    </tr>
                    <tr class="total">
                        <td>TOTAL</td>
                        <td>{self.total:.2f}</td>
                    </tr>
                </table>
                
                <div class="footer">
                    <p>Payment: {self.payment_method.upper()}</p>
                    <p>Thank you for your purchase!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
