# Naive Bayes

## Bayes Theorem Recap

**Bayes' Theorem** describes the probability of an event based on prior knowledge of related conditions:

$$P(C \mid X) = \frac{P(X \mid C) \cdot P(C)}{P(X)}$$

where:
- $P(C \mid X)$ is the **posterior** probability of class $C$ given features $X$
- $P(X \mid C)$ is the **likelihood** of observing features $X$ given class $C$
- $P(C)$ is the **prior** probability of class $C$
- $P(X)$ is the **evidence** (marginal likelihood), a normalization constant

The predicted class is the one that maximizes the posterior (Maximum A Posteriori, or MAP):

$$\hat{y} = \arg\max_{C} P(C \mid X) = \arg\max_{C} P(X \mid C) \cdot P(C)$$

$P(X)$ is dropped because it is constant across all classes for a given input.

## The "Naive" Conditional Independence Assumption

Computing $P(X \mid C) = P(x_1, x_2, \dots, x_n \mid C)$ directly is intractable for high-dimensional data. The **naive** assumption is that features are **conditionally independent** given the class:

$$P(X \mid C) = P(x_1 \mid C) \cdot P(x_2 \mid C) \cdot \dots \cdot P(x_n \mid C) = \prod_{i=1}^{n} P(x_i \mid C)$$

This is almost always false in the real world — features frequently correlate. Yet Naive Bayes often works remarkably well, especially for text classification, because:
- The ranking of posteriors matters more than their exact values
- The independence assumption makes parameters easy to estimate from limited data
- Correlated features tend to "double-count" evidence, but the direction (toward the correct class) is often consistent

The full MAP decision rule becomes:

$$\hat{y} = \arg\max_{C} P(C) \prod_{i=1}^{n} P(x_i \mid C)$$

In practice, log-probabilities are used to avoid numerical underflow:

$$\hat{y} = \arg\max_{C} \left[ \log P(C) + \sum_{i=1}^{n} \log P(x_i \mid C) \right]$$

## Variants of Naive Bayes

### Gaussian Naive Bayes

Assumes continuous features follow a **Gaussian (normal) distribution** for each class:

$$P(x_i \mid C) = \frac{1}{\sqrt{2\pi\sigma_{C,i}^2}} \exp\left( -\frac{(x_i - \mu_{C,i})^2}{2\sigma_{C,i}^2} \right)$$

Parameters $\mu_{C,i}$ and $\sigma_{C,i}$ are estimated via MLE (sample mean and variance) from training data. Used when features are continuous and roughly normally distributed.

### Multinomial Naive Bayes

Models feature vectors as counts (e.g., word frequencies in a document). The likelihood is:

$$P(X \mid C) = \frac{(\sum_i x_i)!}{\prod_i x_i!} \prod_i p_{C,i}^{x_i}$$

where $p_{C,i}$ is the probability of feature $i$ in class $C$, estimated as:

$$p_{C,i} = \frac{N_{C,i} + \alpha}{N_C + \alpha n}$$

where $N_{C,i}$ is the count of feature $i$ in class $C$, $N_C$ is the total count of all features in class $C$, $n$ is the number of features, and $\alpha$ is the smoothing parameter.

Primary use case: **text classification** with word count features (bag-of-words).

### Bernoulli Naive Bayes

Assumes binary feature vectors (0 or 1). Likelihood:

$$P(x_i \mid C) = p_{C,i}^{x_i} \cdot (1 - p_{C,i})^{(1 - x_i)}$$

Used when features indicate presence/absence rather than frequency. Common in short-text classification where word occurrence matters more than frequency.

### Complement Naive Bayes

A variant of Multinomial NB that uses statistics from the complement of each class. Designed to address imbalanced datasets. When the imbalance is severe, standard Multinomial NB tends to favor the majority class; Complement NB corrects this.

## Laplace Smoothing

What happens if a feature value never appears in a class in the training data? Without smoothing, $P(x_i \mid C) = 0$, which zeros out the entire product. **Laplace (additive) smoothing** adds a small count $\alpha$ to all feature-class counts:

$$P(x_i \mid C) = \frac{\text{count}(x_i, C) + \alpha}{\text{count}(C) + \alpha \cdot d}$$

where $d$ is the number of distinct feature values. When $\alpha = 1$, it is standard Laplace smoothing; $\alpha < 1$ is called Lidstone smoothing. This ensures no probability is ever zero.

## Pros

- **Extremely fast**: training is $O(Nd)$, prediction is $O(d)$. One of the fastest classifiers.
- **Works well with small datasets**: parameter estimation requires minimal data (only means and variances).
- **Scales to high dimensions**: dimensionality does not hurt as much as in distance-based methods.
- **Handles irrelevant features gracefully**: they just get near-uniform probabilities and don't skew the result.
- **Probabilistic output**: well-calibrated probabilities (especially after calibration).
- **Incremental learning**: easily updated with new data (partial_fit in sklearn).
- **Interpretability**: you can inspect $P(x_i \mid C)$ to see which features drive classification.

## Cons

- **Strong independence assumption**: rarely holds in practice. Features like "height" and "weight" are clearly correlated.
- **Zero-frequency problem** without smoothing: unseen feature-class combinations zero out the posterior.
- **Not competitive on complex, structured data**: deep learning and tree ensembles usually outperform NB on tabular data with complex interactions.
- **Assumes specific distributions**: Gaussian NB assumes normality; poor fit degrades performance.
- **Sensitive to feature scaling** (Gaussian NB): features with larger variance dominate.
- **Poor probability estimates**: while the ranking is generally good, the actual probability values can be miscalibrated (often overconfident).

## sklearn Example: Text Classification

```python
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB, GaussianNB, BernoulliNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import make_pipeline

# Load text data (binary classification: alt.atheism vs soc.religion.christian)
categories = ["alt.atheism", "soc.religion.christian"]
newsgroups = fetch_20newsgroups(subset="all", categories=categories,
                                 random_state=42)

X_train, X_test, y_train, y_test = train_test_split(
    newsgroups.data, newsgroups.target, test_size=0.2, random_state=42
)

# Pipeline: vectorize text, then classify
# Option 1: CountVectorizer + MultinomialNB (standard for text)
pipeline = make_pipeline(
    CountVectorizer(stop_words="english", max_features=5000),
    MultinomialNB(alpha=1.0)  # Laplace smoothing
)

pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)

print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")
print(classification_report(y_test, y_pred,
                             target_names=newsgroups.target_names))

# Inspect most informative features for each class
nb = pipeline.named_steps["multinomialnb"]
vec = pipeline.named_steps["countvectorizer"]
feature_names = vec.get_feature_names_out()

for i, class_name in enumerate(newsgroups.target_names):
    top_indices = nb.feature_log_prob_[i].argsort()[-10:][::-1]
    top_words = [feature_names[j] for j in top_indices]
    print(f"\nTop words for {class_name}: {', '.join(top_words)}")
```

## Applications

### Spam Detection

The classic Naive Bayes application. Email features (words, sender, links) are used to compute $P(\text{spam} \mid \text{email})$. Multinomial NB with TF-IDF weighting achieves >95% accuracy on standard datasets. Features include: presence of words like "free", "win", "click here", number of exclamation marks, sender reputation.

### Sentiment Analysis

Classify text as positive, negative, or neutral. Features are n-grams (sequences of 1-3 words). Naive Bayes is a strong baseline that often rivals more complex models, especially with limited labeled data.

### Document Classification

News categorization, topic labeling, genre identification. Multinomial NB is the standard baseline; Complement NB works better for imbalanced document collections.

### Medical Diagnosis

Given symptoms (features), predict disease (class). Works well with categorical symptoms (present/absent). Prior $P(C)$ can come from disease prevalence data.

### Real-time Classification

Naive Bayes is ideal for real-time or streaming applications due to its sub-millisecond prediction time: fraud detection, chat moderation, recommendation engines.

## Comparing the Three Main Variants

| Variant | Data Type | Likelihood | Best For |
|---------|-----------|------------|----------|
| Gaussian NB | Continuous | $P(x_i \mid C) \sim \mathcal{N}(\mu_{C,i}, \sigma^2_{C,i})$ | General continuous features |
| Multinomial NB | Count/discrete | $P(X \mid C) \propto \prod p_{C,i}^{x_i}$ | Text, word counts |
| Bernoulli NB | Binary | $p^{x_i} (1-p)^{1-x_i}$ | Presence/absence features |

## Key Hyperparameters (sklearn)

| Parameter | Description |
|-----------|-------------|
| `alpha` | Additive (Laplace/Lidstone) smoothing parameter (default 1.0) |
| `fit_prior` | Whether to learn class priors from data (default True) |
| `class_prior` | Manually specified class priors (if known) |
| `var_smoothing` | (Gaussian NB) portion of largest variance added to all variances for stability |
| `binarize` | (Bernoulli NB) threshold to binarize features |
| `norm` | (Complement NB) whether to weight by second normalization |

## When to Choose Naive Bayes

Naive Bayes is the right choice when:
- You need a **fast baseline** to benchmark more complex models
- Training data is **scarce** (works well with hundreds, not millions, of samples)
- Features are reasonably **independent** (or you can engineer them to be)
- You need **real-time predictions** with very low latency
- Interpretability matters (examining word-class associations)
- The problem is **text classification** (Naive Bayes remains a top performer here)
