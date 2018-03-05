import collections
import random
from ext_euclid import inverse_modulo
from hashlib import sha256
from os import urandom

#EllipticCurve=collections.namedtuple('EllipticCurve','name p a b g n h')

class ellipticCurve(object):
    def __init__(self):
        # Field characteristic.
        self.p=0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f
        # Curve coefficients.
        self.a=0
        self.b=7
        # Base point.
        self.g=(0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798,0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8)
        # Subgroup order.
        self.n=0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
        # Subgroup cofactor.
        self.h=1

    '''curve=EllipticCurve('secp256k1',
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
    h=1,)'''
    def is_on_curve(self, point):
        if point is None:
            return True
        x,y=point
        return (y*y-x*x*x-self.a*x-self.b)%self.p==0

    def neg(self,point):
        assert self.is_on_curve(point)
        if point is None:
            return None
        x,y=point
        result=(x,-y%self.p)
        assert self.is_on_curve(result)
        return result 

    def addition(self,point1,point2):
        # Check if points are on curve
        assert self.is_on_curve(point1)
        assert self.is_on_curve(point2)

        if point1 is None:
            return point2
        if point2 is None:
            return point1

        # Assigning point tuple to respective co-ordinates
        xp,yp=point1
        xq,yq=point2

        # Case when point2 = -point1
        # point1 + point2 = 0
        if xp==xq and yp!=yq:
            return None

        if xp==xq:
            m=(3*xp*xp+self.a)*inverse_modulo(2*yp,self.p)
        else:
            m=(yp-yq)*inverse_modulo(xp-xq,self.p)
        xr=(m*m-xp-xq)%self.p
        yr=(yp+m*(xr-xp))%self.p
        result=(xr,-yr)
        assert self.is_on_curve(result)

        return result

    def mult(self,k,point):
        assert self.is_on_curve(point)

        if k%self.n==0 or point is None:
            return None

        if k<0:
            return self.mult(-k,neg(point))

        result=None
        double_n=point

        while k:
            if k & 1:
                result=self.addition(result,double_n)
            double_n=self.addition(double_n,double_n)
            k=k>>1
    
        assert self.is_on_curve(result)

        return result

    def make_key(self):
        # Generates public and private key
        private_key=random.randint(1,self.n-1)
        public_key=self.mult(private_key,self.g)
        return private_key,public_key


    def hash_message(self,message):
        message_hash = sha256(message).hexdigest()
        m = int(message_hash,16)
        return m

    def sign_message(self,private_key, message):
        z = self.hash_message(message)
        r = 0
        s = 0
        while not r or not s:
            k = int(urandom(64).encode('hex'),16) % self.n
            x, y = self.mult(k, self.g)
            r = x % self.n
            s = ((z + r * private_key) * inverse_modulo(k, self.n)) % self.n

        return (r, s)

    def verify_signature(self,public_key, message, signature):
        z = self.hash_message(message)
        r, s = signature
        w = inverse_modulo(s, self.n)
        u1 = (z * w) % self.n
        u2 = (r * w) % self.n
        x, y = self.addition(self.mult(u1, self.g),self.mult(u2, public_key))
        if (r % self.n) == (x % self.n):
            return True
        else:
            return False


# print "Curve: ",curve.name

# Generating private and public key pair
# pr_key,pub_key=make_key()
# print "Private key: ",hex(pr_key)
# print "Public key: (0x{:x},0x{:x})".format(pub_key[0],pub_key[1])


