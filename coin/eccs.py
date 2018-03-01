import collections
import random
from ext_euclid import inverse_modulo
from hashlib import sha256
from os import urandom

EllipticCurve=collections.namedtuple('EllipticCurve','name p a b g n h')

curve=EllipticCurve('secp256k1',
    # Field characteristic.
    p=0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f,
    # Curve coefficients.
    a=0,
    b=7,
    # Base point.
    g=(0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798,
       0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8),
    # Subgroup order.
    n=0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141,
    # Subgroup cofactor.
h=1,)

def is_on_curve(point):
    if point is None:
        return True
    x,y=point
    return (y*y-x*x*x-curve.a*x-curve.b)%curve.p==0

def neg(point):
    x,y=point
    assert is_on_curve(point)
    if point is None:
        return None
    result=(x,-y%curve.p)
    assert is_on_curve(result)
    return result 

def addition(point1,point2):
    # Check if points are on curve
    assert is_on_curve(point1)
    assert is_on_curve(point2)

    if point1 is None:
        return point2
    if point2 is None:
        return point1

    # Assigning point tuple to respective co-ordinates
    xp,yp=point1
    xq,yq=point2

    # Case when point2 = -point1
    # point1 + point2 = 0
    if xp==yq and yp!=yq:
        return None

    if xp!=xq:
        m=(yp-yq)*inverse_modulo(xp-xq,curve.p)
    elif xp==xq:
        m=(3*xp*xp+curve.a)*inverse_modulo(2*yp,curve.p)
    xr=(m*m-xp-xq)%curve.p
    yr=(yp+m*(xr-xp))%curve.p
    result=(xr,-yr)
    assert is_on_curve(result)

    return result

def mult(k,point):
    assert is_on_curve(point)

    if k%curve.n==0 or point is None:
        return None

    if k<0:
        return mult(-k,neg(point))

    result=None
    double_n=point

    while k:
        if k & 1:
            result=addition(result,double_n)
        double_n=addition(double_n,double_n)
        k=k>>1
    
    assert is_on_curve(result)

    return result

def make_key():
    # Generates public and private key
    private_key=random.randint(1,curve.n-1)
    public_key=mult(private_key,curve.g)
    return private_key,public_key


def hash_message(message):
    message_hash = sha256(message).hexdigest()
    m = int(message_hash,16)
    return m

def sign_message(private_key, message):
    z = hash_message(message)
    r = 0
    s = 0
    while not r or not s:
        k = int(urandom(64).encode('hex'),16) % curve.n
        x, y = mult(k, curve.g)
        r = x % curve.n
        s = ((z + r * private_key) * inverse_modulo(k, curve.n)) % curve.n

    return (r, s)

def verify_signature(public_key, message, signature):
    z = hash_message(message)
    r, s = signature
    w = inverse_modulo(s, curve.n)
    u1 = (z * w) % curve.n
    u2 = (r * w) % curve.n
    x, y = addition(mult(u1, curve.g),mult(u2, public_key))
    if (r % curve.n) == (x % curve.n):
        return True
    else:
        return False


# print "Curve: ",curve.name

# Generating private and public key pair
pr_key,pub_key=make_key()
# print "Private key: ",hex(pr_key)
# print "Public key: (0x{:x},0x{:x})".format(pub_key[0],pub_key[1])


