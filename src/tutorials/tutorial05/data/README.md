# Original UCI SMS Spam Collection

**Source:** Almeida, T. A. and Gómez Hidalgo, J. M. (2011), SMS Spam Collection,
UCI Machine Learning Repository.
https://archive.ics.uci.edu/dataset/228/sms+spam+collection
Dataset DOI: https://doi.org/10.24432/C5CC84
Original archive: https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip

`SMSSpamCollection.txt` contains the original archive's `SMSSpamCollection` bytes,
unchanged; only the local filename has a `.txt` extension. Downloaded 2026-10-05.
It has 5,574 tab-separated label/message records: 4,827 ham and 747 spam.
UCI currently lists CC BY 4.0; original attribution/terms are in SOURCE-LICENSE.txt.

**Paper:** Almeida, T. A., Gómez Hidalgo, J. M., and Yamakami, A. (2011),
“Contributions to the Study of SMS Spam Filtering: New Collection and Results,”
ACM Symposium on Document Engineering. https://doi.org/10.1145/2034691.2034742

The English messages were compiled from Grumbletext (UK spam complaints), the NUS
SMS Corpus (volunteer messages, largely Singaporean students), Caroline Tagg's PhD
research and the SMS Spam Corpus v0.1 Big. It is a compiled research corpus, not a
random sample of today's inboxes. Messages are not chronologically ordered.

Why use it: short inspectable examples, explicit binary labels, manageable local training,
class imbalance and repeated messages make representation and evaluation choices visible.
These are SMS messages, without
email senders, subjects, attachments or headers. Text-classification methods transfer;
measured performance does not establish results on modern email, phishing, other
languages or another population. Constructed teaching examples illustrate the methods.

The loader checks empty/placeholder messages, normalizes case/whitespace solely for
message identity, rejects conflicting labels, and keeps one record per identity before
splitting. It reports every count and preserves retained message text. Splits are
stratified 60% train / 20% validation / 20% test (seed 3612). Five-fold CV uses training
only. Vocabulary, IDF, scaling and spline knots belong inside each fold's fitted pipeline.

SHA-256 of the unchanged original file:
7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d  src/tutorials/tutorial05/data/SMSSpamCollection.txt
