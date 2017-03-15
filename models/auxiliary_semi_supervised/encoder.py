import tensorflow as tf

from models.utils.distributions import draw_norm
from models.utils.tf_helpers import create_nn_weights, mlp_neuron, normalized_mlp


def qz_given_ayx(a, y, x, latent_dim, num_classes, hidden_dim, input_dim, is_training, reuse=False):
    with tf.variable_scope("encoder", reuse=reuse):
        # Variables
        w_h1, b_h1 = create_nn_weights('h1_z', 'encoder', [input_dim + num_classes + latent_dim, hidden_dim])
        w_h2, b_h2 = create_nn_weights('h1_z', 'encoder', [hidden_dim, hidden_dim])

        w_mu_z, b_mu_z = create_nn_weights('mu_z', 'encoder', [hidden_dim, latent_dim])
        w_var_z, b_var_z = create_nn_weights('var_z', 'encoder', [hidden_dim, latent_dim])

        # Hidden layers
        h1 = normalized_mlp(tf.concat([y, x, a], axis=1), w_h1, b_h1, is_training)
        h2 = normalized_mlp(h1, w_h2, b_h2, is_training)
        # Z2 latent layer mu and var
        logvar_z = mlp_neuron(h2, w_var_z, b_var_z, activation=False)
        mu_z = mlp_neuron(h2, w_mu_z, b_mu_z, activation=False)
        z = draw_norm(latent_dim, mu_z, logvar_z)
        return z, mu_z, logvar_z


def qa_given_x(x, hidden_dim, input_dim, latent_dim, is_training, reuse=False):
    # Auxiliary q(a|x)
    with tf.variable_scope("encoder", reuse=reuse):
        # Variables
        w_h1, b_h1 = create_nn_weights('h1_a', 'encoder', [input_dim, hidden_dim])
        w_h2, b_h2 = create_nn_weights('h2_a', 'encoder', [hidden_dim, hidden_dim])

        w_mu_a, b_mu_a = create_nn_weights('mu_a', 'encoder', [hidden_dim, latent_dim])
        w_var_a, b_var_a = create_nn_weights('var_a', 'encoder', [hidden_dim, latent_dim])

        # Hidden layers
        h1 = mlp_neuron(x, w_h1, b_h1)
        h2 = mlp_neuron(h1, w_h2, b_h2)

        # a latent layer mu and var
        logvar_a = mlp_neuron(h2, w_var_a, b_var_a, activation=False)
        mu_a = mlp_neuron(h2, w_mu_a, b_mu_a, activation=False)
        # Model
        a = draw_norm(latent_dim, mu_a, logvar_a)
        return a, mu_a, logvar_a


def qy_given_ax(a, x, input_dim, hidden_dim, latent_dim, num_classes, is_training, reuse=False):
    # Classifier q(y|a,x)
    with tf.variable_scope("y_classifier", reuse=reuse):
        w_h1_a, b_h1_a = create_nn_weights('y_h1', 'infer', [latent_dim, hidden_dim])
        w_h1_x, b_h1_x = create_nn_weights('y_h1', 'infer', [input_dim, hidden_dim])

        w_h2, b_h2 = create_nn_weights('y_h2', 'infer', [hidden_dim, hidden_dim])
        w_y, b_y = create_nn_weights('y_fully_connected', 'infer', [hidden_dim, num_classes])

        l_qa_to_qy = mlp_neuron(a, w_h1_a, b_h1_a)
        l_x_to_qy = mlp_neuron(x, w_h1_x, b_h1_x)

        h1 = normalized_mlp(tf.add(l_qa_to_qy, l_x_to_qy), w_h1_a, b_h1_a, is_training)
        h2 = normalized_mlp(h1, w_h2, b_h2, is_training)
        logits = tf.nn.softmax(mlp_neuron(h2, w_y, b_y, activation=False))
    return logits