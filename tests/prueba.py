from decimal import Decimal,ROUND_HALF_UP
amount = Decimal(1500)

# multiplier = Decimal(10) ** 2
# to_minor = int((amount * multiplier).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
# print (to_minor)
amount = Decimal(1500)
scale =2
print((Decimal(amount) / (Decimal(10) ** scale)))#.quantize(Decimal(10) ** -scale))

"""
comprador
TESTUSER1390167848358775668
xtpqnufUcK
vendedor
TESTUSER5924716395395326701
LWeiGLVwJs
"""