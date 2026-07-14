# Data Preprocessing: From Raw Data to Model-Ready

## Why Preprocessing Matters

*Garbage in, garbage out.* Raw data is rarely clean enough for direct modeling. Preprocessing transforms messy, incomplete, inconsistent data into a structured format that machine learning algorithms can learn from effectively. Skipping this step is the most common cause of model failure in production.

---

## 1. Data Cleaning

### 1.1 Missing Value Handling

| Method | Description | Best For |
|--------|-------------|----------|
| **Deletion** | Drop rows/columns with missing values | When missingness is < 5% and MCAR (Missing Completely At Random) |
| **Mean/Median/Mode Imputation** | Fill with central tendency | Quick baseline; median is robust to outliers |
| **KNN Imputation** | Impute using k-nearest neighbors | Captures local structure; expensive for large datasets |
| **Multiple Imputation** | Generate multiple plausible values, pool results | Gold standard for statistical inference; preserves uncertainty |
| **Forward/Backward Fill** | Propagate last known value | Time series with temporal dependence |
| **Missing Indicator** | Add a binary flag marking missingness | When missingness itself is informative (MNAR) |

```python
from sklearn.impute import SimpleImputer, KNNImputer
imp_mean = SimpleImputer(strategy='median')
imp_knn = KNNImputer(n_neighbors=5)
```

### 1.2 Outlier Detection

**Z-Score Method:**
Points with $|z| > 3$ are potential outliers, where $z = \frac{x - \mu}{\sigma}$. Assumes approximate normality.

**IQR Method (Tukey's Fences):**
Lower fence = $Q1 - 1.5 \times IQR$, Upper fence = $Q3 + 1.5 \times IQR$. More robust than Z-score — no normality assumption.

**Isolation Forest:** Tree-based anomaly detection. Works well for high-dimensional data and can handle clusters.

**DBSCAN:** Density-based clustering; points not assigned to any cluster are outliers. Excellent when outliers are isolated in low-density regions.

```python
from sklearn.ensemble import IsolationForest
iso = IsolationForest(contamination=0.05)
outliers = iso.fit_predict(X)  # -1 = outlier
```

### 1.3 Duplicate Removal

Always check for exact duplicates (`df.drop_duplicates()`) and near-duplicates (fuzzy matching for text). Duplicates artificially inflate training metrics and can cause data leakage if split across train/test.

### 1.4 Noise Handling

- **Binning/Smoothing:** Replace values with bin means/medians/boundaries
- **Filtering:** Moving average, Savitzky-Golay, or low-pass filters for signal data
- **Regression:** Fit a local regression (LOESS) to smooth noisy trends

---

## 2. Feature Scaling

Many algorithms (SVM, KNN, PCA, neural networks, gradient descent-based methods) are sensitive to feature scales. Tree-based models (RF, XGBoost) are scale-invariant.

### 2.1 Standardization (Z-score Normalization)

$$x' = \frac{x - \mu}{\sigma}$$

After transformation, features have $\mu = 0$, $\sigma = 1$. **Use for:** SVM, PCA, logistic regression, neural networks.

### 2.2 Min-Max Normalization

$$x' = \frac{x - x_{min}}{x_{max} - x_{min}}$$

Maps values to $[0, 1]$. **Use for:** image pixel data, distance-based algorithms when bounded input is preferred, neural networks with sigmoid/tanh activation.

### 2.3 RobustScaler

$$x' = \frac{x - \text{median}}{\text{IQR}}$$

Centers and scales using median and interquartile range. **Use for:** data with many outliers — much less influenced by extreme values than StandardScaler.

### 2.4 MaxAbsScaler

$$x' = \frac{x}{\max(|x|)}$$

Maps to $[-1, 1]$, preserves sparsity. **Use for:** sparse data (TF-IDF, one-hot encodings) where centering would destroy sparsity.

### 2.5 Power Transformations

- **Log Transform:** $\log(x + c)$ — reduces right-skewness
- **Box-Cox:** Requires strictly positive data; finds optimal lambda for normality
- **Yeo-Johnson:** Handles negative values; generalization of Box-Cox

```python
from sklearn.preprocessing import StandardScaler, RobustScaler, PowerTransformer
pt = PowerTransformer(method='yeo-johnson')
```

---

## 3. Encoding Categorical Variables

| Method | Mechanism | When to Use |
|--------|-----------|-------------|
| **Label Encoding** | Integer mapping `[A,B,C] -> [0,1,2]` | Tree-based models only; implies false ordinality for nominal features |
| **One-Hot Encoding** | Binary columns per category | Linear models, neural nets; low cardinality (< 10-15 categories) |
| **Ordinal Encoding** | Integer mapping respecting order | Ordered categories: `[low, medium, high] -> [0,1,2]` |
| **Target Encoding** | Replace category with mean of target | High-cardinality features; risk of overfitting — always use cross-validation |
| **Frequency/Count Encoding** | Replace with count or frequency | High cardinality as a quick baseline; preserves no relationship with target |

```python
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
import category_encoders as ce
te = ce.TargetEncoder(cols=['city'], smoothing=10)
```

---

## 4. Text Preprocessing

### Standard Pipeline
1. **Lowercasing** — unify case
2. **Tokenization** — split into words/subwords
3. **Stopword Removal** — remove common words (the, is, at) unless task-dependent
4. **Stemming vs Lemmatization** — Porter stemmer chops suffixes; WordNet lemmatizer produces dictionary forms. Lemmatization is slower but more accurate.
5. **Vectorization** — TF-IDF for traditional ML; Word2Vec/GloVe/BERT embeddings for deep learning

### Chinese Text Specifics
- **Segmentation is mandatory:** Chinese has no natural word boundaries. Use `jieba` for segmentation before any further processing.
- jieba supports precise mode, full mode, and search engine mode.

```python
import jieba
tokens = jieba.lcut("机器学习是人工智能的核心")
```

---

## 5. Image Preprocessing

- **Resize & Center Crop:** Standardize input dimensions for CNNs (e.g., 224x224 for ResNet)
- **Normalization:** Scale pixel values to $[0, 1]$ or standardize per-channel using ImageNet statistics
- **Data Augmentation:** Random horizontal flip, rotation ($\pm 10^\circ$), color jitter (brightness, contrast, saturation), random erasing/cutout. Essential for preventing overfitting with small image datasets.

```python
from torchvision import transforms
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
```

---

## 6. Handling Imbalanced Data

When one class dominates, models learn to predict the majority class and ignore the minority.

### Oversampling
- **SMOTE:** Generates synthetic minority samples via interpolation between neighbors
- **ADASYN:** Adaptive SMOTE — focuses on harder-to-learn minority samples

### Undersampling
- **Random Undersampling:** Drop majority samples randomly
- **Tomek Links:** Remove majority samples that are nearest neighbors of minority samples
- **NearMiss:** Select majority samples closest to minority class boundary

### Algorithm-Level Approaches
- **Class Weights:** Weight the loss function inversely proportional to class frequency
- **Ensemble Methods:** BalancedBaggingClassifier, EasyEnsemble

```python
from imblearn.over_sampling import SMOTE
from sklearn.utils.class_weight import compute_class_weight
smote = SMOTE(random_state=42)
class_weights = compute_class_weight('balanced', classes=np.unique(y), y=y)
```

---

## 7. Pipeline Integration

Never fit preprocessing on the full dataset — it causes data leakage. Use `sklearn.pipeline.Pipeline`:

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

num_pipe = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])
cat_pipe = Pipeline([
    ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
    ('encoder', OneHotEncoder(handle_unknown='ignore'))
])

preprocessor = ColumnTransformer([
    ('num', num_pipe, numeric_cols),
    ('cat', cat_pipe, categorical_cols)
])

pipeline = Pipeline([
    ('preprocess', preprocessor),
    ('classifier', LogisticRegression())
])
```

---

## 8. Common Pitfalls and Best Practices

1. **Data Leakage:** Never fit scalers, imputers, or encoders on test data. Use `fit` on train, `transform` on everything else.
2. **Ignoring Domain Knowledge:** Imputation with the mean is mathematically convenient but often physically wrong (e.g., imputing body temperature with the "mean" of 37C for a hypothermia patient).
3. **One-Hot Encoding High-Cardinality Features:** Explodes feature space. Use target encoding or embeddings.
4. **Improper Scaling Before PCA:** PCA is variance-maximizing — unscaled features with larger magnitudes dominate components.
5. **Forgetting the Validation Set:** Always split before preprocessing. Chain preprocessing in the pipeline so validation data never leaks into training.
6. **Over-augmenting:** Too aggressive augmentation can create unrealistic samples that confuse the model.
7. **Not Documenting Transformations:** Always log preprocessing parameters for reproducibility in production.
