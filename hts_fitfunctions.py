import numpy as np
from scipy.special import erf

def affine(x, a):
    return a*x

def linear(x, a, b):
    return a*x+b

def norm_linear(x, a):
    return 1 - a*x
    
def log_linear(x, a, b):
    return a*np.log(x)+b

def quadratic(x, a, b, c):
    return a*np.pow(x, 2)+b*x+c

def quadratic2(x, a, b):
    return a*(x-20)**2+b*(x-20)+1

def cubic(x, a, b, c, d):
    return a*x**3+b*x**2+c*x+d

def cubic2(x, a, b, c):
    return a*(x-20)**3+b*(x-20)**2+c*(x-20)+1

def poly5(x, a, b, c, d, e):
    return a*x**4+b*x**3+c*x**2+d*x+e

def inverse(x, a, b, c, d):
    return b+a/(c*x+d)

def inverse_cubic(x, a, b, c):
    return a/(b*x**3) + c
    
def powerLaw(i, ic, n):
    return 2e-7*(i/ic)**n

def inverseExponential(temperature, a, b, c, t50):
    #return a*temperature*(1-1/(np.exp(b*(temperature-t50))+1))
    return a*temperature-c/(np.exp(b*(temperature-t50))+1)

def modified_erf(temperature, a, v0, Tc):
    return 0.5*v0*temperature*(erf(a*(temperature - Tc)) + 1)/Tc

def gaussian(x, a0, mu, sigma):
    return a0*np.exp(-.5*((x - mu)/sigma)**2)/(sigma*np.sqrt(2*np.pi))