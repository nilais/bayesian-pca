import numpy as np

class Q(object):
    def __init__(self, n, p, q):
        self.n = n
        self.d = p
        self.q = q
        self.init_rnd()

    def init_rnd(self):
        self.x_mean = np.random.normal(0.0, 1.0, self.q * self.n).reshape(self.q, self.n)
        self.x_cov = np.eye(self.q)
        self.w_mean = np.random.normal(0.0, 1.0, self.d * self.q).reshape(self.d, self.q)
        self.w_cov = np.eye(self.q)
        self.mu_mean = np.random.normal(0.0, 1.0, self.d)
        self.mu_cov = np.eye(self.d)
        self.alpha_a = 1.0
        self.alpha_b = np.ones(self.q)
        self.gamma_a = 1.0
        self.gamma_b = 1.0

    def gamma_mean(self):
        return self.gamma_a / self.gamma_b

    def alpha_mean(self):
        return self.alpha_a / self.alpha_b

class VBPCA(object):

    def __init__(self, y):
        self.y = y
        self.d = y.shape[0]
        self.q = self.d - 1
        self.n = y.shape[1]
        self.alpha_a = 1.0
        self.alpha_b = 1.0
        self.gamma_a = 1.0
        self.gamma_b = 1.0
        self.beta = 1.0
        self.q_dist = Q(self.n, self.d, self.q)

    def fit_transform(self, *args, **kwargs):
        self.fit(*args, **kwargs)
        return self.transform()

    def transform(self, y=None):
        if y is None:
            return self.q_dist.x_mean
        q = self.q_dist
        [w, mu, sigma] = [q.w_mean, q.mu_mean, q.gamma_mean()**-1]
        m = w.T.dot(w) + sigma * np.eye(w.shape[1])
        m = np.linalg.inv(m)
        x = m.dot(w.T).dot(y - mu)
        return x

    def update(self):
        # update mu
        q = self.q_dist
        gamma_mean = q.gamma_a / q.gamma_b
        q.mu_cov = (self.beta + self.n * gamma_mean)**-1 * np.eye(self.d)
        q.mu_mean = np.sum(self.y - q.w_mean.dot(q.x_mean), 1)
        q.mu_mean = gamma_mean * q.mu_cov.dot(q.mu_mean)

        # update w
        q = self.q_dist
        # cov
        x_cov = np.zeros((self.q, self.q))
        for n in range(self.n):
            x = q.x_mean[:, n]
            x_cov += x[:, np.newaxis].dot(np.array([x]))
        q.w_cov = np.diag(q.alpha_a / q.alpha_b) + q.gamma_mean() * x_cov
        q.w_cov = np.linalg.inv(q.w_cov)
        # mean
        yc = self.y - q.mu_mean[:, np.newaxis]
        q.w_mean = (q.gamma_mean() * q.w_cov.dot(q.x_mean.dot(yc.T))).T

        # update x
        q = self.q_dist
        gamma_mean = q.gamma_a / q.gamma_b
        q.x_cov = np.linalg.inv(np.eye(self.q) + gamma_mean * q.w_mean.T.dot(q.w_mean))
        q.x_mean = gamma_mean * q.x_cov.dot(q.w_mean.T).dot(self.y - q.mu_mean[:, np.newaxis])

        # update alpha
        q = self.q_dist
        q.alpha_a = self.alpha_a + 0.5 * self.d
        q.alpha_b = self.alpha_b + 0.5 * np.linalg.norm(q.w_mean, axis=0)**2

        # update gamma
        q = self.q_dist
        q.gamma_a = self.gamma_a + 0.5 * self.n * self.d
        q.gamma_b = self.gamma_b
        w = q.w_mean
        ww = w.T.dot(w)
        for n in range(self.n):
            y = self.y[:, n]
            x = q.x_mean[:, n]
            q.gamma_b += y.dot(y) + q.mu_mean.dot(q.mu_mean)
            q.gamma_b += np.trace(ww.dot(x[:, np.newaxis].dot([x])))
            q.gamma_b += 2.0 * q.mu_mean.dot(w).dot(x[:, np.newaxis])
            q.gamma_b -= 2.0 * y.dot(w).dot(x)
            q.gamma_b -= 2.0 * y.dot(q.mu_mean)
