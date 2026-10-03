export type LearningSection = {
  title: string
  paragraphs: string[]
  equation: string
  notation: [string, string][]
  insight: string
  functions: string[]
  notebook: string
  challenge: string
  starter: string
}
export const learning: Record<string, LearningSection> = {
  data: {
    title: 'The first modelling decision is what an example means.',
    paragraphs: [
      'To us, the image is a handwritten digit. To a classifier, it is a list of measurements paired with a target. We choose one pixel at one location as a feature, one complete image as an example, and the digit identity as the label.',
      'Flattening the image keeps all 784 values and their order. What it does not do is tell the model that neighbouring positions should be treated similarly. That assumption belongs to the model—not to the reshape operation. Keep this distinction in mind when we reach convolution.',
    ],
    equation:
      'X\\in\\mathbb{R}^{n\\times784},\\quad \\mathbf{x}_i\\in\\mathbb{R}^{784},\\quad y_i\\in\\{0,1\\}',
    notation: [
      ['n', 'Number of examples in the selected split.'],
      ['X_{ij}', 'Intensity at pixel position j in example i.'],
      ['y_i=0\\;/\\;y_i=1', 'Our convention: 3 / 8. These numbers encode categories.'],
    ],
    insight:
      'Train, validation and test describe different uses of data. Repeatedly checking a test set while choosing a model turns it into another validation set.',
    functions: ['load_data'],
    notebook: '§1 · Meet the data',
    challenge:
      'Find a bright pixel and a blank pixel in the same image. Recover their row and column from the flattened index, and verify that the values are unchanged.',
    starter:
      'image = images[0]\nx = image.reshape(-1)\nj = int(np.argmax(x))\nrow, col = divmod(j, 28)\nprint("image shape:", image.shape, "row shape:", x.shape)\nprint("index / row / column:", j, row, col)\nprint("same value:", x[j], image[row, col])',
  },
  prepare: {
    title: 'Choose the input to match the task, not the appearance of the picture.',
    paragraphs: [
      'Dividing intensities by 255 preserves their relative values while changing the numerical scale. The gradient depends on that scale, so a learning rate that works on 0–1 inputs may behave very differently on 0–255 inputs. Scaling is not the same as removing information.',
      'Blur and edge extraction do change the representation: they emphasise some patterns and suppress others. Augmentation changes the training examples instead. It is justified only when the transformation preserves the intended label. A large rotation, for example, is not automatically harmless for every digit task.',
    ],
    equation:
      '\\mathbf{x}_{\\mathrm{scaled}}=\\frac{\\mathbf{x}_{\\mathrm{raw}}}{255},\\qquad \\mathbf{x}_{\\mathrm{feature}}=\\phi(\\mathbf{x}_{\\mathrm{scaled}})',
    notation: [
      ['\\phi', 'A chosen feature transformation, such as blur or edges.'],
      [
        '\\phi_{\\mathrm{train}}=\\phi_{\\mathrm{eval}}',
        'Apply the same preprocessing at evaluation time.',
      ],
    ],
    insight:
      'A picture that looks cleaner to a human is not necessarily easier to classify. Compare representations using the same split and a clearly stated training setup.',
    functions: ['features', 'transform'],
    notebook: '§2 · Prepare the inputs',
    challenge:
      'Change the blur strength. Describe what happens to high-frequency detail and to the numerical range. Which information might distinguish a 3 from an 8?',
    starter:
      'image = images[0]\nsigma = 1.0  # try 0.5, 1.0, 2.0\nblurred = transform(image, "blur", sigma)\nprint("original range:", image.min(), image.max())\nprint("blurred range:", blurred.min(), blurred.max())\nprint("mean absolute change:", np.abs(blurred - image).mean())',
  },
  model: {
    title: 'A linear score combines evidence. A sigmoid gives it a probability scale.',
    paragraphs: [
      'Each weight says how much a pixel contributes to the score. Positive contributions favour an 8, negative contributions favour a 3, and the bias shifts the score for every image. A weight only contributes when its corresponding input is nonzero.',
      'The sigmoid is nonlinear, but this classifier still has a linear decision boundary: a probability threshold of 0.5 is exactly a score threshold of zero. The model cannot express arbitrary interactions between pixels just because its output is a probability.',
    ],
    equation:
      'z=\\sum_{j=1}^{784}w_jx_j+b,\\qquad p(y=1\\mid\\mathbf{x})=\\sigma(z)=\\frac{1}{1+e^{-z}}',
    notation: [
      ['w_j', 'Learned contribution per unit of feature j.'],
      ['b', 'Learned intercept, shared across examples.'],
      ['p\\geq0.5\\iff z\\geq0', 'The classification rule used in this tutorial.'],
    ],
    insight:
      'Logistic regression is a useful transparent baseline, not a requirement for image classification. Its decision boundary, assumptions and failure modes are easy to inspect.',
    functions: ['sigmoid'],
    notebook: '§3 · Prediction and loss',
    challenge:
      'Start with zero weights. Change only the bias, then give one inked pixel a positive weight. Explain which change affects all images and which depends on the image.',
    starter:
      'x = X_train[0]\nw = np.zeros(x.size)\nb = 0.0\nj = int(np.argmax(x))\nw[j] = 2.0  # try -2.0\nz = x @ w + b\nprint("chosen pixel:", j, "contribution:", x[j] * w[j])\nprint("score:", z, "p(8):", float(sigmoid(z)))',
  },
  loss: {
    title: 'A useful training objective measures how wrong, not only whether wrong.',
    paragraphs: [
      'Accuracy changes only when a prediction crosses the decision threshold. It gives no useful local signal for most small parameter changes. Cross-entropy changes smoothly with the score and penalises confidently incorrect predictions strongly.',
      'For a true 8, the contribution is −log(p); for a true 3, it is −log(1−p). Minimising their average is equivalent to maximising the model’s likelihood for the observed labels under a Bernoulli model. It is a fitting objective, not a guarantee that probabilities will be calibrated on new data.',
    ],
    equation:
      'L(\\mathbf{w},b)=\\frac{1}{n}\\sum_{i=1}^n\\left[-y_i\\log p_i-(1-y_i)\\log(1-p_i)\\right]',
    notation: [
      ['p_i=\\sigma(\\mathbf{w}^\\top\\mathbf{x}_i+b)', 'Predicted probability of class 1.'],
      ['L', 'Mean training loss; smaller is better on the measured examples.'],
    ],
    insight:
      'Loss and accuracy answer different questions. Two models can have the same accuracy and different loss, because their confidence differs.',
    functions: ['loss'],
    notebook: '§3 · Prediction and loss',
    challenge:
      'Construct two predictions with the same classification but different loss. Then flip the true label. Explain why confidence can be either helpful or costly.',
    starter:
      'y = 1  # then try 0\nfor p in [0.01, 0.4, 0.51, 0.99]:\n    cross_entropy = -y * np.log(p) - (1-y) * np.log(1-p)\n    print(f"p={p:.2f}, class={int(p >= .5)}, loss={cross_entropy:.3f}")',
  },
  update: {
    title: 'The chain rule connects a prediction error to every parameter.',
    paragraphs: [
      'For sigmoid plus cross-entropy, the derivative with respect to the score simplifies to p−y. The score depends on weight j with derivative xⱼ. Multiplying these terms assigns a share of the error signal to each feature.',
      'A gradient points towards local increase of the loss. Gradient descent moves in the opposite direction, with a distance controlled by the learning rate. For a batch, average the examples’ contributions. A sufficiently small full-gradient step decreases a smooth objective locally; a stochastic step need not reduce the full-dataset loss.',
    ],
    equation:
      '\\frac{\\partial\\ell}{\\partial z}=p-y,\\quad\\frac{\\partial\\ell}{\\partial w_j}=(p-y)x_j,\\quad w_j^{\\mathrm{new}}=w_j-\\eta(p-y)x_j',
    notation: [
      ['\\eta>0', 'Learning rate: how far to move along the update direction.'],
      ['p-y', 'Signed error signal at the model score.'],
    ],
    insight:
      'On a true 8 with p=0.5 and a positive pixel value, the gradient is negative. Subtracting it increases the weight. The two signs matter more than memorising the code.',
    functions: ['step'],
    notebook: '§4 · Learn from one example',
    challenge:
      'Choose a true 3 and a true 8. Predict the sign of the bias update before running each. Find a blank pixel and explain why its weight does not move in that step.',
    starter:
      'i = int(np.flatnonzero(y_train == 1)[0])  # try class 0\nX, y = X_train[i:i+1], y_train[i:i+1]\nw, b = np.zeros(X.shape[1]), 0.0\nw_new, b_new = step(w, b, X, y, lr=0.1)\nj = int(np.argmax(X[0]))\nprint("label:", y[0], "bias:", b_new)\nprint("pixel:", X[0, j], "new weight:", w_new[j])\nprint("new p(8):", sigmoid(X @ w_new + b_new))',
  },
  train: {
    title: 'Training is repeated estimation and correction.',
    paragraphs: [
      'One example tells us little about the whole dataset. A minibatch averages several signals and gives a less noisy estimate than a single example, while costing less per update than the full training set. Shuffling changes which examples meet in each batch.',
      'Epochs count passes through the data; updates count parameter changes. Changing batch size changes the number of updates per epoch. Learning rate, batch size and input scale interact, so compare controlled experiments rather than assuming one setting is universally best.',
    ],
    equation:
      '\\mathbf{w}_{t+1}=\\mathbf{w}_t-\\eta\\underbrace{\\frac{1}{|B_t|}\\sum_{i\\in B_t}(p_i-y_i)\\mathbf{x}_i}_{\\text{minibatch gradient}}',
    notation: [
      ['B_t', 'The set of training examples used at update t.'],
      ['\\lceil n/|B_t|\\rceil', 'Updates per epoch, for the fixed batch size used here.'],
    ],
    insight:
      'A falling training curve shows better fit to training data. Whether the model is becoming more useful on new examples is a separate question answered by validation.',
    functions: ['train_epochs'],
    notebook: '§5 · Build the training loop',
    challenge:
      'Compare two batch sizes at equal epochs, then calculate their update counts. Would your conclusion change if you compared at equal updates instead?',
    starter:
      'for batch in [16, 128]:\n    model = train(X_train, y_train, X_val, y_val,\n                  lr=0.1, epochs=5, batch=batch)\n    last = model["history"][-1]\n    print("batch:", batch, "updates:", 5 * int(np.ceil(len(y_train)/batch)))\n    print("validation:", last["validation"])',
  },
  evaluate: {
    title: 'Make the next experiment answer a specific question.',
    paragraphs: [
      'A confusion matrix separates the kinds of errors; individual examples reveal whether those errors share a pattern. A one-pixel translation is a controlled probe of how the classifier depends on position. It is evidence about that particular transformation, not a complete diagnosis of every possible failure.',
      'Propose one change, state what you expect, and compare on validation data. If you augment with shifted copies, training takes more updates at the same epoch count. If you replace the representation, the old weights no longer describe the same model. Keep the comparison and its limits explicit.',
    ],
    equation: '\\operatorname{accuracy}=\\frac{1}{n}\\sum_{i=1}^n\\mathbb{1}[\\hat y_i=y_i]',
    notation: [
      ['\\hat y_i', 'Predicted class, obtained by thresholding the probability.'],
      ['\\mathbb{1}[\\cdot]', '1 when the condition is true, 0 otherwise.'],
    ],
    insight:
      'An unsuccessful intervention is still useful if the experiment was designed to distinguish plausible explanations. Record what changed, what stayed fixed, and what the result does not establish.',
    functions: ['metrics'],
    notebook: '§6–7 · Investigate, choose, evaluate',
    challenge:
      'Replace logistic regression with a nearest-centroid classifier. It needs no SGD. Compare validation accuracy, then explain why the Euclidean centroid rule still has a linear decision boundary.',
    starter:
      'centres = np.stack([X_train[y_train == c].mean(axis=0) for c in [0, 1]])\ndistance = ((X_val[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2)\nprediction = distance.argmin(axis=1)\nprint("Nearest-centroid validation accuracy:", (prediction == y_val).mean())\nprint("No gradient descent was needed to fit this baseline.")',
  },
  beyond: {
    title: 'Keep the task. Reconsider the assumptions.',
    paragraphs: [
      'Nothing about image classification requires logistic regression. We used it because the entire learning loop stays visible. A nonlinear feature map followed by logistic regression, an MLP, a CNN, a kernel method or a nearest-neighbour rule can make different assumptions about the same task.',
      'Separate two questions: does the model need feature interactions, and should a useful local pattern be recognised at several positions? Hidden nonlinear layers address the first. Convolution adds locality and weight sharing, which are especially useful for images. More capacity alone is not a promise of better validation performance.',
    ],
    equation:
      '\\underbrace{\\sigma(\\mathbf{w}^\\top\\mathbf{x}+b)}_{\\text{linear classifier}}\\quad\\longrightarrow\\quad\\underbrace{\\sigma(\\mathbf{v}^\\top\\phi_\\theta(\\mathbf{x})+c)}_{\\text{learned features + classifier}}',
    notation: [
      [
        '\\phi_\\theta',
        'A learned representation: for example a hidden layer or convolutional network.',
      ],
      ['\\theta,\\mathbf{v},c', 'Parameters typically learned jointly from a training objective.'],
    ],
    insight:
      'Convolution is approximately translation-equivariant away from boundary effects: shifting the input shifts the feature map. It is not, by itself, a guarantee of invariant class predictions.',
    functions: ['convolution_map'],
    notebook: '§8 · Beyond the baseline',
    challenge:
      'Use the XOR example below to show why an interaction helps. Then ask what would be needed to learn that representation rather than hand-design it.',
    starter:
      'X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)\ny = np.array([0, 1, 1, 0])\ninteraction = X[:, 0] * X[:, 1]\nz = 4 * (X[:, 0] + X[:, 1] - 2 * interaction - 0.5)\nprint("targets:", y)\nprint("predictions:", (sigmoid(z) >= 0.5).astype(int))\nprint("This is linear in the expanded features, not in the original inputs.")',
  },
}
