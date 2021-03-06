#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
2D simulation of gaussian source using cylindrical polar coordinates.
"""

import sys

import scipy as sp
import matplotlib.pyplot as pl

# Number of cells in each coordinate
SIZE_R = 100
SIZE_PHI = 180  # cell separation must be 2 degrees
# Maximum number of iterations
MAXTIME = 1000
PPW = 20        # Points per wave of the ricker source

## Field matrix definitions ##

# Only z-component of E is present
E_z = sp.zeros((SIZE_R, SIZE_PHI))

# H-field matrices are defined mainly at "half-integral points".
H_r = sp.zeros((SIZE_R, SIZE_PHI))
H_phi = sp.zeros((SIZE_R-1, SIZE_PHI))

## Space steps and time step ##

delta_r = 1
delta_phi = 2
delta_t = 1

## Medium permittivity and permeability ##

EPSILON0 = 1 #8.854187817e-12
MU0 = 1 #4 * sp.pi * 1e-7
epsR = EPSILON0 * sp.ones((SIZE_R, SIZE_PHI))
muR = MU0 * sp.ones((SIZE_R, SIZE_PHI))

## Grid for plotting ##

grid = sp.mgrid[0:SIZE_R, 0:SIZE_PHI]

# Re-represent the grid values in cartesian coordinates
r = sp.array(grid[0], dtype=float)
r[0, :] = 0.000001
phi = 2 * grid[1]
gridx = r * sp.cos(sp.pi * phi / 180)
gridy = r * sp.sin(sp.pi * phi / 180)

## Coordinate-dependent scale factors ##

# We define the scale factors at *integral points*. Thus, the position of the
# scale factors does not coincide with *any* field point, because the fields
# are defined at points which are half-integral in at least one coordinate
h_r = sp.ones((SIZE_R, SIZE_PHI))
h_phi = r
h_z = sp.ones((SIZE_R, SIZE_PHI))

## Coefficients for update equations ##

# In this section, the notation cA_i_B_j is used to mean the coefficient of the
# j-component of B in the update equation for the i-component of A.
# The notation is reduced to cA_i_B where there is only one component of B in
# A_i's update equation.

# Coefficients for the H_r update
cH_r_H = sp.ones(H_r.shape)
H_r_h_phi = (h_phi[:, 1:] + h_phi[:, :-1]) / 2
H_r_h_phi = sp.hstack((H_r_h_phi, (h_phi[:, :1] + h_phi[:, -1:])/2))
H_r_muR = (muR[:, 1:] + muR[:, :-1]) / 2
H_r_muR = sp.hstack((H_r_muR, (muR[:, :1] + muR[:, -1:])/2))
cH_r_E_z = - delta_t / (H_r_muR * delta_phi * H_r_h_phi * h_z)

# Coefficients for the H_phi update
cH_phi_H = sp.ones(H_phi.shape)
H_phi_h_r = (h_r[1:, :] + h_r[:-1, :]) / 2
H_phi_h_z = (h_z[1:, :] + h_z[:-1, :]) / 2
H_phi_muR = (muR[1:, :] + muR[:-1, :]) / 2
cH_phi_E_z = delta_t / (H_phi_muR * delta_r * H_phi_h_r * H_phi_h_z)

# Coefficients for the E_z update
cE_z_E = sp.ones((E_z[1:-1, :]).shape)
# Linear interpolation
E_z_epsR = epsR[1:-1, :]
E_z_h_r = h_r[1:-1, :]
E_z_h_phi = h_phi[1:-1, :]
E_z_h_phi_fwd_avg = (h_phi[2:, :] + h_phi[1:-1, :]) / 2
E_z_h_phi_bwd_avg = (h_phi[1:-1, :] + h_phi[:-2, :]) / 2
cE_z_H_phi = delta_t / (E_z_epsR * delta_r * E_z_h_r * E_z_h_phi)
cE_z_H_r = - delta_t / (E_z_epsR * delta_phi * E_z_h_r * E_z_h_phi)

# Turn on interactive mode for animation
pl.ion()

for t in range(1, MAXTIME):

    ## Update equations ##
    
    # Update H-field, r-component
    delta_E_z = E_z[:, 1:] - E_z[:, :-1]
    delta_E_z = sp.hstack((delta_E_z, (E_z[:, :1] - E_z[:, -1:])))
    H_r = cH_r_H * H_r + cH_r_E_z * delta_E_z
    #sp.savetxt('output/time-step-%d-H_r.csv' % t, H_r[40:60, 80:100],
    #           delimiter=','                                          )
    
    # Update H-field, phi-componenet
    H_phi = cH_phi_H * H_phi + cH_phi_E_z * (E_z[1:, :] - E_z[:-1, :])
    #sp.savetxt('output/time-step-%d-H_phi.csv' % t, H_phi[40:60, 80:100],
    #           delimiter=','                                              )
    
    # Update E-field, z-component
    #TODO: Use E_z_h_r_fwd_avg and E_z_h_r_bwd_avg
    delta_H_r = H_r[1:-1, 1:] - H_r[1:-1, :-1]
    # Note carefully how the extra element, first-last, comes _before_ the rest
    delta_H_r = sp.hstack(((H_r[1:-1, :1] - H_r[1:-1, -1:]), delta_H_r))
    E_z[1:-1, :] = (  cE_z_E * E_z[1:-1, :]
                    + cE_z_H_phi * (  E_z_h_phi_fwd_avg * H_phi[1:, :]
                                    - E_z_h_phi_bwd_avg * H_phi[:-1, :] )
                    + cE_z_H_r * delta_H_r
                   )
    #sp.savetxt('output/time-step-%d-E_z.csv' % t, E_z[40:60, 80:100],
    #           fmt='%.18e', delimiter=','                             )
    
    ## Hard source ##
    
    # Ricker wavelet
    #arg = (sp.pi * (Sc_nu * t / PPW - 1.0)) ** 2
    #E_z[0, :] = (1 - 2*arg) * sp.exp(-arg)
    
    ## Gaussian
    E_z[50, 90] += sp.exp(-(t-30) * (t-30) / 100.0)
    
    # Sine wave
    #omega = 0.0001
    #E_z[0, :] = sp.cos(omega * t)
    
    ## Plotting ##
    
    if t % 5 == 0:
        temp_gridx = sp.hstack((gridx, sp.arange(SIZE_R).reshape((SIZE_R, 1))))
        temp_gridy = sp.hstack((gridy, sp.zeros(SIZE_R).reshape((SIZE_R, 1))))
        
        pl.figure(0)
        pl.clf()
        temp_H_r = sp.hstack((H_r, H_r[:, :1]))
        pl.contour(temp_gridx, temp_gridy, temp_H_r, 100)
        #pl.pcolor(H_r)
        pl.draw()

        pl.figure(1)
        pl.clf()
        temp_H_phi = sp.hstack((H_phi, H_phi[:, :1]))
        pl.contour(temp_gridx[1:, :], temp_gridy[1:, :], temp_H_phi, 100)
        #pl.pcolor(H_r)
        pl.draw()
        
        pl.figure(2)
        pl.clf()
        temp_E_z = sp.hstack((E_z, E_z[:, :1]))
        pl.contour(temp_gridx, temp_gridy, temp_E_z, 100)
        #pl.plot(range(len(E_z[:, 0])), E_z[:, 0])
        #pl.pcolor(E_z)
        pl.draw()
    
    #if t == 100:
    #    sys.exit(0)
