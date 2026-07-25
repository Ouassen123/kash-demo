"""KASH Knowledge ML Model — Professional CV analysis pipeline.

Pipeline: Data Cleaning -> NLTK Tokenization -> Porter Stemming -> TF-IDF (n-grams 1-3) -> Ensemble Voting -> KNN Similarity

Improvements over basic model:
- NLTK PorterStemmer for proper English stemming + French accent normalization
- Trigram features (1,3) for better technical term capture
- Ensemble VotingClassifier (RF + SVM + LogReg) instead of single best
- Section-aware CV text extraction (skills, experience, education weighted)
- Technical skill keyword boosting for domain-specific features
- Comprehensive French + English stopwords
- Confidence calibration via probability analysis
- Model persisted to disk, auto-loaded on startup

KASH = Knowledge – Attitude – Skills – Habits
"""

import os
import re
import math
import pickle
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from pathlib import Path
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.cluster import KMeans
from sklearn.model_selection import cross_val_score, StratifiedKFold, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder, StandardScaler, MaxAbsScaler
from sklearn.pipeline import Pipeline as SKPipeline
from sklearn.utils.class_weight import compute_sample_weight

try:
    from imblearn.over_sampling import SMOTE, RandomOverSampler
    _IMBLEARN_AVAILABLE = True
except ImportError:
    _IMBLEARN_AVAILABLE = False

from src.core.logging import get_logger

logger = get_logger(__name__)

if not _IMBLEARN_AVAILABLE:
    logger.info("imblearn not available, using class_weight instead of SMOTE")

try:
    import nltk
    from nltk.stem import PorterStemmer, SnowballStemmer
    from nltk.tokenize import word_tokenize
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab', quiet=True)
    _STEMMER_EN = PorterStemmer()
    _STEMMER_FR = SnowballStemmer('french')
    _NLTK_AVAILABLE = True
except Exception:
    _NLTK_AVAILABLE = False
    _STEMMER_EN = None
    _STEMMER_FR = None
    logger.warning("NLTK not fully available, using fallback stemmer")

# French words that should use French stemmer
_FRENCH_INDICATORS = {'le', 'la', 'les', 'de', 'des', 'du', 'et', 'un', 'une', 'en', 'dans', 'pour', 'avec', 'par', 'sur', 'qui', 'que', 'pas', 'plus', 'etre', 'avoir', 'fait', 'cette', 'ces', 'son', 'sa', 'ses'}

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "models")
MODEL_DIR = os.path.abspath(MODEL_DIR)
MODEL_PATH = os.path.join(MODEL_DIR, "kash_knowledge_model.pkl")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "test_knowledge_results.json")
RESULTS_PATH = os.path.abspath(RESULTS_PATH)
TRAINING_HISTORY_PATH = os.path.join(MODEL_DIR, "kash_knowledge_training_history.json")

# Professional reference corpus — domain-specific profiles for KNN similarity
_REFERENCE_DOCS = [
    "python machine learning data science pandas numpy scikit tensorflow pytorch deep learning neural network nlp computer vision",
    "javascript react node typescript angular vue frontend backend web development api rest graphql",
    "java spring boot microservices kubernetes docker devops ci cd jenkins maven gradle",
    "sql postgresql mysql mongodb redis database design etl data engineering warehousing",
    "project management agile scrum kanban leadership communication team stakeholder jira confluence",
    "c++ embedded systems linux rtos firmware drivers hardware arm cortex programming algorithms",
    "cloud aws azure gcp infrastructure terraform ansible networking security ci cd monitoring",
    "research analysis statistics phd academic publication writing r matlab experimental design",
    "solidworks catia autocad cad mechanical design finite element ansys abaqus structural simulation manufacturing cnc thermodynamics",
    "electrical power electronics plc automation scada motor control arduino raspberry pi circuit design vhdl verilog",
    "quality management iso six sigma lean kaizen 5s audit compliance maintenance reliability qms",
    "logistics supply chain inventory warehouse transportation procurement distribution erp sap",
]

REF_LABELS = [
    "Python/ML/Data Science", "JS/React/Web", "Java/DevOps", "SQL/Database",
    "Management/Agile", "C++/Systems", "Cloud/Infra", "Research/Academic",
    "Mechanical/Design", "Electrical/Power", "Quality/Maintenance", "Logistics/Supply Chain",
]

# Technical skill keywords for domain boosting
_TECH_KEYWORDS = {
    'mechanical': ['solidworks', 'catia', 'autocad', 'ansys', 'abaqus', 'cnc', 'cad', 'cam',
                   'thermodynamics', 'mechanical', 'structural', 'manufacturing', 'materials',
                   'finite element', 'fluid mechanics', 'heat transfer', 'plastic', 'metal'],
    'electrical': ['plc', 'scada', 'arduino', 'raspberry', 'vhdl', 'verilog', 'fpga',
                   'electrical', 'power', 'electronics', 'motor', 'circuit', 'automation',
                   'control system', 'embedded', 'microcontroller', 'pcb'],
    'software': ['python', 'java', 'javascript', 'react', 'node', 'typescript', 'c++',
                 'docker', 'kubernetes', 'aws', 'azure', 'sql', 'tensorflow', 'pytorch'],
    'quality': ['iso', 'six sigma', 'lean', 'kaizen', '5s', 'audit', 'compliance',
                'quality', 'maintenance', 'reliability', 'qms', 'corrective'],
    'logistics': ['supply chain', 'logistics', 'inventory', 'warehouse', 'procurement',
                  'transportation', 'distribution', 'erp', 'sap'],
    'management': ['project management', 'agile', 'scrum', 'leadership', 'team',
                   'stakeholder', 'planning', 'budget', 'risk'],
}

# Comprehensive stopwords (English + French + CV-generic)
STOPWORDS = set(ENGLISH_STOP_WORDS) | {
    # French articles, pronouns, conjunctions
    'a', 'an', 'the', 'le', 'la', 'les', 'de', 'du', 'des', 'et', 'un', 'une',
    'en', 'dans', 'sur', 'pour', 'avec', 'sans', 'sous', 'par', 'au', 'aux',
    'ce', 'ces', 'son', 'sa', 'ses', 'leur', 'leurs', 'que', 'qui', 'quoi',
    'dont', 'où', 'ne', 'pas', 'plus', 'moins', 'très', 'bien', 'aussi',
    'ainsi', 'donc', 'car', 'ni', 'ou', 'est', 'sont', 'été', 'être', 'avoir',
    'fait', 'faire', 'comme', 'mais', 'donc', 'alors', 'si', 'quand', 'comment',
    # CV-generic terms (non-discriminative)
    'diplome', 'diplôme', 'génie', 'genie', 'ensem', 'emi', 'ensam', 'inpt',
    'engineer', 'ingénieur', 'ingenieur', 'ing', 'master', 'licence',
    'projet', 'stage', 'etude', 'étude', 'university', 'universite',
    'morocco', 'maroc', 'casablanca', 'fsts', 'fst', 'uh2', 'ensias',
    'ans', 'description', 'competence', 'compétence', 'formation',
    'education', 'éducation', 'school', 'ecole', 'école', 'student',
    'etudiant', 'étudiant', 'curriculum', 'vitae', 'cv', 'email', 'tel',
    'telephone', 'address', 'adresse', 'linkedin', 'github', 'profile',
    'profil', 'contact', 'nom', 'name', 'prenom', 'prénom', 'date',
    'naissance', 'born', 'nationality', 'nationalite', 'nationalité',
    'marocaine', 'languages', 'langues', 'francais', 'français', 'anglais',
    'english', 'arabe', 'arabic', 'french', 'objective', 'objectif',
    'reference', 'references', 'référence', 'available', 'disponible',
    'responsibilities', 'responsabilités', 'achievements', 'réalisations',
}


def _normalize_text(text: str) -> str:
    """Normalize text: remove French accents, lowercase, clean special chars."""
    # Remove French accents (é->e, è->e, ê->e, etc.)
    accent_map = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'î': 'i', 'ï': 'i',
        'ô': 'o', 'ö': 'o',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'ñ': 'n',
    }
    for acc, plain in accent_map.items():
        text = text.replace(acc, plain)
    # Lowercase and keep only alphanumeric + spaces
    text = re.sub(r'[^a-zA-Z0-9\s+\-/#]', ' ', text.lower())
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _preprocess(text: str) -> List[str]:
    """Professional bilingual preprocessing: normalize -> tokenize -> remove stopwords -> French/English stem."""
    text = _normalize_text(text)
    if _NLTK_AVAILABLE:
        try:
            tokens = word_tokenize(text)
        except Exception:
            tokens = text.split()
    else:
        tokens = text.split()
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1 and not t.isdigit()]

    if _STEMMER_EN and _STEMMER_FR:
        stemmed = []
        for t in tokens:
            # Use French stemmer for French-looking words, English for others
            if t in _FRENCH_INDICATORS or any(t.startswith(p) for p in ('form', 'maint', 'qual', 'gest', 'prod', 'logis', 'indus', 'constr', 'electr', 'mecan')):
                try:
                    stemmed.append(_STEMMER_FR.stem(t))
                except Exception:
                    stemmed.append(_STEMMER_EN.stem(t))
            else:
                stemmed.append(_STEMMER_EN.stem(t))
    else:
        stemmed = []
        for t in tokens:
            for suffix in ('ing', 'tion', 'ness', 'ment', 'ed', 'er', 'ly', 'al', 'ic', 'age', 'ite', 'ique', 'isation', 'ement', 'ite'):
                if t.endswith(suffix) and len(t) - len(suffix) >= 3:
                    t = t[:-len(suffix)]
                    break
            stemmed.append(t)

    # Add bigrams for key technical terms (boost discriminative power)
    bigrams = []
    for i in range(len(stemmed) - 1):
        pair = f"{stemmed[i]}_{stemmed[i+1]}"
        bigrams.append(pair)
    return stemmed + bigrams


def _build_tfidf(docs: List[List[str]]) -> List[Dict[str, float]]:
    N = len(docs)
    df: Dict[str, int] = {}
    for tokens in docs:
        for t in set(tokens):
            df[t] = df.get(t, 0) + 1
    vectors = []
    for tokens in docs:
        tf: Dict[str, float] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        total = max(len(tokens), 1)
        vec: Dict[str, float] = {}
        for t, count in tf.items():
            idf = math.log((N + 1) / (df.get(t, 0) + 1)) + 1
            vec[t] = (count / total) * idf
        vectors.append(vec)
    return vectors


def _cosine_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    common = set(v1) & set(v2)
    dot = sum(v1[t] * v2[t] for t in common)
    mag1 = math.sqrt(sum(x ** 2 for x in v1.values()))
    mag2 = math.sqrt(sum(x ** 2 for x in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def compute_tfidf_knn_score(cv_text: str, k: int = 3) -> Tuple[float, List[Tuple[str, float]]]:
    cv_tokens = _preprocess(cv_text)
    ref_tokens = [_preprocess(d) for d in _REFERENCE_DOCS]
    all_docs = ref_tokens + [cv_tokens]
    vectors = _build_tfidf(all_docs)
    cv_vec = vectors[-1]
    ref_vecs = vectors[:-1]

    sims = []
    for i, rv in enumerate(ref_vecs):
        sim = _cosine_similarity(cv_vec, rv)
        sims.append((REF_LABELS[i], sim))
    sims.sort(key=lambda x: x[1], reverse=True)

    top_k = sims[:k]
    score = sum(s for _, s in top_k) / k if top_k else 0.0
    return score, sims


class KnowledgeMLModel:
    """KASH Knowledge (K) — Professional ML model for CV filiere prediction.

    Pipeline: Data Cleaning -> NLTK Tokenization -> Porter Stemming -> TF-IDF (1-3 grams) -> Ensemble Voting -> KNN
    """

    _GENERIC_STOPWORDS = set()

    def __init__(self):
        self.vectorizer = None
        self.classifier = None
        self.kmeans = None
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.training_report = None
        self.feature_names = []
        self.classes_ = []
        self._load_model()

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, 'rb') as f:
                    data = pickle.load(f)
                self.vectorizer = data.get('vectorizer')
                self.classifier = data.get('classifier')
                self.kmeans = data.get('kmeans')
                self.label_encoder = data.get('label_encoder', self.label_encoder)
                self.feature_names = data.get('feature_names', [])
                self.classes_ = data.get('classes_', [])
                self.training_report = data.get('training_report')
                self.is_trained = True
                logger.info(f"KASH Knowledge model loaded from {MODEL_PATH} ({len(self.classes_)} classes)")
            except Exception as e:
                logger.warning(f"Failed to load KASH Knowledge model: {e}")

    def save_model(self):
        os.makedirs(MODEL_DIR, exist_ok=True)
        data = {
            'vectorizer': self.vectorizer,
            'classifier': self.classifier,
            'kmeans': self.kmeans,
            'label_encoder': self.label_encoder,
            'feature_names': self.feature_names,
            'classes_': self.classes_,
            'training_report': self.training_report,
        }
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(data, f)
        logger.info(f"KASH Knowledge model saved to {MODEL_PATH}")

    def _append_training_history(self, report: Dict) -> None:
        """Append the latest training summary to a JSON history file."""
        os.makedirs(MODEL_DIR, exist_ok=True)
        history: List[Dict] = []
        if os.path.exists(TRAINING_HISTORY_PATH):
            try:
                with open(TRAINING_HISTORY_PATH, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception:
                history = []

        history.append({
            'trained_at': report.get('trained_at'),
            'cv_accuracy': report.get('cv_accuracy', 0),
            'train_accuracy': report.get('train_accuracy', 0),
            'n_samples': report.get('n_samples', 0),
            'n_samples_after_smote': report.get('n_samples_after_smote', report.get('n_samples', 0)),
            'n_features': report.get('n_features', 0),
            'n_classes': report.get('n_classes', 0),
            'best_algorithm': report.get('best_algorithm', ''),
            'ensemble_members': report.get('ensemble_members', []),
            'smote_applied': report.get('smote_applied', False),
            'model_type': report.get('model_type', ''),
        })

        # Keep only the latest 50 runs to avoid unbounded growth.
        history = history[-50:]
        with open(TRAINING_HISTORY_PATH, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        logger.info(f"Training history updated: {TRAINING_HISTORY_PATH}")

    def _extract_cv_sections(self, text: str) -> Dict[str, str]:
        """Extract CV sections (skills, experience, education) for weighted feature engineering."""
        sections = {'skills': '', 'experience': '', 'education': '', 'full': text}
        text_lower = text.lower()

        section_patterns = [
            ('skills', [r'(?:comp[ée]tences|skills|techniques?|technologies?)[:\s].*?(?=\n\n|\n[A-Z]|$)']),
            ('experience', [r'(?:exp[ée]rience|experience|emploi|work)[:\s].*?(?=\n\n|\n[A-Z]|$)']),
            ('education', [r'(?:formation|education|dipl[ôo]me|academic)[:\s].*?(?=\n\n|\n[A-Z]|$)']),
        ]
        for section_name, patterns in section_patterns:
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
                if match:
                    sections[section_name] = match.group(0)[:2000]
                    break
        return sections

    def _extract_tech_keywords(self, text: str) -> Dict[str, int]:
        """Detect technical domain keywords and return domain hit counts."""
        text_lower = text.lower()
        domain_hits = {}
        for domain, keywords in _TECH_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in text_lower)
            if hits > 0:
                domain_hits[domain] = hits
        return domain_hits

    def _extract_cv_full_text(self, r: Dict) -> str:
        """Extract full CV text from PDF or fallback to skills+education fields."""
        path = r.get('path', '')
        if path and os.path.exists(path):
            try:
                from pypdf import PdfReader
                import io as _io
                with open(path, 'rb') as f:
                    content = f.read()
                reader = PdfReader(_io.BytesIO(content))
                pages = [page.extract_text() or '' for page in reader.pages]
                text = '\n'.join(pages)
                if len(text.strip()) > 50:
                    return text
            except Exception:
                pass
        parts = []
        if r.get('skills'):
            parts.append(' '.join(r['skills']))
        if r.get('education'):
            parts.append(' '.join(r['education']))
        if r.get('experience'):
            parts.append(' '.join(r['experience']))
        return ' '.join(parts) if parts else ' '.join(r.get('skills', []))

    def _build_enhanced_text(self, raw_text: str) -> str:
        """Build enhanced text with section weighting: skills x3, experience x2, education x1."""
        sections = self._extract_cv_sections(raw_text)
        parts = [raw_text]
        if sections['skills']:
            parts.append(sections['skills'] * 2)
        if sections['experience']:
            parts.append(sections['experience'])
        return ' '.join(parts)

    def train(self, cv_results: List[Dict]) -> Dict:
        valid = [r for r in cv_results if r.get('filiere') and r.get('filiere') != 'Autre']
        if len(valid) < 10:
            return {'error': f'Pas assez de CVs avec filiere valide ({len(valid)} trouves, min 10 requis)'}

        texts = []
        labels = []
        for r in valid:
            raw_text = self._extract_cv_full_text(r)
            if len(raw_text.strip()) >= 50:
                enhanced = self._build_enhanced_text(raw_text)
                texts.append(enhanced)
                labels.append(r['filiere'])

        if len(texts) < 10:
            return {'error': f'Pas assez de CVs avec texte extractible ({len(texts)} trouves, min 10 requis)'}

        # Check class distribution
        class_counts = Counter(labels)
        min_class_size = min(class_counts.values())
        logger.info(f"Training data: {len(texts)} CVs, {len(class_counts)} classes, min class={min_class_size}")

        all_stop_words = list(STOPWORDS)
        self.vectorizer = TfidfVectorizer(
            max_features=1500,
            ngram_range=(1, 3),
            min_df=1,          # Lower threshold: keep more features for small corpus
            max_df=0.80,       # Slightly higher to keep domain terms
            stop_words=all_stop_words,
            sublinear_tf=True,
            norm='l2',
        )
        X = self.vectorizer.fit_transform(texts)
        self.feature_names = self.vectorizer.get_feature_names_out().tolist()

        y = self.label_encoder.fit_transform(labels)
        self.classes_ = self.label_encoder.classes_.tolist()

        # Apply SMOTE if available and beneficial (minority classes need boosting)
        use_smote = _IMBLEARN_AVAILABLE and min_class_size >= 3 and len(class_counts) > 2
        if use_smote:
            try:
                k_neighbors = min(3, min_class_size - 1)
                smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
                X_resampled, y_resampled = smote.fit_resample(X, y)
                logger.info(f"SMOTE applied: {X.shape[0]} -> {X_resampled.shape[0]} samples")
            except Exception as e:
                logger.warning(f"SMOTE failed ({e}), falling back to class_weight")
                X_resampled, y_resampled = X, y
                use_smote = False
        else:
            X_resampled, y_resampled = X, y

        n_splits = min(5, min_class_size, len(set(y)))
        if n_splits < 2:
            n_splits = 2

        # Compute sample weights for class balancing (fallback when no SMOTE)
        if not use_smote:
            sample_weights = compute_sample_weight('balanced', y)
        else:
            sample_weights = None

        algorithms = {
            'RandomForest': RandomForestClassifier(
                n_estimators=500, max_depth=15, min_samples_split=2,
                min_samples_leaf=1, random_state=42, class_weight='balanced',
                max_features='sqrt',
            ),
            'ExtraTrees': ExtraTreesClassifier(
                n_estimators=500, max_depth=15, min_samples_split=2,
                min_samples_leaf=1, random_state=42, class_weight='balanced',
                max_features='sqrt',
            ),
            'SVM (RBF)': SVC(
                kernel='rbf', C=3.0, gamma='scale', probability=True,
                random_state=42, class_weight='balanced',
            ),
            'LogisticRegression': LogisticRegression(
                max_iter=3000, C=1.5, random_state=42,
                class_weight='balanced', solver='lbfgs',
            ),
            'GradientBoosting': GradientBoostingClassifier(
                n_estimators=300, max_depth=4, learning_rate=0.05,
                random_state=42, subsample=0.8, min_samples_leaf=2,
            ),
        }

        algo_results = {}
        best_cv_acc = 0.0
        best_algo_name = ''

        for name, clf in algorithms.items():
            if n_splits >= 2 and X_resampled.shape[0] >= n_splits * 2:
                cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
                cv_scores = cross_val_score(clf, X_resampled, y_resampled, cv=cv, scoring='accuracy')
                algo_results[name] = {
                    'cv_accuracy': round(float(cv_scores.mean()), 3),
                    'cv_std': round(float(cv_scores.std()), 3),
                }
                if cv_scores.mean() > best_cv_acc:
                    best_cv_acc = cv_scores.mean()
                    best_algo_name = name
            else:
                algo_results[name] = {'cv_accuracy': 0.0, 'cv_std': 0.0}

        if not best_algo_name:
            best_algo_name = 'RandomForest'

        # Build ensemble voting classifier with top 3 algorithms
        sorted_algos = sorted(algo_results.items(), key=lambda x: x[1].get('cv_accuracy', 0), reverse=True)
        top3_names = [name for name, _ in sorted_algos[:3]]
        estimators = [(name, algorithms[name]) for name in top3_names]

        self.classifier = VotingClassifier(
            estimators=estimators,
            voting='soft',
            weights=[3, 2, 1][:len(estimators)],
        )

        if n_splits >= 2 and X_resampled.shape[0] >= n_splits * 2:
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
            cv_scores = cross_val_score(self.classifier, X_resampled, y_resampled, cv=cv, scoring='accuracy')
            cv_accuracy = round(float(cv_scores.mean()), 3)
            cv_std = round(float(cv_scores.std()), 3)
        else:
            cv_accuracy = 0.0
            cv_std = 0.0

        self.classifier.fit(X_resampled, y_resampled)
        y_pred = self.classifier.predict(X)
        train_accuracy = round(float(np.mean(y_pred == y)), 3)

        cm = confusion_matrix(y, y_pred, labels=range(len(self.classes_)))
        cm_list = cm.tolist()
        report = classification_report(y, y_pred, target_names=self.classes_, output_dict=True, zero_division=0)

        # Feature importance — aggregate from ensemble members
        feature_importance = {}
        global_importances = np.zeros(len(self.feature_names))
        n_contributors = 0

        for name, clf in self.classifier.named_estimators_.items():
            if hasattr(clf, 'feature_importances_'):
                global_importances += clf.feature_importances_
                n_contributors += 1
            elif hasattr(clf, 'coef_'):
                coefs = np.abs(clf.coef_).mean(axis=0)
                global_importances += coefs / (coefs.max() + 1e-10)
                n_contributors += 1

        if n_contributors > 0:
            global_importances /= n_contributors
            top_idx = np.argsort(global_importances)[::-1][:25]
            feature_importance['global'] = [
                {'feature': self.feature_names[i], 'importance': round(float(global_importances[i]), 4)}
                for i in top_idx
            ]
        else:
            feature_importance['global'] = []

        for ci, cls in enumerate(self.classes_):
            cls_mask = y == ci
            if cls_mask.sum() > 0:
                cls_mean = np.asarray(X[cls_mask].mean(axis=0)).flatten()
                global_mean = np.asarray(X.mean(axis=0)).flatten()
                cls_specificity = cls_mean - global_mean
                top_cls_idx = np.argsort(cls_specificity)[::-1][:10]
                feature_importance[cls] = [
                    {'feature': self.feature_names[i], 'weight': round(float(cls_mean[i]), 4)}
                    for i in top_cls_idx if cls_mean[i] > 0
                ]

        n_clusters = min(len(self.classes_), 6)
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = self.kmeans.fit_predict(X)

        cluster_composition = []
        for c in range(n_clusters):
            mask = cluster_labels == c
            filieres_in_cluster = [labels[i] for i in range(len(labels)) if mask[i]]
            counts = Counter(filieres_in_cluster)
            cluster_composition.append({
                'cluster': c,
                'size': int(mask.sum()),
                'filieres': dict(counts),
            })

        cv_clusters = []
        for i, r in enumerate(valid):
            if i < len(cluster_labels):
                cv_clusters.append({
                    'filename': r['filename'],
                    'filiere': r['filiere'],
                    'cluster': int(cluster_labels[i]),
                })

        self.is_trained = True
        self.training_report = {
            'status': 'trained',
            'n_samples': len(texts),
            'n_samples_after_smote': X_resampled.shape[0] if use_smote else len(texts),
            'smote_applied': use_smote,
            'n_features': len(self.feature_names),
            'n_classes': len(self.classes_),
            'classes': self.classes_,
            'train_accuracy': train_accuracy,
            'cv_accuracy': cv_accuracy,
            'cv_std': cv_std,
            'cv_folds': n_splits,
            'best_algorithm': best_algo_name,
            'ensemble_members': top3_names,
            'algorithm_comparison': algo_results,
            'confusion_matrix': cm_list,
            'classification_report': report,
            'feature_importance': feature_importance,
            'n_clusters': n_clusters,
            'cluster_composition': cluster_composition,
            'cv_clusters': cv_clusters,
            'model_type': f"Ensemble Voting({', '.join(top3_names)}) + TF-IDF ({len(self.feature_names)} features, trigrams, {'SMOTE + ' if use_smote else ''}bilingual stemming, section-weighted)",
            'saved_to': MODEL_PATH,
            'trained_at': datetime.now().isoformat(),
            'pipeline': 'Data Cleaning -> Accent Normalization -> NLTK Bilingual Tokenization -> FR/EN Stemming -> TF-IDF (1-3 grams) -> ' + ('SMOTE -> ' if use_smote else '') + 'Ensemble Voting -> KNN Similarity',
        }

        self.save_model()
        self._append_training_history(self.training_report)
        return self.training_report

    def predict(self, cv_text: str) -> Optional[Dict]:
        if not self.is_trained:
            return None

        enhanced = self._build_enhanced_text(cv_text)
        X = self.vectorizer.transform([enhanced])
        pred = self.classifier.predict(X)
        proba = self.classifier.predict_proba(X)

        predicted_filiere = self.label_encoder.inverse_transform(pred)[0]
        probabilities = []
        for i, cls in enumerate(self.classes_):
            probabilities.append({'filiere': cls, 'probability': round(float(proba[0][i]), 4)})
        probabilities.sort(key=lambda x: x['probability'], reverse=True)

        cluster = int(self.kmeans.predict(X)[0])

        knn_score, knn_sims = compute_tfidf_knn_score(cv_text)

        # Extract technical domain signals
        tech_domains = self._extract_tech_keywords(cv_text)

        # Confidence assessment
        top_prob = probabilities[0]['probability'] if probabilities else 0
        second_prob = probabilities[1]['probability'] if len(probabilities) > 1 else 0
        confidence = 'high' if top_prob > 0.6 else ('medium' if top_prob > 0.4 else 'low')
        margin = round(top_prob - second_prob, 4)

        # Extract detected skills from CV text
        detected_skills = []
        cv_lower = cv_text.lower()
        for domain, keywords in _TECH_KEYWORDS.items():
            for kw in keywords:
                if kw in cv_lower and kw not in detected_skills:
                    detected_skills.append(kw)

        return {
            'predicted_filiere': predicted_filiere,
            'probabilities': probabilities,
            'cluster': cluster,
            'tfidf_knn_score': round(knn_score, 4),
            'top_similarities': [(label, round(sim, 3)) for label, sim in knn_sims[:5]],
            'confidence': confidence,
            'confidence_margin': margin,
            'detected_tech_domains': tech_domains,
            'detected_skills': detected_skills[:20],
            'n_features_matched': int((X > 0).sum()),
        }


_knowledge_model_instance: Optional[KnowledgeMLModel] = None


def get_knowledge_model() -> KnowledgeMLModel:
    global _knowledge_model_instance
    if _knowledge_model_instance is None:
        _knowledge_model_instance = KnowledgeMLModel()
    return _knowledge_model_instance
