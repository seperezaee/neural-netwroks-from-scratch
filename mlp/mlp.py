# author : Alireza Afzal Aghaei
# references: https://matrices.io/deep-neural-network-from-scratch/
#             https://github.com/theflofly/dnn_from_scratch_py


import numpy as np
from .activations import *
from .loss_functions import MSE, XEntropy

np.random.seed(1)


class MLP:
    def __init__(self, hidden_layer_sizes: list,
                 activation: Activation = Tanh,
                 epochs: int = 1000,
                 eta: float = 0.01,
                 beta: float = 1,
                 alpha: float = 0.01,
                 mu: float = 0.9,
                 verbose: int = False,
                 task: str = 'classification'
                 ):
        self.random = np.random.randn
        self.weights_ = []
        self.beta = beta
        self.alpha = alpha
        self.n_epochs = epochs
        self.learning_rate = eta
        self.momentum = mu
        self.x = None
        self.y = None
        self.a = []
        self.z = []
        self.deltas = []
        self.dLdws = []
        self.hidden_layer_sizes = hidden_layer_sizes
        self.verbose = verbose
        self.activation = activation.activation
        self.activation_prime = activation.activation_prime
        self.current_loss = None
        self.velocity_ = []
        self.type = task
        if task == 'classification':
            self._output = Softmax.activation
            self._output_prime = Softmax.activation_prime
            self._loss = XEntropy.loss
            self._loss_prime = XEntropy.loss_prime

        elif task == 'regression':
            self._output = Identity.activation
            self._output_prime = Identity.activation_prime
            self._loss = MSE.loss
            self._loss_prime = MSE.loss_prime
        else:
            raise ValueError('just use classification or regression')

    def init_weights(self):
        for a, b in zip(self.hidden_layer_sizes, self.hidden_layer_sizes[1:]):
            self.weights_.append(self.random(a + 1, b) * self.beta)
            self.velocity_.append(np.zeros((a + 1, b)))

    def _forward(self, a):
        self.z = []
        self.a = [a]
        for i in range(len(self.weights_)):
            z = a @ self.weights_[i]
            if i != len(self.weights_) - 1:
                a = self.activation(z)
            else:
                a = self._output(z)

            if i != len(self.weights_) - 1:
                a = np.hstack((a, np.ones((a.shape[0], 1))))
            self.a.append(a)
            self.z.append(z)

        return self.a[-1]

    def _backward(self):
        self.deltas = list()
        self.dLdws = list()

        self.deltas.append(-(self._loss_prime(self.a[-1], self.y)) * self._output_prime(self.z[-1]))
        self.dLdws.append(self.a[-2].T @ self.deltas[-1] + self.alpha * self.weights_[-1])
        for i in range(len(self.z) - 1, 0, -1):
            t = np.hstack((self.z[i - 1], np.ones((self.z[i - 1].shape[0], 1))))
            t = self.activation_prime(t)
            delta = ((self.deltas[-1] @ self.weights_[i].T) * t)[:, :-1]
            self.deltas.append(delta)
            dLdw = self.a[i - 1].T @ self.deltas[-1] + self.alpha * self.weights_[i - 1]
            self.dLdws.append(dLdw)

        self.dLdws = self.dLdws[::-1]

    def _update_weights(self):
        for i in range(len(self.weights_)):
            self.velocity_[i] = self.momentum * self.velocity_[i] + self.learning_rate * self.dLdws[i] / len(self.x)
            self.weights_[i] -= self.velocity_[i]

    def cost(self, t, y):
        return self._loss(y, t) + self.alpha * np.sum([w.sum() for w in self.weights_])

    def fit(self, x, y):
        self.hidden_layer_sizes.insert(0, x.shape[1])
        self.hidden_layer_sizes.append(y.shape[1])

        self.x = np.hstack((x, np.ones((x.shape[0], 1))))
        self.y = y
        self.init_weights()
        hist = []
        for i in range(self.n_epochs):
            yp = self._forward(self.x)
            self._backward()
            self._update_weights()
            # validation?
            hist.append(self.cost(yp, self.y))
            self.current_loss = hist[-1]
            self._verbose(i)

        return hist

    def _verbose(self, i):
        if self.verbose and (i + 1) % self.verbose == 0:
            print("epoch %05d, loss: %06.2f" % (i + 1, self.current_loss))

    def predict(self, x):
        x = np.hstack((x, np.ones((x.shape[0], 1))))
        return self._forward(x)
