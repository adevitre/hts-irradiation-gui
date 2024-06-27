import numpy as np

def affine(x, a):
    return a*x

def linear(x, a, b):
    return a*x+b

def square(x, a, b, c):
    return a*x**2+b*x+c

def square2(x, a, b):
    return a*(x-20)**2+b*(x-20)+1

def cubic(x, a, b, c, d):
    return a*x**3+b*x**2+c*x+d

def cubic2(x, a, b, c):
    return a*(x-20)**3+b*(x-20)**2+c*(x-20)+1

def poly5(x, a, b, c, d, e):
    return a*x**4+b*x**3+c*x**2+d*x+e

   
def sqrt(x, a=0.69975365, b=0.75392883, c=0.13455914, d=-0.01259732):
    return a*np.sqrt(c*x+d)+b

def inverse(x, a, b, c, d):
    return b+a/(c*x+d)

def powerLaw(i, ic, n):
    return 2e-7*(i/ic)**n

def inverseExponential(temperature, a, b, c, t50):
    #return a*temperature*(1-1/(np.exp(b*(temperature-t50))+1))
    return a*temperature-c/(np.exp(b*(temperature-t50))+1)

def gaussian(x, a0, mu, sigma):
    return a0*np.exp(-.5*((x - mu)/sigma)**2)/(sigma*np.sqrt(2*np.pi))