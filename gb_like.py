import numpy as np

try:
    import cupy as xp

    gpu = True

except (ImportError, ModuleNotFoundError) as e:
    import numpy as xp

    gpu = False

from response import pyResponseTDI
from few.utils.constants import *

#from ldc.waveform.waveform import HpHc
#from ldc.lisa.orbits import Orbits

class GBLike:
    def __init__(self, response_model, sampling_frequency, Tobs, tdi_kwargs, use_gpu=False):

        self.response_model = response_model
        if use_gpu:
            self.xp = xp
        else:
            self.xp = np
        self.n = int(Tobs * YRSID_SI / response_model.dt)
        self.Tobs = self.n * response_model.dt

        # add the buffer
        self.t_buffer = response_model.total_buffer * response_model.dt
        self.t = np.arange(response_model.t0_wave, response_model.tend_wave, response_model.dt)
        self.t_in = self.xp.asarray(
            self.t
        )  #  - self.t0_tdi  # sets quantities at beginning of tdi
        # TODO: should we keep this?

    def _get_h(self, A, f, fdot, iota, phi0, psi):
        cos2psi = self.xp.cos(2.0 * psi)
        sin2psi = self.xp.sin(2.0 * psi)
        cosiota = self.xp.cos(iota)

        # phi0 is phi(t = 0, which is shifted due to t_buffer)
        phase = 2 * np.pi * (f * self.t_in + 1.0 / 2.0 * fdot * self.t_in ** 2) - phi0

        hSp = -self.xp.cos(phase) * A * (1.0 + cosiota * cosiota)
        hSc = -self.xp.sin(phase) * 2.0 * A * cosiota

        hp = hSp * cos2psi - hSc * sin2psi
        hc = hSp * sin2psi + hSc * cos2psi

        return hp + 1j * hc

    def __call__(self, A, f, fdot, iota, phi0, psi, lam, beta):

        h = self._get_h(A, f, fdot, iota, phi0, psi)

        self.response_model.get_projections(h, lam, beta)
        tdi_out = self.response_model.get_tdi_delays()

        return list(tdi_out)

class EMRILike:
    def __init__(self, few_model, response_model, Tobs, use_gpu=False):

        self.emri_wave = few_model
        self.response_model = response_model
        if use_gpu:
            self.xp = xp
        else:
            self.xp = np
        self.n = int(Tobs * YRSID_SI / response_model.dt)
        self.Tobs = self.n * response_model.dt

        # add the buffer
        self.t_buffer = response_model.total_buffer * response_model.dt
        self.t = np.arange(response_model.t0_wave, response_model.tend_wave, response_model.dt)
        self.t_in = self.xp.asarray(
            self.t
        )
        self.n_all = len(self.t_in)

        # TODO: fix this:
        self.Tobs = (self.n_all * response_model.dt) / YRSID_SI

        #  - self.t0_tdi  # sets quantities at beginning of tdi
        # TODO: should we keep this?

    def _get_h(self, *args, **kwargs):
        out = self.emri_wave(*args, T=self.Tobs, dt=self.response_model.dt, **kwargs)
        hp = out.real
        hc = -out.imag

        return hp + 1j * hc

    def __call__(self, lam, beta, *args, **kwargs):

        h = self._get_h(*args, **kwargs)

        response_model.get_projections(h, lam, beta)
        tdi_out = response_model.get_tdi_delays()

        return list(tdi_out)


if __name__ == "__main__":

    from few.waveform import GenerateEMRIWaveform
    from astropy import units as un
    import doctest
    #from ldc.waveform.waveform import HpHc
    #from ldc.lisa.orbits import Orbits
    #from ldc.lisa.projection import ProjectedStrain

    use_gpu = gpu

    num_pts_in = int(3e6)

    sampling_frequency = 0.1
    dt = 1 / sampling_frequency
    T = (num_pts_in * dt) / YRSID_SI

    order = 25

    orbit_file = "esa_fit_with_equalarmlength.h5"

    config = dict(
        {
            "nominal_arm_length": 2.5e9 * un.m,
            "initial_rotation": 0 * un.rad,
            "initial_position": 0 * un.rad,
            "orbit_type": "analytic",
        }
    )

    pGB = dict(
        {
            "Amplitude": 1.07345e-22,
            "EclipticLatitude": 0.312414 * un.rad,
            "EclipticLongitude": -2.75291 * un.rad,
            "Frequency": 0.00135962 * un.Hz,
            "FrequencyDerivative": 8.94581279e-19 * un.Unit("Hz2"),
            "Inclination": 0.523599 * un.rad,
            "InitialPhase": 3.0581565 * un.rad,
            "Polarization": 3.5621656 * un.rad,
        }
    )

    #GB = HpHc.type("my-galactic-binary", "GB", "TD_fdot")
    #GB.set_param(pGB)
    """
    orbits = Orbits.type(config)

    proj = ProjectedStrain(orbits)
    """
    num_pts = int(3e6)
    tdi_kwargs = dict(
        orbit_kwargs=dict(orbits_file=orbit_file),
        order=order,
        tdi="1st generation",
        tdi_chan="XYZ",
        num_pts=num_pts,
    )
    import time

    response_model = pyResponseTDI(sampling_frequency, use_gpu=use_gpu, **tdi_kwargs)

    gb = GBLike(response_model, sampling_frequency, T, tdi_kwargs, use_gpu=use_gpu)

    A = pGB["Amplitude"]
    f = pGB["Frequency"].value
    fdot = pGB["FrequencyDerivative"].value
    iota = pGB["Inclination"].value
    phi0 = pGB["InitialPhase"].value
    psi = pGB["Polarization"].value

    beta = pGB["EclipticLatitude"].value
    lam = pGB["EclipticLongitude"].value

    num = 1
    chans = gb(A, f, fdot, iota, phi0, psi, lam, beta)
    st = time.perf_counter()
    for i in range(num):
        chans = gb(A, f, fdot, iota, phi0, psi, lam, beta)

    et = time.perf_counter()

    X1, Y1, Z1 = chans
    print("num delays:", num_pts_in, (et - st) / num)

    few_mod = GenerateEMRIWaveform("FastSchwarzschildEccentricFlux", sum_kwargs=dict(pad_output=True))

    em = EMRILike(few_mod, response_model, 2.0)



    M = 1e6
    mu = 1e1
    a = 0.0
    p0 = 12.
    e0 = 0.4
    x0 = 1.0
    dist = 1.0
    qS = 0.5
    phiS = 0.6
    qK = 0.7
    phiK = 0.8
    Phi_phi0 = 0.9
    Phi_theta0 = 1.
    Phi_r0 = 1.1



    out = em(phiS,
        np.pi/2. - qS,
        M,
        mu,
        a,
        p0,
        e0,
        x0,
        dist,
        qS,
        phiS,
        qK,
        phiK,
        Phi_phi0,
        Phi_theta0,
        Phi_r0)

    import matplotlib.pyplot as plt

    """
    import lisagwresponse

    import os

    if "gw.h5" in os.listdir():
        os.remove("gw.h5")

    temp = lisagwresponse.GalacticBinary(
        A=A,
        f=f,
        df=fdot,
        orbits=orbit_file,
        gw_beta=beta,
        gw_lambda=lam,
        phi0=phi0,
        iota=iota,
        psi=psi,
        t0=100.0,
        dt=dt,
        size=num_pts,
    )

    temp.write("gw.h5")

    import h5py

    with h5py.File("gw.h5", "r") as fp:
        checkit = {key: fp[key][:] for key in fp}
    """
    """
    breakpoint()
    proj = ProjectedStrain(orbits)

    t_data = np.load("t_data.npy")

    sampling_frequency = 0.1
    dt = 1 / sampling_frequency

    yArm = proj.arm_response(t_data[0], t_data[-1], dt, [GB])

    X = proj.compute_tdi_x(np.arange(t_data[0], t_data[-1], dt))[:num_pts_in]
    Y = proj.compute_tdi_y(np.arange(t_data[0], t_data[-1], dt))[:num_pts_in]
    Z = proj.compute_tdi_z(np.arange(t_data[0], t_data[-1], dt))[:num_pts_in]
    try:
        X1, Y1, Z1 = X1.get(), Y1.get(), Z1.get()

    except AttributeError:
        pass



    from response import AET
    check = np.load('try1.npy')
    temp = AET(*check)
    mismatch = [
        1.0 - np.dot(K, K1) / np.sqrt(np.dot(K, K) * np.dot(K1, K1))
        for K, K1 in zip(
            check,
            gb.XYZ,
        )
    ]
    print(mismatch)


    #import matplotlib.pyplot as plt
    #plt.plot(X1)
    """
    breakpoint()
