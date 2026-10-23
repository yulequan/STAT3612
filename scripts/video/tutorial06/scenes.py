"""Focus targets for the 34 Tutorial 06 slides.

Each cue has the exact spoken phrase used to time the focus change and a box in
PDF points [x0, y0, x1, y1]. Boxes are deliberately padded so the amber ring
does not cut through text. No pointer is drawn in the full video.
"""

SCENES = [
    {
        'page': 1,
        'id': '01-title',
        'cues': [
            {'phrase': 'Welcome to Tutorial Six', 'box': [30, 52, 338, 142]},
        ],
    },
    {
        'page': 2,
        'id': '02-outline',
        'cues': [
            {'phrase': 'We begin with data', 'box': [14, 46, 325, 63]},
            {'phrase': 'Next, models', 'box': [14, 113, 333, 130]},
            {'phrase': 'Evaluation comes next', 'box': [14, 136, 334, 153]},
            {'phrase': 'Finally, I introduce the group project', 'box': [14, 158, 332, 175]},
        ],
    },
    {
        'page': 3,
        'id': '03-time-series',
        'cues': [
            {'phrase': 'Tabular data gives one row per patient', 'box': [14, 45, 145, 128]},
            {'phrase': 'Here patient A has heart rate', 'box': [195, 45, 390, 152]},
            {'phrase': 'The values matter, but so do their order', 'box': [80, 181, 372, 198]},
        ],
    },
    {
        'page': 4,
        'id': '04-data-structures',
        'cues': [
            {'phrase': 'On the left, a table', 'box': [14, 45, 215, 142]},
            {'phrase': 'On the right, a sequence tensor', 'box': [225, 45, 395, 145]},
            {'phrase': 'Our synthetic ICU cohort has one hundred patients', 'box': [225, 164, 395, 200]},
            {'phrase': 'When you load data, check which axis is time', 'box': [225, 45, 395, 68]},
        ],
    },
    {
        'page': 5,
        'id': '05-tasks',
        'cues': [
            {'phrase': 'All four tasks share the same input', 'box': [14, 45, 280, 67]},
            {'phrase': 'Forecasting predicts the next H hours', 'box': [14, 95, 355, 113]},
            {'phrase': 'Classification predicts whether a future event occurs', 'box': [14, 114, 392, 130]},
            {'phrase': 'Sequence labeling predicts a state', 'box': [14, 130, 390, 147]},
            {'phrase': 'Anomaly detection returns a score per hour', 'box': [14, 149, 382, 165]},
            {'phrase': 'Before modeling, write down the output shape', 'box': [14, 168, 405, 186]},
        ],
    },
    {
        'page': 6,
        'id': '06-characteristics',
        'cues': [
            {'phrase': 'The left panel shows a trend', 'box': [14, 44, 180, 146]},
            {'phrase': 'The middle panel shows a daily rhythm', 'box': [183, 44, 300, 146]},
            {'phrase': 'The right panel shows a sudden change', 'box': [305, 44, 443, 146]},
            {'phrase': 'Order is the common thread', 'box': [14, 144, 420, 162]},
            {'phrase': 'Ask whether the pattern is a trend', 'box': [14, 195, 386, 214]},
        ],
    },
    {
        'page': 7,
        'id': '07-modeling-approach',
        'cues': [
            {'phrase': 'One practical approach is to compress the history into features', 'box': [24, 50, 425, 105]},
            {'phrase': 'Hourly readings become a small set of numbers', 'box': [24, 55, 150, 105]},
            {'phrase': 'A logistic model or a tree ensemble maps those features', 'box': [240, 55, 315, 105]},
            {'phrase': 'The key question is on the slide', 'box': [108, 149, 345, 166]},
        ],
    },
    {
        'page': 8,
        'id': '08-level-recency-change',
        'cues': [
            {'phrase': 'Patient A rises from 60 to 120', 'box': [80, 54, 345, 92]},
            {'phrase': 'Both have mean 90', 'box': [14, 138, 295, 154]},
            {'phrase': 'The latest value separates them', 'box': [14, 153, 292, 168]},
            {'phrase': 'The change, latest minus earliest', 'box': [14, 168, 310, 183]},
        ],
    },
    {
        'page': 9,
        'id': '09-summaries',
        'cues': [
            {'phrase': 'Overall level: the mean heart rate', 'box': [14, 47, 330, 84]},
            {'phrase': 'Change: the recent six-hour mean', 'box': [14, 91, 365, 130]},
            {'phrase': 'Extremes: maximum heart rate', 'box': [14, 136, 346, 175]},
        ],
    },
    {
        'page': 10,
        'id': '10-task-definition',
        'cues': [
            {'phrase': 'We observe vitals from hour zero', 'box': [32, 76, 238, 100]},
            {'phrase': 'The prediction cutoff is the end of hour twenty-three', 'box': [210, 52, 305, 72]},
            {'phrase': 'The target is sepsis onset during hours twenty-four to twenty-nine', 'box': [264, 76, 410, 100]},
            {'phrase': 'The cohort is patients who do not already have sepsis', 'box': [14, 173, 295, 190]},
            {'phrase': 'The input window, the target window, and the cohort definition', 'box': [14, 128, 330, 190]},
        ],
    },
    {
        'page': 11,
        'id': '11-gaps',
        'cues': [
            {'phrase': 'Not measured means no reading or test was ordered', 'box': [14, 161, 410, 178]},
            {'phrase': 'A charting gap means the value exists', 'box': [14, 184, 398, 200]},
            {'phrase': 'Irregular timing means readings arrive at event times', 'box': [14, 207, 415, 223]},
            {'phrase': 'Patient A shows a long gap around hours six to twelve', 'box': [245, 58, 360, 145]},
            {'phrase': 'Missing is not zero', 'box': [245, 58, 360, 145]},
        ],
    },
    {
        'page': 12,
        'id': '12-filling-one-gap',
        'cues': [
            {'phrase': 'Last value carried forward keeps the last level', 'box': [14, 45, 120, 145]},
            {'phrase': 'Mean or median is simple and stable', 'box': [120, 45, 235, 145]},
            {'phrase': 'Linear interpolation is smooth for short gaps', 'box': [235, 45, 340, 145]},
            {'phrase': 'A better default is to keep the trace', 'box': [340, 45, 440, 145]},
            {'phrase': 'Choose the fill method on validation data', 'box': [14, 215, 410, 232]},
        ],
    },
    {
        'page': 13,
        'id': '13-grid',
        'cues': [
            {'phrase': 'Irregular readings need a grid', 'box': [14, 44, 230, 170]},
            {'phrase': 'for the project, one row per day', 'box': [235, 44, 435, 170]},
            {'phrase': 'The empty-bin rule is crucial', 'box': [138, 116, 178, 150]},
            {'phrase': 'In an event log, an empty day means zero clicks', 'box': [235, 44, 435, 170]},
            {'phrase': 'This one distinction, zero versus unknown', 'box': [14, 218, 395, 235]},
        ],
    },
    {
        'page': 14,
        'id': '14-pandas',
        'cues': [
            {'phrase': 'On the left, events become a daily grid', 'box': [14, 47, 205, 160]},
            {'phrase': 'On the right, readings become an hourly grid', 'box': [225, 47, 435, 160]},
            {'phrase': 'The missing indicator is a separate column', 'box': [225, 143, 435, 160]},
            {'phrase': 'Development data means explore these choices', 'box': [14, 173, 395, 204]},
        ],
    },
    {
        'page': 15,
        'id': '15-feature-python',
        'cues': [
            {'phrase': 'This code builds the feature table', 'box': [14, 52, 380, 175]},
            {'phrase': 'Mean and maximum are straightforward', 'box': [14, 89, 255, 115]},
            {'phrase': 'The last six-hour mean and the previous six-hour mean', 'box': [14, 114, 355, 165]},
            {'phrase': 'Then the question at the bottom', 'box': [170, 199, 285, 216]},
        ],
    },
    {
        'page': 16,
        'id': '16-classifiers',
        'cues': [
            {'phrase': 'Logistic regression computes a linear score', 'box': [14, 48, 210, 135]},
            {'phrase': 'Tree-based methods', 'box': [225, 48, 390, 115]},
            {'phrase': 'Always start with a baseline', 'box': [14, 139, 330, 158]},
        ],
    },
    {
        'page': 17,
        'id': '17-sequence-models',
        'cues': [
            {'phrase': 'An encoder, g with parameters theta', 'box': [40, 52, 210, 105]},
            {'phrase': 'A task head then maps that representation', 'box': [340, 52, 410, 105]},
            {'phrase': 'The important idea is the separation', 'box': [14, 128, 365, 145]},
            {'phrase': 'Training uses a suitable objective', 'box': [14, 173, 397, 203]},
        ],
    },
    {
        'page': 18,
        'id': '18-rnn',
        'cues': [
            {'phrase': 'The simplest sequence encoder is a recurrent network', 'box': [40, 52, 420, 125]},
            {'phrase': 'The hidden state is the memory', 'box': [14, 153, 290, 170]},
            {'phrase': 'The limitation is practical', 'box': [14, 176, 370, 192]},
        ],
    },
    {
        'page': 19,
        'id': '19-gru',
        'cues': [
            {'phrase': 'A gated recurrent unit, or G R U, adds gates', 'box': [20, 48, 100, 190]},
            {'phrase': 'The reset gate controls', 'box': [230, 48, 430, 95]},
            {'phrase': 'The update gate balances', 'box': [230, 103, 430, 150]},
            {'phrase': 'A long short-term memory model', 'box': [230, 157, 438, 190]},
        ],
    },
    {
        'page': 20,
        'id': '20-transformer',
        'cues': [
            {'phrase': 'Self-attention lets each hour look at other hours', 'box': [75, 58, 380, 120]},
            {'phrase': 'The formula on the slide is the standard attention operation', 'box': [125, 125, 325, 160]},
            {'phrase': 'Intuitively, a query says what to look for', 'box': [14, 164, 438, 181]},
            {'phrase': 'Because attention alone has no notion of order', 'box': [14, 187, 282, 203]},
        ],
    },
    {
        'page': 21,
        'id': '21-masks',
        'cues': [
            {'phrase': 'For a whole observed window', 'box': [14, 45, 365, 75]},
            {'phrase': 'For an alerting task', 'box': [14, 81, 405, 110]},
            {'phrase': 'For forecasting, we train autoregressively', 'box': [14, 117, 399, 146]},
            {'phrase': 'For variable-length sequences', 'box': [14, 153, 380, 168]},
        ],
    },
    {
        'page': 22,
        'id': '22-arima-pictures',
        'cues': [
            {'phrase': 'Start with the observed levels', 'box': [25, 55, 110, 90]},
            {'phrase': 'Difference the series d times', 'box': [110, 55, 195, 90]},
            {'phrase': 'Fit an autoregressive part and a moving-average part', 'box': [200, 55, 300, 90]},
            {'phrase': 'The AR part uses the last p values', 'box': [105, 95, 350, 125]},
            {'phrase': 'Then restore the levels', 'box': [300, 55, 420, 90]},
            {'phrase': 'For example, with p, d, q', 'box': [14, 172, 422, 190]},
        ],
    },
    {
        'page': 23,
        'id': '23-differencing',
        'cues': [
            {'phrase': 'With d equal to zero', 'box': [14, 44, 180, 148]},
            {'phrase': 'With d equal to one', 'box': [180, 44, 310, 148]},
            {'phrase': 'With d equal to two', 'box': [310, 44, 443, 148]},
            {'phrase': 'So d is not a knob to maximize', 'box': [14, 155, 420, 216]},
        ],
    },
    {
        'page': 24,
        'id': '24-arima-variants',
        'cues': [
            {'phrase': 'AR, MA, and ARMA use no differencing', 'box': [14, 69, 362, 84]},
            {'phrase': 'ARIMA adds differencing', 'box': [14, 84, 367, 99]},
            {'phrase': 'Seasonal ARIMA, or SARIMA', 'box': [14, 99, 440, 114]},
            {'phrase': 'ARIMA with external predictors', 'box': [14, 114, 428, 129]},
            {'phrase': 'The seasonal lag picture at the bottom', 'box': [75, 155, 390, 235]},
        ],
    },
    {
        'page': 25,
        'id': '25-model-comparison',
        'cues': [
            {'phrase': 'A constant probability is the first reference', 'box': [14, 71, 388, 86]},
            {'phrase': 'Logistic regression uses explicit summaries', 'box': [14, 87, 440, 102]},
            {'phrase': 'Tree ensembles capture interactions', 'box': [14, 103, 414, 118]},
            {'phrase': 'Recurrent networks and gated recurrent units', 'box': [14, 120, 432, 134]},
            {'phrase': 'Transformers use attention across hours', 'box': [14, 136, 420, 151]},
            {'phrase': 'The last row is the most important', 'box': [14, 154, 350, 170]},
        ],
    },
    {
        'page': 26,
        'id': '26-validation',
        'cues': [
            {'phrase': 'We need three parts: train, validation, and test', 'box': [55, 55, 400, 85]},
            {'phrase': 'For new patients, group by patient', 'box': [14, 95, 433, 123]},
            {'phrase': 'For future admissions, split by time', 'box': [14, 130, 388, 160]},
            {'phrase': 'You may develop freely on train and validation', 'box': [14, 167, 440, 183]},
            {'phrase': 'But once you freeze the pipeline', 'box': [14, 189, 400, 205]},
        ],
    },
    {
        'page': 27,
        'id': '27-leakage',
        'cues': [
            {'phrase': 'First, the prediction cutoff', 'box': [14, 44, 380, 73]},
            {'phrase': 'Second, the evaluation unit', 'box': [14, 80, 425, 109]},
            {'phrase': 'Third, the final test', 'box': [14, 116, 413, 145]},
            {'phrase': 'Finally, remember that validation is development', 'box': [14, 158, 420, 187]},
        ],
    },
    {
        'page': 28,
        'id': '28-log-loss',
        'cues': [
            {'phrase': 'Log loss measures probability quality', 'box': [115, 58, 335, 95]},
            {'phrase': 'A septic patient predicted at 0.60', 'box': [78, 125, 375, 140]},
            {'phrase': 'The same patient predicted at 0.90', 'box': [78, 138, 375, 153]},
            {'phrase': 'A patient without sepsis predicted at 0.90', 'box': [78, 152, 375, 167]},
        ],
    },
    {
        'page': 29,
        'id': '29-evaluation',
        'cues': [
            {'phrase': 'Log loss is not the only view', 'box': [14, 47, 335, 85]},
            {'phrase': 'Calibration asks whether a predicted twenty percent risk', 'box': [14, 92, 375, 107]},
            {'phrase': 'Decision errors, precision and recall', 'box': [14, 114, 310, 129]},
            {'phrase': 'Slices check performance', 'box': [14, 137, 382, 152]},
        ],
    },
    {
        'page': 30,
        'id': '30-summary',
        'cues': [
            {'phrase': 'On the left, temporal features plus a standard model', 'box': [50, 100, 200, 145]},
            {'phrase': 'On the right, a learned representation', 'box': [255, 100, 385, 145]},
            {'phrase': 'Both end in a task-specific output', 'box': [65, 171, 390, 187]},
        ],
    },
    {
        'page': 31,
        'id': '31-project-task',
        'cues': [
            {'phrase': 'The input is days zero to twenty-eight', 'box': [42, 50, 252, 96]},
            {'phrase': 'The prediction cutoff is the end of day twenty-eight', 'box': [195, 98, 315, 112]},
            {'phrase': 'The outcome is days twenty-nine to forty-two', 'box': [264, 50, 410, 96]},
            {'phrase': 'train.csv is labeled', 'box': [14, 169, 345, 185]},
            {'phrase': 'The VLE events Parquet file', 'box': [14, 192, 372, 222]},
        ],
    },
    {
        'page': 32,
        'id': '32-file-formats',
        'cues': [
            {'phrase': 'CSV is portable', 'box': [14, 69, 395, 83]},
            {'phrase': 'Parquet is typed', 'box': [14, 84, 417, 97]},
            {'phrase': 'JSON is convenient', 'box': [14, 98, 420, 137]},
            {'phrase': 'Pickle is fast', 'box': [14, 137, 412, 151]},
            {'phrase': 'The code shows the project files', 'box': [14, 169, 402, 232]},
        ],
    },
    {
        'page': 33,
        'id': '33-starting-questions',
        'cues': [
            {'phrase': 'Representation: which parts', 'box': [14, 47, 314, 62]},
            {'phrase': 'Baseline: what is the simplest', 'box': [14, 69, 334, 84]},
            {'phrase': 'Validation: how will you handle', 'box': [14, 92, 440, 107]},
            {'phrase': 'Improvement: does a change', 'box': [14, 114, 340, 129]},
            {'phrase': 'Instructions: read the project brief', 'box': [14, 146, 315, 176]},
        ],
    },
    {
        'page': 34,
        'id': '34-further-reading',
        'cues': [
            {'phrase': 'scikit-learn for features and splits', 'box': [14, 80, 440, 110]},
            {'phrase': 'pandas for data formats', 'box': [14, 116, 418, 132]},
            {'phrase': 'PyTorch for sequence models', 'box': [14, 139, 410, 168]},
            {'phrase': 'the Forecasting: Principles and Practice text', 'box': [14, 174, 430, 205]},
            {'phrase': 'Contact details are on the slide', 'box': [14, 216, 270, 232]},
        ],
    },
]

SAMPLE_PAGES = {1, 2, 3, 4}
