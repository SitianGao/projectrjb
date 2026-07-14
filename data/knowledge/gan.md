# Generative Adversarial Networks (GANs)

## The Core Idea

A GAN consists of two neural networks locked in a game-theoretic contest:

- **Generator $G$:** Takes random noise $z \sim p_z$ (e.g., Gaussian) and produces synthetic data $G(z)$ that aims to look real.
- **Discriminator $D$:** Takes a sample (real or generated) and outputs the probability that it came from the real data distribution.

$G$ tries to minimize and $D$ tries to maximize the probability that the discriminator correctly labels real vs. fake. This adversarial process drives the generator to produce increasingly realistic outputs.

---

## Minimax Objective

The training objective (Goodfellow et al., 2014):

$$\min_G \max_D V(D, G) = \mathbb{E}_{x \sim p_{\text{data}}}[\log D(x)] + \mathbb{E}_{z \sim p_z}[\log(1 - D(G(z)))]$$

- $D(x)$ should be close to 1 for real data (maximize $\log D(x)$).
- $D(G(z))$ should be close to 0 for generated data (maximize $\log(1 - D(G(z)))$).
- $G$ minimizes $\log(1 - D(G(z)))$, which is equivalent to maximizing $\log D(G(z))$ — this "non-saturating" loss provides stronger gradients early in training.

At the theoretical Nash equilibrium, $G$ perfectly replicates $p_{\text{data}}$ and $D(x) = 0.5$ everywhere (the discriminator cannot distinguish real from fake).

---

## Training Procedure

GANs are trained by alternating between:
1. **Train $D$:** On a batch of real data (label=1) and a batch of generated data (label=0). Update $D$ to maximize classification accuracy.
2. **Train $G$:** Generate a batch of fake data, ask $D$ to evaluate it, and update $G$ to maximize $D$'s mistake (i.e., make $D(G(z)) \to 1$).

A common heuristic: train $D$ for $k$ steps per $G$ step (e.g., $k = 1$ or $k = 5$) to keep the discriminator ahead.

---

## Training Instability and Mode Collapse

GAN training is notoriously unstable. Two major failure modes:

**Mode collapse:** The generator finds a few samples that fool the discriminator and produces only those. The distribution $p_g$ covers only a tiny subset of $p_{\text{data}}$. Visible as lack of diversity in generated outputs.

**Non-convergence:** The two networks oscillate instead of converging to equilibrium. Loss curves are often uninformative — the GAN loss does not reliably indicate sample quality.

**Mitigations:** Feature matching, minibatch discrimination, historical averaging, gradient penalty, and architectural improvements (see DCGAN, WGAN below).

---

## DCGAN: Deep Convolutional GAN

Radford et al. (2016) established a stable convolutional architecture:

**Generator architecture:**
- Start with a dense layer, reshape to 4x4 feature maps.
- Series of transposed convolutions (fractionally-strided) doubling spatial resolution each step.
- Batch normalization in all layers except the output.
- ReLU activations in intermediate layers; Tanh in the output layer.

**Discriminator architecture:**
- Standard convolutions with stride 2 (replacing pooling).
- Batch normalization.
- LeakyReLU with slope 0.2.
- No fully-connected layers at the end (fully convolutional).

**Key DCGAN guidelines:**
- Replace any pooling layers with strided convolutions.
- Use batch normalization in both $G$ and $D$.
- Remove fully-connected hidden layers.
- Use ReLU in $G$ except the output layer; use LeakyReLU in $D$.

---

## WGAN and WGAN-GP

Wasserstein GAN (Arjovsky et al., 2017) replaces the Jensen-Shannon divergence with the **Wasserstein distance** (Earth Mover's Distance):

$$W(p_r, p_g) = \inf_{\gamma \in \Pi(p_r, p_g)} \mathbb{E}_{(x, y) \sim \gamma}[\|x - y\|]$$

This provides meaningful gradients even when the real and generated distributions are disjoint.

**WGAN changes:**
- Remove the sigmoid from $D$'s output (it's now a "critic," not a classifier).
- Use weight clipping to enforce 1-Lipschitz constraint.
- Train the critic many more steps than the generator.
- Use RMSProp or Adam with lower $\beta_1$.

**WGAN-GP (Gradient Penalty):** Replaces the hacky weight clipping with a gradient penalty term added to the critic loss:

$$\lambda \cdot \mathbb{E}_{\hat{x}}[(\|\nabla_{\hat{x}} D(\hat{x})\|_2 - 1)^2]$$

where $\hat{x}$ is sampled uniformly along straight lines between real and generated samples. This yields more stable training and better sample quality.

---

## Conditional GAN (cGAN)

Conditioning both $G$ and $D$ on auxiliary information $y$ (e.g., class labels) allows controlled generation:

$$\min_G \max_D \mathbb{E}_{x,y}[\log D(x, y)] + \mathbb{E}_{z,y}[\log (1 - D(G(z, y), y))]$$

The generator takes both noise $z$ and label $y$ as input; the discriminator evaluates both the image and whether it matches the condition.

---

## StyleGAN and CycleGAN

### StyleGAN (Karras et al., 2019)

Key innovations:
- **Progressive growing:** Start training with 4x4 resolution, gradually add layers for higher resolution.
- **Mapping network:** Maps $z$ to an intermediate latent space $w$ before feeding into synthesis network.
- **Adaptive Instance Normalization (AdaIN):** Controls style at each resolution independently.
- **Style mixing:** Regularization technique where two different $w$ vectors control different layers.
- Achieves state-of-the-art high-resolution face generation.

### CycleGAN (Zhu et al., 2017)

Enables **unpaired** image-to-image translation (e.g., horses to zebras without paired examples).

**Cycle consistency loss:** If you translate $A \to B \to A$, the result should match the original:

$$\mathcal{L}_{\text{cycle}}(G, F) = \mathbb{E}_{x \sim p_A}[\|F(G(x)) - x\|_1] + \mathbb{E}_{y \sim p_B}[\|G(F(y)) - y\|_1]$$

Two generators $(G: A \to B, F: B \to A)$ and two discriminators $(D_A, D_B)$ are trained jointly.

---

## Evaluation Metrics

**FID (Frechet Inception Distance):** Measures the distance between real and generated distributions in the Inception v3 feature space. Lower is better. FID correlates well with human judgment and detects mode collapse.

$$\text{FID} = \|\mu_r - \mu_g\|^2 + \operatorname{Tr}(\Sigma_r + \Sigma_g - 2(\Sigma_r \Sigma_g)^{1/2})$$

**IS (Inception Score):** Measures both quality (high confidence predictions) and diversity (uniform marginal label distribution). Higher is better. Less reliable than FID for many settings.

---

## Applications

- **Image generation:** Photorealistic faces, objects, scenes (StyleGAN).
- **Super-resolution:** SRGAN, ESRGAN — upscale low-res images while adding plausible detail.
- **Image-to-image translation:** Style transfer, semantic segmentation to photo, day-to-night.
- **Data augmentation:** Generate additional training samples for downstream tasks.
- **Text-to-image:** DALL-E, Stable Diffusion (building on GAN concepts but using diffusion models).
- **Video generation and prediction.**
- **Drug discovery:** Generate molecular structures with desired properties.
