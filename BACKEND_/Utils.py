## Utils file to store the necessary script required to inference the model ##

# Class preprocessing defined #
import re
from collections import Counter
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import numpy as np
import unicodedata
import pickle
from sklearn.ensemble import IsolationForest
import nltk

# Download required NLTK data
nltk.download('wordnet')
nltk.download('stopwords')

class TextPreprocessor:
    def __init__(self, max_len=200):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.vocab = None
        self.vocab_size = 1  # Starts with 1 for padding index 0
        self.max_len = max_len
        
    def clean_text(self, text):
        """
        Clean and normalize text
        """
        text = re.sub(r'[^a-zA-Z]', ' ', text)
        text = text.lower()
        text = text.split()
        text = [self.lemmatizer.lemmatize(word) for word in text if word not in self.stop_words]
        return ' '.join(text)
    
    def build_vocab(self, train_texts):
        """
        Build vocabulary from training texts
        """
        word_counts = Counter()
        for text in train_texts:
            cleaned_text = self.clean_text(text)
            word_counts.update(cleaned_text.split())
            
        self.vocab = {word: i+1 for i, (word, _) in enumerate(word_counts.most_common())}
        self.vocab_size = len(self.vocab) + 1  # +1 for padding index
    
    def text_to_sequence(self, text):
        """
        Convert text to sequence of word indices
        """
        return [self.vocab.get(word, 0) for word in text.split()]
    
    def pad_sequence(self, sequence):
        """
        Pad or truncate sequence to fixed length
        """
        sequence = sequence[:self.max_len]
        padding_length = max(0, self.max_len - len(sequence))
        padded_sequence = sequence + [0] * padding_length
        return np.array(padded_sequence, dtype=np.int64)
    
    def fit(self, train_texts):
        """
        Fit the preprocessor on training texts (build vocabulary)
        """
        # Clean the training texts (but don't store them)
        _ = [self.clean_text(text) for text in train_texts]
        # Build vocabulary
        self.build_vocab(train_texts)
        
    def process(self, text):
        """
        Process a single text for inference
        Returns: torch.Tensor of shape (1, max_len) ready for model input
        """
        if not self.vocab:
            raise ValueError("Vocabulary not built. Call fit() first.")
            
        # Clean the text
        cleaned_text = self.clean_text(text)
        # Convert to sequence
        sequence = self.text_to_sequence(cleaned_text)
        # Pad sequence
        padded_sequence = self.pad_sequence(sequence)
        # Add batch dimension (model expects batch of sequences)
        return np.expand_dims(padded_sequence, axis=0)

class DriftDetector:
    def __init__(self, preprocessor, contamination=0.05, random_state=42):
        """
        preprocessor: Fitted TextPreprocessor
        contamination: Expected proportion of drifted samples
        """
        self.preprocessor = preprocessor
        self.model = IsolationForest(contamination=contamination, random_state=random_state)
        self.fitted = False

    def _is_latin(self, char):
        """
        Check if a character belongs to the Latin script.
        """
        try:
            return 'LATIN' in unicodedata.name(char)
        except ValueError:
            return False

    def extract_features(self, text):
        """
        Extracting the features to fit isolation forest
        """
        cleaned = self.preprocessor.clean_text(text)
        tokens = cleaned.split()

        if not tokens:
            return np.array([1.0, 0.0, 1.0, 0.0, 0.0])  # Edge case: empty

        # Feature 1: OOV ratio
        oov_ratio = sum(1 for t in tokens if t not in self.preprocessor.vocab) / len(tokens)
        # Feature 2: Average word length
        avg_word_len = np.mean([len(t) for t in tokens])
        # Feature 3: Non-Latin character ratio (using raw text)
        raw = text.strip()
        non_latin_ratio = sum(1 for c in raw if not self._is_latin(c)) / len(raw) if raw else 0
        # Feature 4: Transliteration-like token frequency
        translit_markers = {'nahi', 'hai', 'ka', 'kya', 'zindagi', 'tum', 'mera'}
        translit_score = sum(1 for t in tokens if t in translit_markers) / len(tokens)
        # Feature 5: Mixed alphanumeric token ratio
        mixed_token_ratio = sum(1 for t in tokens if re.search(r'[a-zA-Z]', t) and re.search(r'\d', t)) / len(tokens)

        return np.array([oov_ratio, avg_word_len, non_latin_ratio, translit_score, mixed_token_ratio])

    def fit(self, train_texts):
        features = np.array([self.extract_features(text) for text in train_texts])
        self.model.fit(features)
        self.fitted = True

    def is_drifted(self, text):
        if not self.fitted:
            raise RuntimeError("DriftDetector must be fitted first.")

        features = self.extract_features(text).reshape(1, -1)
        return self.model.predict(features)[0] == -1  # -1 = drifted

    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path):
        with open(path, 'rb') as f:
            return pickle.load(f)
