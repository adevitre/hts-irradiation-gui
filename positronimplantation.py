##
## Library for calculations related to positron spectroscopy
## @author Alexis Devitre
## @lastmod 2025/05/01
##

import pandas as pd, numpy as np
from scipy import constants, integrate
from importlib.resources import files

u = constants.atomic_mass

data_path = files('PAPER_SUPPLEMENTAL_INFORMATION').joinpath('4g_cc_Elemental_4term_exponentialCoefficients_vsDistance_um.csv')
dfC = pd.read_csv(data_path, usecols=[1,2,3,4,5,6,7,8,9, 10])

dfY = dfC[dfC.Element=='Yttrium']
dfBa = dfC[dfC.Element=='Barium']
dfCu = dfC[dfC.Element=='Copper']
dfO = dfC[dfC.Element=='Oxygen']

dfTi = dfC[dfC.Element=='Titanium']
dfS = dfC[dfC.Element=='Carbon']

def pip_Ti(x, mS=12., mfS=0.):
    
    mTi = 47.867*(1-mfS)
    mC = 2.267*mfS
    
    m = mTi + mS
    
    fTi = mTi/m
    fS = mS/m
    
    rho_k = 4        # g/cm3
    rho_Ti = 4.506   # g/cm3

    A = (dfY.a.values[0]*fTi + dfS.a.values[0]*fS)
    C = (dfY.c.values[0]*fTi + dfS.c.values[0]*fS)
    E = (dfY.e.values[0]*fTi + dfS.e.values[0]*fS)
    G = (dfY.g.values[0]*fTi + dfS.g.values[0]*fS)

    B = (dfY.b.values[0]*fTi + dfS.b.values[0]*fS)*(rho_Ti/rho_k)
    D = (dfY.d.values[0]*fTi + dfS.d.values[0]*fS)*(rho_Ti/rho_k)
    F = (dfY.f.values[0]*fTi + dfS.f.values[0]*fS)*(rho_Ti/rho_k)
    H = (dfY.h.values[0]*fTi + dfS.h.values[0]*fS)*(rho_Ti/rho_k)

    return A*np.exp(-B*x)+C*np.exp(-D*x)+E*np.exp(-F*x)+G*np.exp(-H*x)

def pip_YBCO(x):
    mY = 88.90585
    mBa = 2*137.327
    mCu = 3*63.55
    mO = 6.9*15.999

    m = mY+mBa+mCu+mO

    fY = mY/m
    fBa = mBa/m
    fCu = mCu/m
    fO = mO/m

    rho_k = 4      # g/cm3
    rho_YBCO = 6.3 # g/cm3

    A = (dfY.a.values[0]*fY + dfBa.a.values[0]*fBa + dfCu.a.values[0]*fCu + dfO.a.values[0]*fO)
    C = (dfY.c.values[0]*fY + dfBa.c.values[0]*fBa + dfCu.c.values[0]*fCu + dfO.c.values[0]*fO)
    E = (dfY.e.values[0]*fY + dfBa.e.values[0]*fBa + dfCu.e.values[0]*fCu + dfO.e.values[0]*fO)
    G = (dfY.g.values[0]*fY + dfBa.g.values[0]*fBa + dfCu.g.values[0]*fCu + dfO.g.values[0]*fO)

    B = (dfY.b.values[0]*fY + dfBa.b.values[0]*fBa + dfCu.b.values[0]*fCu + dfO.b.values[0]*fO)*(rho_YBCO/rho_k)
    D = (dfY.d.values[0]*fY + dfBa.d.values[0]*fBa + dfCu.d.values[0]*fCu + dfO.d.values[0]*fO)*(rho_YBCO/rho_k)
    F = (dfY.f.values[0]*fY + dfBa.f.values[0]*fBa + dfCu.f.values[0]*fCu + dfO.f.values[0]*fO)*(rho_YBCO/rho_k)
    H = (dfY.h.values[0]*fY + dfBa.h.values[0]*fBa + dfCu.h.values[0]*fCu + dfO.h.values[0]*fO)*(rho_YBCO/rho_k)

    return A*np.exp(-B*x)+C*np.exp(-D*x)+E*np.exp(-F*x)+G*np.exp(-H*x)