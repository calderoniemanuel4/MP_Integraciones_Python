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
TESTUSER7086514198906533797
WZvWOXxYCg
vendedor
TESTUSER5924716395395326701
LWeiGLVwJs
TEST-7590725045170040-061822-e3ee6e06388edfd03dc6eff3fd098172-67076163
APP_USR-7590725045170040-061822-19438305ec8057d306f2b59eefdc5aac-67076163
"""