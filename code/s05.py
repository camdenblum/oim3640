# a product would cost $100, how much tax do we pay

product = 100
tax_rate = 0.0625
#tax = product * tax_rate


#print(f'the tax for a product which costs ${product} is ${tax}.')


#def calc_tax(price, tax_rate):
    """Calculate product tax based on given price and return the tax amount."""
    #tax = price * tax_rate
   # print(f'the tax for a product which costs ${price} is ${tax}.')
    #print(tax)
    #if the fucnction does not explicitly return any value, it would return none"
   # return(tax)

computer_price = 900
iphone_price = 1100
mass_rate = 0.0625
ny_rate = 0.0875

tax_computer = calc_tax(computer_price, mass_rate)
tax_iphone = calc_tax(iphone_price, ny_rate)

total_tax = calc_tax(computer_price, mass_rate) + calc_tax(iphone_price, ny_rate)
print(total_tax)






