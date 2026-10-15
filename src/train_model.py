# train_model.py — Random Forest training on ISCX VPN-NonVPN 2016
#
# Trains the five-class traffic classifier and writes model.pkl and
# features.pkl for the Ryu controller.
import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

PROJECT_DIR = os.environ.get(
    'PROJECT_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET = os.path.join(PROJECT_DIR, 'dataset', 'consolidated_traffic_data.csv')
MODEL_DIR = os.path.join(PROJECT_DIR, 'model')

df = pd.read_csv(DATASET)

# 14 original ISCX categories -> 5 project classes
label_map = {
    'BROWSING': 'Web_Browsing', 'VPN-BROWSING': 'Web_Browsing',
    'VOIP': 'VoIP', 'VPN-VOIP': 'VoIP',
    'FT': 'File_Transfer', 'VPN-FT': 'File_Transfer',
    'STREAMING': 'Video_Streaming', 'VPN-STREAMING': 'Video_Streaming',
    'P2P': 'Gaming', 'VPN-P2P': 'Gaming',
    'CHAT': 'Web_Browsing', 'VPN-CHAT': 'Web_Browsing',
    'MAIL': 'Web_Browsing', 'VPN-MAIL': 'Web_Browsing',
}
df['label'] = df['traffic_type'].map(label_map)
df = df.dropna(subset=['label'])

features = [c for c in df.columns if c not in ['traffic_type', 'label']]
X = df[features].fillna(0)
y = df['label']

# Stratified 80/20 split: 47,764 training / 11,942 test samples
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

# 100 trees, Gini impurity, all CPU cores
clf = RandomForestClassifier(n_estimators=100, criterion='gini',
                             random_state=42, n_jobs=-1)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
print(f'Accuracy: {accuracy_score(y_test, y_pred)*100:.2f}%')  # 94.55%
print(classification_report(y_test, y_pred))

# Persist for Ryu deployment
os.makedirs(MODEL_DIR, exist_ok=True)
joblib.dump(clf, os.path.join(MODEL_DIR, 'model.pkl'))
joblib.dump(features, os.path.join(MODEL_DIR, 'features.pkl'))
