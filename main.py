from math import pi, sin, sqrt
import random
import numpy as np
import matplotlib.pyplot as plt

m = 8
K = 50


def generate(seed=0, plot=True, start=0.):
    random.seed(seed)
    if plot:
        plt.subplot(1, 1, 1)
    delta_t = 20/(K * 1)
    x1 = [k*delta_t for k in range(K)]

    # A = [(random.random()-0.5)*10 for _ in range(m+1)]
    A = [i**2 for i in range(m+1)]
    phi = [(random.random()-0.5)*pi for _ in range(m+1)]
    w = lambda p: (2*pi*p)
    print(">>>> ", [w(p)/(2*pi) for p in range(m+1)])
    print(">>>> ", A)

    def sin_1(p):
        return lambda t: A[p]*sin(w(p)*t + phi[p])

    sins = [sin_1(p) for p in range(m+1)]
    if plot:
        for s in sins:
            plt.plot(x1, [s(x) for x in x1], 'r--')

    x = lambda t: sum(func(t) for func in sins)


    nums = [x(k*delta_t + start) for k in range(K)]
    mat = sum(nums)/K
    D = sum([(i - mat)**2 for i in nums]) / K
    Sigma = sqrt(D)
    print(nums)
    print("m =", mat)
    print("D =", D)
    print("Sigma =", Sigma)

    if plot:
        mat_p = plt.plot(x1, np.linspace(mat, mat), 'g-', linewidth=2)
        sigma_p = plt.fill_between(x1, np.linspace(mat-Sigma, mat-Sigma),
                                 np.linspace(mat+Sigma, mat+Sigma),
                                 alpha=0.2, hatch='/')
        nums_p = plt.plot(x1, nums, 'bo-')
        plt.show()
    return x1, nums, mat, D, Sigma, delta_t


def main():
    import numpy as np
    import matplotlib.pyplot as plt

    x1, nums1, mat1, D1, Sigma1, delta_t = generate(plot=True, start=0)

    nums1 = np.array(nums1)
    # data = np.random.rand(301) - 0.5
    ps = np.abs(np.fft.fft(nums1)/(nums1.size/2))
    ps[0] *= 2

    # time_step = 1 / 30
    freqs = np.fft.fftfreq(nums1.size, delta_t)
    print(">>>>> freqs", freqs)
    idx = np.argsort(freqs)

    plt.plot(freqs[idx], ps[idx], '-o')

    plt.show()

if __name__ == "__main__":
    main()
    # generate(plot=True, seed=0)
