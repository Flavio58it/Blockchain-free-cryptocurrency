def inverse_modulo(a,n):
    if a==0:
        raise ZeroDivisionError('Division by zero')

    if a<0:
        return n-inverse_modulo(-a,n)

    t=0;new_t=1;
    r=n;new_r=a;
    while new_r!=0:
        quotient=r/new_r
        t,new_t=new_t,t-quotient*new_t
        r,new_r=new_r,r-quotient*new_r
    if r>1:
        raise ValueError('{} has no multiplicative inverse modulo {}'.format(a,n))
    if t<0:
        t=t+n
    return t

"""a=int(raw_input("a:"))
n=int(raw_input("n:"))
print "multiplicative inverse modulo of {},{} is {}".format(a,n,inverse_modulo(a,n))
"""
