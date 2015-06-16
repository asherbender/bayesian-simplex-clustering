import math
import numpy as np
from numpy import linalg, random
from scipy import special


class dirich(object):

    # Define a structure-like container class for storing the parameters of the
    # Dirichlet distribution.
    class param:
        pi = None
        alpha = None

    def __init__(self, dim, pi=None, alpha=None):

        assert dim > 0

        # Define default values for the parameters.
        if pi is None:
            pi = np.repeat(1.0/dim, dim)
        if alpha is None:
            alpha = 1.0

        self.__dim__ = dim
        self.__param__ = dirich.param()

        # Initialize the parameters.
        self.__param__.pi = pi
        self.__param__.alpha = alpha

        return

    @property
    def dim(self):
        return self.__dim__

    @property
    def pi(self):
        return self.__param__.pi

    @pi.setter
    def pi(self, pi):

        assert np.size(pi) == self.__dim__

        # Check that the parameter is a vector on the unit simplex.
        assert np.all(pi >= 0.0) and abs(np.sum(pi) - 1.0) < np.spacing(1.0)

        self.__param__.pi = np.copy(pi)

    @property
    def alpha(self):
        return self.__param__.alpha

    @alpha.setter
    def alpha(self, alpha):

        # Check that the parameter is a positive number.
        assert not np.isnan(alpha) and alpha > 0.0

        self.__param__.alpha = float(alpha)

    def copy(self, other):

        assert isinstance(other, dirich) and other.__dim__ == self.__dim__

        # Copy the parameters of the posterior distribution from the prior
        # distribution.
        self.__param__.pi[:] = other.__param__.pi
        self.__param__.alpha = other.__param__.alpha

        return self

    def rand(self):

        pi = self.__param__.pi
        alpha = self.__param__.alpha

        prop = np.copy(pi)

        if np.isfinite(alpha):

            ind, = np.where(pi > 0.0)

            # Simulate the Dirichlet distribution.
            prop[ind] = random.gamma(alpha*pi[ind]) / alpha
            prop[ind] /= prop[ind].sum()

        return prop

    def loglik(self, obs=None):

        dim = self.__dim__

        if obs is None:
            obs = np.arange(dim)
        else:
            assert np.ndim(obs) == 1

        pi = self.__param__.pi
        alpha = self.__param__.alpha

        if np.isfinite(alpha):

            val = np.zeros(np.size(obs))

            val[:] = -np.inf

            ind, = np.where(pi[obs] > 0.0)

            # Evaluate the expected log-likelihood.
            val[ind] = special.psi(alpha*pi[obs[ind]]) - special.psi(alpha)

            return val

        else:
            return np.log(pi[obs])

    def div(self, other):

        assert isinstance(other, dirich) and other.__dim__ == self.__dim__

        post = dirich.param()
        prior = dirich.param()

        post.pi = self.__param__.pi
        post.alpha = self.__param__.alpha

        prior.pi = other.__param__.pi
        prior.alpha = other.__param__.alpha

        if np.isfinite(post.alpha) and np.isfinite(prior.alpha):

            ind = post.pi > 0.0

            # Both distributions must have the same support, otherwise the
            # divergence is infinite.
            if np.logical_xor(ind, prior.pi > 0.0).any():
                return np.inf

            ind, = np.where(ind)

            # Compute the divergence between the posterior and the prior
            # Dirichlet distributions.
            return special.gammaln(post.alpha)-special.gammaln(prior.alpha) \
                   - (special.gammaln(post.alpha*post.pi[ind])-
                      special.gammaln(prior.alpha*prior.pi[ind])).sum() \
                   + np.dot(post.alpha*post.pi[ind]-prior.alpha*prior.pi[ind],
                               special.psi(post.alpha*post.pi[ind])-special.psi(post.alpha))

        elif (np.isinf(post.alpha) and np.isinf(prior.alpha) and
              np.equal(post.pi, prior.pi).all()):

            # The divergence vanishes if both distributions have exactly the
            # same parameters, even if they are singular.
            return 0.0

        else:

            # If either of the distributions is singular, and they have
            # different parameters, then the divergence is infinite.
            return np.inf

    def stat(self, evidence):

        dim = self.__dim__

        stat = dirich.param()

        # Initialize the expected sufficient statistics.
        stat.pi = np.zeros(dim)
        stat.alpha = 0.0

        for prob in evidence:

            assert np.ndim(prob) == 2
            dim, size = np.shape(prob)
            assert dim == self.__dim__

            count = np.sum(prob, axis=1)

            # Update the expected sufficient statistics.
            stat.pi += count
            stat.alpha += count.sum()

        return stat

    def update(self, stat):

        dim = self.__dim__

        assert isinstance(stat, dirich.param) and np.size(stat.pi) == dim

        pi = self.__param__.pi
        alpha = self.__param__.alpha

        # If the distribution is singular, then there is no more information to
        # be gained from the data.
        if np.isinf(alpha):
            return

        # Update the parameters to reflect the information gained from the
        # data.
        pi = alpha*pi + stat.pi
        alpha += stat.alpha
        pi /= alpha

        self.__param__.pi = pi
        self.__param__.alpha = alpha

        return self

class gaussgamma(object):

    # Define a structure-like container class for storing the parameters of the
    # Gauss-Gamma distribution.
    class param:
        mu = None
        omega = None
        sigma = None
        eta = None

    def __init__(self, dim, mu=None, omega=None, sigma=None, eta=None):

        assert dim > 0

        # Define default values for the parameters.
        if mu is None:
            mu = np.zeros(dim)
        if omega is None:
            omega = 1.0
        if sigma is None:
            sigma = np.ones(dim)
        if eta is None:
            eta = 1.0

        self.__dim__ = dim
        self.__param__ = gaussgamma.param()

        # Initialize the parameters.
        self.__param__.mu = mu
        self.__param__.omega = omega
        self.__param__.sigma = sigma
        self.__param__.eta = eta

        return

    @property
    def dim(self):
        return self.__dim__

    @property
    def mu(self):
        return self.__param__.mu

    @mu.setter
    def mu(self, mu):

        assert np.size(mu) == self.__dim__

        # Check that the parameter is a vector of finite numbers.
        assert not np.isnan(mu).any() and np.isfinite(mu).all()

        self.__param__.mu = np.copy(mu)

    @property
    def omega(self):
        return self.__param__.omega

    @omega.setter
    def omega(self, omega):

        # Check that the parameter is a positive number.
        assert not np.isnan(omega) and omega > 0.0

        self.__param__.omega = float(omega)

    @property
    def sigma(self):
        return self.__param__.sigma

    @sigma.setter
    def sigma(self, sigma):

        assert np.size(sigma) == self.__dim__

        # Check that the parameter is a vector of positive finite numbers.
        assert not np.isnan(sigma).any() and np.isfinite(sigma).all() and np.all(sigma > 0.0)

        self.__param__.sigma = np.copy(sigma)

    @property
    def eta(self):
        return self.__param__.eta

    @eta.setter
    def eta(self, eta):

        # Check that the parameter is a positive number.
        assert not np.isnan(eta) and eta > 0.0

        self.__param__.eta = float(eta)

    def copy(self, other):

        assert isinstance(other, gaussgamma) and other.__dim__ == self.__dim__

        # Copy the parameters of the posterior
        # distribution from the prior distribution.
        self.__param__.mu[:] = other.__param__.mu
        self.__param__.omega = other.__param__.omega
        self.__param__.sigma[:] = other.__param__.sigma
        self.__param__.eta = other.__param__.eta

        return self

    def rand(self):

        dim = self.__dim__

        mu = self.__param__.mu
        omega = self.__param__.omega
        sigma = self.__param__.sigma
        eta = self.__param__.eta

        if np.isfinite(eta):

            # Simulate the marginal Gamma distribution.
            disp = sigma/(random.gamma(eta/2.0, size=dim)/(eta/2.0))

        else:

            # Account for the special case where the marginal distribution is
            # singular.
            disp = np.copy(sigma)

        if np.isfinite(omega):

            # Simulate the conditional Gauss distribution.
            loc = mu + (np.sqrt(disp)*random.randn(dim))/math.sqrt(omega)

        else:

            # Account for the special case where the conditional distribution
            # is singular.
            loc = np.copy(mu)

        return loc, disp

    def loglik(self, obs, nu=None):

        assert np.ndim(obs) == 2
        dim, size = np.shape(obs)
        assert dim == self.__dim__

        mu = self.__param__.mu
        omega = self.__param__.omega
        sigma = self.__param__.sigma
        eta = self.__param__.eta

        # Compute the expected squared error.
        sqerr = ((np.abs(obs-mu[:, np.newaxis])**2)/sigma[:, np.newaxis]).sum(axis=0)
        if np.isfinite(omega):
            sqerr += dim/omega

        # Compute half of the expected log-determinant.
        logdet = np.log(sigma).sum()/2.0
        if np.isfinite(eta):
            logdet += (dim/2.0)*math.log(eta/2.0)-special.psi((eta-np.arange(dim))/2.0)/2.0

        if nu is None:

            # Evaluate the expected log-likelihood of the observations.
            return -(numdim/2.0)*math.log(2.0*math.pi)-logdet-sqerr/2.0

        elif np.isinf(nu):

            # Evaluate the expected log-likelihood of the observations, and the mixing weights.
            return -(numdim/2.0)*math.log(2.0*math.pi)-logdet-sqerr/2.0, np.ones(size)

        else:

            const = special.gammaln(nu/2.0) - special.gammaln((nu+dim)/2.0) \
                    + (dim/2.0)*math.log(math.pi*nu)+logdet

            # Evaluate the expected log-likelihood of the observations, and the
            # expected value of the posterior distribution over mixing weights.
            return -const-((nu+dim)/2.0)*np.log1p(sqerr/nu), (nu+dim)/(nu+sqerr)

    def div(self, other):

        assert isinstance(other, gaussgamma) and other.__dim__ == self.__dim__

        dim = self.__dim__

        post = gaussgamma.param()
        prior = gaussgamma.param()

        post.mu = self.__param__.mu
        post.omega = self.__param__.omega
        post.sigma = self.__param__.sigma
        post.eta = self.__param__.eta

        prior.mu = other.__param__.mu
        prior.omega = other.__param__.omega
        prior.sigma = other.__param__.sigma
        prior.eta = other.__param__.eta

        if np.isfinite(post.omega) and np.isfinite(prior.omega):

            # Compute the expected divergence between the posterior and the
            # prior conditional Gauss distributions.
            div = (dim/2.0)*(prior.omega/post.omega-math.log(prior.omega/post.omega)-1.0) \
                  + (prior.omega/2.0)*((np.abs(post.mu-prior.mu)**2)/post.sigma).sum()

        elif (np.isinf(post.omega) and np.isinf(prior.omega) and
              np.equal(post.mu, prior.mu).all()):

            # The divergence vanishes if both distributions have exactly the
            # same parameters, even if they are singular.
            div = 0.0

        else:

            # If either of the distributions is singular, and their parameters
            # are not exactly the same, then the divergence is infinite.
            return np.inf

        if np.isfinite(post.eta) and np.isfinite(prior.eta):

            # Calculate the log-determinants.
            post.det = np.log(post.sigma).sum()
            prior.det = np.log(prior.sigma).sum()

            aux = math.log(post.eta/2.0) - special.psi(post.eta/2.0).sum()

            # Add the divergence between the posterior and the prior marginal
            # Gamma distributions.
            return div-(post.eta/2.0)*dim+(prior.eta/2.0)*(prior.sigma/post.sigma).sum() \
                   + ((prior.eta-post.eta)/2.0)*(post.det+dim*aux) \
                   - (prior.eta/2.0)*prior.det+(post.eta/2.0)*post.det \
                   + dim*special.gammaln(prior.eta/2.0) \
                   - dim*special.gammaln(post.eta/2.0) \
                   - dim*(prior.eta/2.0)*math.log(prior.eta/2.0) \
                   + dim*(post.eta/2.0)*math.log(post.eta/2.0)

        elif (np.isinf(post.eta) and np.isinf(prior.eta) and
              np.equal(post.sigma, prior.sigma).all()):

            # If both distributions have the same parameters, then the
            # divergence vanishes.
            return div

        else:

            # If either distribution is singular, and they have different
            # parameters, then the divergence is infinite.
            return np.inf

    def stat(self, evidence, weighted=False, scaled=False):

        dim = self.__dim__

        stat = gaussgamma.param()

        # Initialize the expected sufficient statistics.
        stat.mu = np.zeros(dim)
        stat.omega = 0.0
        stat.sigma = np.zeros(dim)
        stat.eta = 0.0

        ref = self.__param__.mu.copy()

        # Accumulate the expected sufficient statistics.
        if not weighted:
            if not scaled:
                for obs in evidence:

                    assert np.ndim(obs) == 2
                    dim, size = np.shape(obs)
                    assert dim == self.__dim__

                    # Update the statistics of the conditional Gauss
                    # distribution.
                    stat.mu += np.sum(obs, axis=1)
                    stat.omega += size

                    # Update the statistics of the marginal Gamma distribution.
                    stat.sigma += (np.abs(obs-ref[:, np.newaxis])**2).sum(axis=1)
                    stat.eta += size

            else:
                for obs, scale in evidence:

                    assert np.ndim(obs) == 2
                    dim, size = np.shape(obs)
                    assert dim == self.__dim__

                    # Check that the size matches.
                    assert np.ndim(scale) == 1 and np.size(scale) == size

                    # Update the statistics of the conditional Gauss
                    # distribution.
                    stat.mu += np.dot(obs, scale)
                    stat.omega += np.sum(scale)

                    # Update the statistics of the marginal Gamma distribution.
                    stat.sigma += np.dot(np.abs(obs-ref[:, np.newaxis])**2, scale)
                    stat.eta += np.sum(scale)

        else:
            if scaled:
                for obs, weight, scale in evidence:

                    assert np.ndim(obs) == 2
                    dim, size = np.shape(obs)
                    assert dim == self.__dim__

                    # Check that the sizes match.
                    assert np.ndim(weight) == 1 and np.size(weight) == size
                    assert np.ndim(scale) == 1 and np.size(scale) == size

                    weight = np.multiply(weight, scale)

                    # Update the statistics of the conditional Gauss
                    # distribution.
                    stat.mu += np.dot(obs, weight)
                    stat.omega += weight.sum()

                    # Update the statistics of the marginal Gamma distribution.
                    stat.sigma += np.dot(np.abs(obs-ref[:, np.newaxis])**2, weight)
                    stat.eta += np.sum(scale)

            else:
                for obs, weight in evidence:

                    assert np.ndim(obs) == 2
                    dim, size = np.shape(obs)
                    assert dim == self.__dim__

                    # Check that the size matches.
                    assert np.ndim(weight) == 1 and np.size(weight) == size

                    # Update the statistics of the conditional Gauss
                    # distribution.
                    stat.mu += np.dot(obs, weight)
                    stat.omega += np.sum(weight)

                    # Update the statistics of the marginal Gamma distribution.
                    stat.sigma += np.dot(np.abs(obs-ref[:, np.newaxis])**2, weight)
                    stat.eta += size

        if stat.omega > 0.0:
            ref -= stat.mu/stat.omega

        # Compensate for the difference between the reference mean and the
        # sample mean.
        stat.sigma -= stat.omega*np.abs(ref)**2

        return stat

    def update(self, stat):

        dim = self.__dim__

        assert isinstance(stat, gaussgamma.param) and np.size(stat.mu) == dim \
               and np.size(stat.sigma) == dim

        mu = self.__param__.mu
        omega = self.__param__.omega
        sigma = self.__param__.sigma
        eta = self.__param__.eta

        # If the distribution is singular, then there is no more information to
        # be gained from the data.
        if np.isinf(omega) and np.isinf(eta):
            return self

        if stat.omega > 0.0:
            diff = mu - stat.mu/stat.omega
        else:
            diff = mu

        if np.isfinite(omega):

            weight = (omega*stat.omega)/(omega+stat.omega)

            # Update the parameters of the conditional Gauss distribution to
            # reflect the information gained from the data.
            mu = omega*mu+stat.mu
            omega += stat.omega
            mu /= omega

        else:

            weight = stat.omega

        if np.isfinite(eta):

            # Update the parameters of the marginal Gamma distribution to
            # reflect the information gained from the data.
            sigma = eta*sigma+stat.sigma+weight*np.abs(diff)**2
            eta += stat.eta
            sigma /= eta

        self.__param__.mu = mu
        self.__param__.omega = omega
        self.__param__.sigma = sigma
        self.__param__.eta = eta

        return self

class gausswish(object):

    # Define a structure-like container class for storing the parameters of the
    # Gauss-Wishart distribution.
    class param:
        mu = None
        omega = None
        sigma = None
        eta = None

    def __init__(self, dim, mu=None, omega=None, sigma=None, eta=None):

        assert dim > 0

        # Define default values for the parameters.
        if mu is None:
            mu = np.zeros(dim)
        if omega is None:
            omega = 1.0
        if sigma is None:
            sigma = np.eye(dim)
        if eta is None:
            eta = float(dim)

        self.__dim__ = dim
        self.__param__ = gausswish.param()

        # Initialize the parameters.
        self.__param__.mu = mu
        self.__param__.omega = omega
        self.__param__.sigma = sigma
        self.__param__.eta = eta

        return

    @property
    def dim(self):
        return self.__dim__

    @property
    def mu(self):
        return self.__param__.mu

    @mu.setter
    def mu(self, mu):

        assert np.size(mu) == self.__dim__

        # Check that the parameter is a vector of finite numbers.
        assert not np.isnan(mu).any() and np.isfinite(mu).all()

        self.__param__.mu = np.copy(mu)

    @property
    def omega(self):
        return self.__param__.omega

    @omega.setter
    def omega(self, omega):

        # Check that the parameter is a positive number.
        assert not np.isnan(omega) and omega > 0.0

        self.__param__.omega = float(omega)

    @property
    def sigma(self):
        return self.__param__.sigma

    @sigma.setter
    def sigma(self, sigma):

        assert np.shape(sigma) == (self.__dim__, self.__dim__)

        # Check that the parameter is a symmetric, positive-definite matrix.
        assert not np.isnan(sigma).any() and np.isfinite(sigma).all() \
               and np.allclose(np.transpose(sigma), sigma) \
               and (linalg.eigvals(sigma) > 0.0).all()

        self.__param__.sigma = np.copy(sigma)

    @property
    def eta(self):
        return self.__param__.eta

    @eta.setter
    def eta(self, eta):

        # Check that the parameter is a number greater than one minus the
        # number of degrees of freedom.
        assert not np.isnan(eta) and eta > self.__dim__ - 1.0

        self.__param__.eta = float(eta)

    def copy(self, other):

        assert isinstance(other, gausswish) and other.__dim__ == self.__dim__

        # Copy the parameters of the posterior distribution from the prior
        # distribution.
        self.__param__.mu[:] = other.__param__.mu
        self.__param__.omega = other.__param__.omega
        self.__param__.sigma[:] = other.__param__.sigma
        self.__param__.eta = other.__param__.eta

        return self

    def rand(self):

        dim = self.__dim__

        mu = self.__param__.mu
        omega = self.__param__.omega
        sigma = self.__param__.sigma
        eta = self.__param__.eta

        if np.isfinite(eta):

            # Simulate the marginal Wishart distribution.
            diag = 2.0*random.gamma((eta-np.arange(dim))/2.0)
            fact = np.diag(np.sqrt(diag))+np.tril(random.randn(dim, dim), -1)
            fact = linalg.solve(fact, math.sqrt(eta)*linalg.cholesky(sigma).T)
            disp = np.dot(fact.T, fact)

        else:

            # Account for the special case where the marginal distribution is
            # singular.
            disp = np.copy(sigma)

        if np.isfinite(omega):

            # Simulate the conditional Gauss distribution.
            loc = mu+np.dot(linalg.cholesky(disp), random.randn(dim))/math.sqrt(omega)

        else:

            # Account for the special case where the conditional distribution
            # is singular.
            loc = np.copy(mu)

        return loc, disp

    def loglik(self, obs, nu=None):

        assert np.ndim(obs) == 2
        dim, size = np.shape(obs)
        assert dim == self.__dim__

        mu = self.__param__.mu
        omega = self.__param__.omega
        sigma = self.__param__.sigma
        eta = self.__param__.eta

        fact = linalg.cholesky(sigma)

        # Compute the expected squared error.
        sqerr = (np.abs(linalg.solve(fact, obs-mu[:, np.newaxis]))**2).sum(axis=0)
        if np.isfinite(omega):
            sqerr += dim/omega

        # Compute half of the expected log-determinant.
        logdet = np.log(np.diag(fact)).sum()
        if np.isfinite(eta):
            logdet += (dim/2.0)*math.log(eta/2.0) - special.psi((eta-np.arange(dim))/2.0).sum()/2.0

        if nu is None:

            # Evaluate the expected log-likelihood of the observations.
            return -(numdim/2.0)*math.log(2.0*math.pi)-logdet-sqerr/2.0

        elif np.isinf(nu):

            # Evaluate the expected log-likelihood of the observations, and the
            # mixing weights.
            return -(numdim/2.0)*math.log(2.0*math.pi)-logdet-sqerr/2.0, np.ones(size)

        else:

            const = special.gammaln(nu/2.0)-special.gammaln((nu+dim)/2.0) \
                    + (dim/2.0)*math.log(math.pi*nu) + logdet

            # Evaluate the expected log-likelihood of the observations, and the
            # expected value of the posterior distribution over mixing weights.
            return -const-((nu+dim)/2.0)*np.log1p(sqerr/nu), (nu+dim)/(nu+sqerr)

    def div(self, other):

        assert isinstance(other, gausswish) and other.__dim__ == self.__dim__

        dim = self.__dim__

        post = gausswish.param()
        prior = gausswish.param()

        post.mu = self.__param__.mu
        post.omega = self.__param__.omega
        post.sigma = self.__param__.sigma
        post.eta = self.__param__.eta

        prior.mu = other.__param__.mu
        prior.omega = other.__param__.omega
        prior.sigma = other.__param__.sigma
        prior.eta = other.__param__.eta

        post.fact = linalg.cholesky(post.sigma)

        if np.isfinite(post.omega) and np.isfinite(prior.omega):

            # Compute the expected divergence between the posterior and the
            # prior conditional Gauss distributions.
            div = (dim/2.0)*(prior.omega/post.omega-math.log(prior.omega/post.omega)-1.0) \
                  + (prior.omega/2.0)*(np.abs(linalg.solve(post.fact, post.mu-prior.mu))**2).sum()

        elif (np.isinf(post.omega) and np.isinf(prior.omega) and
              np.equal(post.mu, prior.mu).all()):

            # The divergence vanishes if both distributions have exactly the
            # same parameters, even if they are singular.
            div = 0.0

        else:

            # If either of the distributions is singular, and their parameters
            # are not exactly the same, then the divergence is infinite.
            return np.inf

        if np.isfinite(post.eta) and np.isfinite(prior.eta):

            prior.fact = linalg.cholesky(prior.sigma)

            # Calculate half of the log-determinants.
            post.det = np.log(np.diagonal(post.fact)).sum()
            prior.det = np.log(np.diagonal(prior.fact)).sum()

            aux = (dim/2.0)*math.log(post.eta/2.0) \
                  -special.psi((post.eta-np.arange(dim))/2.0).sum()/2.0

            # Add the divergence between the posterior and the prior marginal
            # Wishart distributions.
            return div-(post.eta/2.0)*dim \
                   + (prior.eta/2.0)*(np.abs(linalg.solve(post.fact, prior.fact))**2).sum() \
                   + (prior.eta-post.eta)*(post.det+aux)-prior.eta*prior.det+post.eta*post.det \
                   + special.gammaln((prior.eta-np.arange(dim))/2.0).sum() \
                   - special.gammaln((post.eta-np.arange(dim))/2.0).sum() \
                   - dim*(prior.eta/2.0)*math.log(prior.eta/2.0) \
                   + dim*(post.eta/2.0)*math.log(post.eta/2.0)

        elif (np.isinf(post.eta) and np.isinf(prior.eta) and
              np.equal(post.sigma, prior.sigma).all()):

            # If both distributions have the same parameters, then the
            # divergence vanishes.
            return div

        else:

            # If either distribution is singular, and they have different
            # parameters, then the divergence is infinite.
            return np.inf

    def stat(self, evidence, weighted=False, scaled=False):

        dim = self.__dim__

        stat = gausswish.param()

        # Initialize the expected sufficient statistics.
        stat.mu = np.zeros(dim)
        stat.omega = 0.0
        stat.sigma = np.zeros([dim, dim])
        stat.eta = 0.0

        ref = self.__param__.mu.copy()

        # Accumulate the expected sufficient statistics.
        if not weighted:
            if not scaled:
                for obs in evidence:

                    assert np.ndim(obs) == 2
                    dim, size = np.shape(obs)
                    assert dim == self.__dim__

                    # Update the statistics of the conditional Gauss
                    # distribution.
                    stat.mu += np.sum(obs, axis=1)
                    stat.omega += size

                    resid = obs-ref[:, np.newaxis]

                    # Update the statistics of the marginal Wishart
                    # distribution.
                    stat.sigma += np.dot(resid, resid.T)
                    stat.eta += size

            else:
                for obs, scale in evidence:

                    assert np.ndim(obs) == 2
                    dim, size = np.shape(obs)
                    assert dim == self.__dim__

                    # Check that the size matches.
                    assert np.ndim(scale) == 1 and np.size(scale) == size

                    # Update the statistics of the conditional Gauss
                    # distribution.
                    stat.mu += np.dot(obs, scale)
                    stat.omega += np.sum(scale)

                    resid=obs-ref[:, np.newaxis]

                    # Update the statistics of the marginal Wishart
                    # distribution.
                    stat.sigma += np.dot(resid, np.reshape(scale, [size, 1])*resid.T)
                    stat.eta += np.sum(scale)

        else:
            if scaled:
                for obs, weight, scale in evidence:

                    assert np.ndim(obs) == 2
                    dim, size = np.shape(obs)
                    assert dim == self.__dim__

                    # Check that the sizes match.
                    assert np.ndim(weight) == 1 and np.size(weight) == size
                    assert np.ndim(scale) == 1 and np.size(scale) == size

                    weight = np.multiply(weight, scale)

                    # Update the statistics of the conditional Gauss
                    # distribution.
                    stat.mu += np.dot(obs, weight)
                    stat.omega += weight.sum()

                    resid = obs-ref[:, np.newaxis]

                    # Update the statistics of the marginal Wishart
                    # distribution.
                    stat.sigma += np.dot(resid, weight[:, np.newaxis]*resid.T)
                    stat.eta += np.sum(scale)

            else:
                for obs, weight in evidence:

                    assert np.ndim(obs) == 2
                    dim, size = np.shape(obs)
                    assert dim == self.__dim__

                    # Check that the size matches.
                    assert np.ndim(weight) == 1 and np.size(weight) == size

                    # Update the statistics of the conditional Gauss
                    # distribution.
                    stat.mu += np.dot(obs, weight)
                    stat.omega += np.sum(weight)

                    resid=obs-ref[:, np.newaxis]

                    # Update the statistics of the marginal Wishart
                    # distribution.
                    stat.sigma += np.dot(resid, np.reshape(weight, [size, 1])*resid.T)
                    stat.eta += size

        if stat.omega > 0.0:
            ref -= stat.mu/stat.omega

        # Compensate for the difference between the reference mean and the
        # sample mean.
        stat.sigma -= stat.omega*np.outer(ref, ref)

        return stat

    def update(self, stat):

        dim = self.__dim__

        assert isinstance(stat, gausswish.param) and np.size(stat.mu) == dim \
               and np.shape(stat.sigma) == (dim, dim)

        mu = self.__param__.mu
        omega = self.__param__.omega
        sigma = self.__param__.sigma
        eta = self.__param__.eta

        # If the distribution is singular, then there is no more information to
        # be gained from the data.
        if np.isinf(omega) and np.isinf(eta):
            return

        if stat.omega > 0.0:
            diff = mu-stat.mu/stat.omega
        else:
            diff = mu

        if np.isfinite(omega):

            weight = (omega*stat.omega)/(omega+stat.omega)

            # Update the parameters of the conditional Gauss distribution to
            # reflect the information gained from the data.
            mu = omega*mu+stat.mu
            omega += stat.omega
            mu /= omega

        else:

            weight = stat.omega

        if np.isfinite(eta):

            # Update the parameters of the marginal Wishart distribution to
            # reflect the information gained from the data.
            sigma = eta*sigma + stat.sigma + weight*np.outer(diff, diff)
            eta += stat.eta
            sigma /= eta

        sigma = sigma/2.0+(sigma/2.0).T

        self.__param__.mu = mu
        self.__param__.omega = omega
        self.__param__.sigma = sigma
        self.__param__.eta = eta

        return self
