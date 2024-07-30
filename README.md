Follow the instructions at https://developers.google.com/gmail/api/quickstart/python to create a `credentials.json` and store in the project directory.

## Example output

<div class="paper">
    <p class="title">Specify and Edit: Overcoming Ambiguity in Text-Based Image Editing</p>
    <p class="authors"><strong>Authors:</strong> Ekaterina Iakovleva, Fabio Pizzati, Philip Torr, Stéphane Lathuilière</p>
    <p class="summary"><strong>Summary:</strong> Text-based editing diffusion models exhibit limited performance when the
user's input instruction is ambiguous. To solve this problem, we propose
$\textit{Specify ANd Edit}$ (SANE), a zero-shot inference pipeline for
diffusion-based editing systems. We use a large language model (LLM) to
decompose the input instruction into specific instructions, i.e. well-defined
interventions to apply to the input image to satisfy the user's request. We
benefit from the LLM-derived instructions along the original one, thanks to a
novel denoising guidance strategy specifically designed for the task. Our
experiments with three baselines and on two datasets demonstrate the benefits
of SANE in all setups. Moreover, our pipeline improves the interpretability of
editing models, and boosts the output diversity. We also demonstrate that our
approach can be applied to any edit, whether ambiguous or not. Our code is
public at https://github.com/fabvio/SANE.</p>
    <p class="link"><a href="http://arxiv.org/abs/2407.20232v1">Read more</a></p>
</div>

<div class="paper">
    <p class="title">SAPG: Split and Aggregate Policy Gradients</p>
    <p class="authors"><strong>Authors:</strong> Jayesh Singla, Ananye Agarwal, Deepak Pathak</p>
    <p class="summary"><strong>Summary:</strong> Despite extreme sample inefficiency, on-policy reinforcement learning, aka
policy gradients, has become a fundamental tool in decision-making problems.
With the recent advances in GPU-driven simulation, the ability to collect large
amounts of data for RL training has scaled exponentially. However, we show that
current RL methods, e.g. PPO, fail to ingest the benefit of parallelized
environments beyond a certain point and their performance saturates. To address
this, we propose a new on-policy RL algorithm that can effectively leverage
large-scale environments by splitting them into chunks and fusing them back
together via importance sampling. Our algorithm, termed SAPG, shows
significantly higher performance across a variety of challenging environments
where vanilla PPO and other strong baselines fail to achieve high performance.
Website at https://sapg-rl.github.io/</p>
    <p class="link"><a href="http://arxiv.org/abs/2407.20230v1">Read more</a></p>
</div>

<div class="paper">
    <p class="title">Characterizing Dynamical Stability of Stochastic Gradient Descent in
Overparameterized Learning</p>
    <p class="authors"><strong>Authors:</strong> Dennis Chemnitz, Maximilian Engel</p>
    <p class="summary"><strong>Summary:</strong> For overparameterized optimization tasks, such as the ones found in modern
machine learning, global minima are generally not unique. In order to
understand generalization in these settings, it is vital to study to which
minimum an optimization algorithm converges. The possibility of having minima
that are unstable under the dynamics imposed by the optimization algorithm
limits the potential minima that the algorithm can find. In this paper, we
characterize the global minima that are dynamically stable/unstable for both
deterministic and stochastic gradient descent (SGD). In particular, we
introduce a characteristic Lyapunov exponent which depends on the local
dynamics around a global minimum and rigorously prove that the sign of this
Lyapunov exponent determines whether SGD can accumulate at the respective
global minimum.</p>
    <p class="link"><a href="http://arxiv.org/abs/2407.20209v1">Read more</a></p>
</div>
    