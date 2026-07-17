# RNN and LSTM: Sequential Deep Learning Models

## Overview

Recurrent Neural Networks (RNNs) are designed for sequential data — text, speech, time series — where the order of inputs matters. Unlike feed-forward networks, RNNs maintain a hidden state that captures information from previous time steps, creating a form of "memory."

---

## RNN Basic Structure

At each time step $t$, an RNN receives input $x_t$ and the previous hidden state $h_{t-1}$ to produce output $h_t$:

$$h_t = \tanh(W_h h_{t-1} + W_x x_t + b)$$

The output at each step can be derived as:

$$y_t = W_y h_t + b_y$$

The entire sequence is processed by unrolling the network through time — conceptually a deep feed-forward network where each layer shares weights $W_h, W_x, W_y$.

### Weight Sharing

A key property: the same weight matrices are applied at every time step. This allows the RNN to process variable-length sequences without a blow-up in parameter count.

---

## Backpropagation Through Time (BPTT)

Training an RNN requires unrolling it over all time steps, then backpropagating the loss:

$$\frac{\partial L}{\partial W} = \sum_{t=1}^{T} \frac{\partial L_t}{\partial W}$$

At each step, the gradient flows back through the recurrence. For the hidden-state weight $W_h$, the gradient involves a product of Jacobians:

$$\frac{\partial L}{\partial h_t} \cdot \frac{\partial h_t}{\partial h_k} = \frac{\partial L}{\partial h_t} \cdot \prod_{j=k+1}^{t} \frac{\partial h_j}{\partial h_{j-1}}$$

where each factor $\frac{\partial h_j}{\partial h_{j-1}} = \operatorname{diag}(\tanh'(\cdot)) \cdot W_h^T$.

---

## Vanishing and Exploding Gradients

The long product of Jacobians causes two famous problems:

**Vanishing gradient:** If $|\frac{\partial h_j}{\partial h_{j-1}}| < 1$, repeated multiplication drives the gradient to zero. Early time steps receive no useful learning signal; long-range dependencies are lost.

**Exploding gradient:** If $|\frac{\partial h_j}{\partial h_{j-1}}| > 1$, the gradient grows exponentially, causing unstable updates and NaN losses.

**Mitigations for vanilla RNNs:**
- Gradient clipping (cap the norm at a threshold, e.g., 1.0–5.0)
- Proper weight initialization (Xavier/Glorot)
- ReLU alternatives (but ReLU itself explodes in RNNs; use bounded activations)
- Use gated architectures (LSTM/GRU)

---

## LSTM: Long Short-Term Memory

Hochreiter & Schmidhuber (1997) introduced LSTMs to solve the vanishing gradient problem through a **cell state** $C_t$ that acts as a gradient highway, regulated by three gates.

### The Gates

**Forget gate** — decides what to discard from the previous cell state:

$$f_t = \sigma(W_f \cdot [h_{t-1}, x_t] + b_f)$$

**Input gate** — selects which new information to store:

$$i_t = \sigma(W_i \cdot [h_{t-1}, x_t] + b_i)$$

$$\tilde{C}_t = \tanh(W_C \cdot [h_{t-1}, x_t] + b_C)$$

**Cell state update** — combines forget and input signals:

$$C_t = f_t \odot C_{t-1} + i_t \odot \tilde{C}_t$$

**Output gate** — controls what the hidden state reveals:

$$o_t = \sigma(W_o \cdot [h_{t-1}, x_t] + b_o)$$

$$h_t = o_t \odot \tanh(C_t)$$

### Why LSTM Helps

The cell state $C_t$ passes through only element-wise multiplications and additions (no matrix multiply with $\tanh$), so the gradient can flow across many time steps without vanishing — the "constant error carousel."

---

## GRU: Gated Recurrent Unit

Cho et al. (2014) simplified LSTM into the GRU with two gates:

**Reset gate** — determines how much past information to forget:

$$r_t = \sigma(W_r \cdot [h_{t-1}, x_t] + b_r)$$

**Update gate** — balances old vs. new hidden state:

$$z_t = \sigma(W_z \cdot [h_{t-1}, x_t] + b_z)$$

**Candidate and final hidden state:**

$$\tilde{h}_t = \tanh(W_h \cdot [r_t \odot h_{t-1}, x_t] + b_h)$$

$$h_t = (1 - z_t) \odot h_{t-1} + z_t \odot \tilde{h}_t$$

GRU merges the cell state and hidden state, uses fewer parameters than LSTM, and often performs comparably. Good default choice when compute is limited.

---

## Bidirectional RNN (BiRNN)

A BiRNN runs two independent RNNs — one forward over the sequence, one backward — and concatenates their hidden states:

$$\overrightarrow{h_t} = \text{RNN}_{\text{forward}}(x_t, \overrightarrow{h}_{t-1})$$

$$\overleftarrow{h_t} = \text{RNN}_{\text{backward}}(x_t, \overleftarrow{h}_{t+1})$$

$$h_t^{\text{bi}} = [\overrightarrow{h_t}; \overleftarrow{h_t}]$$

This gives each output access to both past and future context. Essential for tasks like NER, POS tagging, and machine translation (encoder side).

---

## Deep (Stacked) RNN

Multiple RNN layers are stacked so the output of layer $l$ at time $t$ becomes the input to layer $l+1$:

$$h_t^{(l)} = \text{RNN}^{(l)}(h_t^{(l-1)}, h_{t-1}^{(l)})$$

Typically 2–4 layers; beyond that, diminishing returns and training instability. Dropout applied between layers (not within the recurrent connection itself, unless using variational dropout).

---

## PyTorch Example

```python
import torch
import torch.nn as nn

class LSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, output_dim):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers,
                            batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_dim * 2, output_dim)

    def forward(self, x):
        # x: (batch, seq_len, input_dim)
        out, (h_n, c_n) = self.lstm(x)
        # Use the last time step's output
        return self.fc(out[:, -1, :])
```

For GRU, swap `nn.LSTM` with `nn.GRU` — the API is identical.

---

## Applications

| Domain | Task |
|--------|------|
| NLP | Machine translation, text generation, sentiment analysis |
| Speech | ASR (speech-to-text), TTS, speaker identification |
| Time Series | Stock prediction, weather forecasting, anomaly detection |
| Video | Action recognition, frame prediction |

---

## Limitations vs. Transformer

- **Sequential bottleneck:** RNNs process tokens one by one; cannot parallelize across the sequence during training.
- **Long-range dependency:** Even with LSTM/GRU, very long sequences (500+ tokens) remain challenging.
- **No explicit pairwise interaction:** Each token only sees its predecessor's hidden state, not every other token, as self-attention does.
- For most NLP tasks today, Transformers have replaced RNNs. However, RNNs remain relevant for streaming/low-latency inference and on-device models where $O(n)$ computation is preferred over $O(n^2)$ attention.
