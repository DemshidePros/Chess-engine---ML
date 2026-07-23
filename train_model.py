import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, roc_auc_score
from features import FEATURE_NAMES

df = pd.read_csv("dataset.csv")
X = df[FEATURE_NAMES].values
y = df["label"].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

model = LogisticRegression(max_iter=1000, C=1.0)
model.fit(X_train_s, y_train)

pred = model.predict(X_test_s)
proba = model.predict_proba(X_test_s)[:, 1]
acc = accuracy_score(y_test, pred)
auc = roc_auc_score(y_test, proba)

print(f"Accuracy on the test set: {acc:.4f}")
print(f"ROC-AUC on the test set: {auc:.4f}")

print("\nFeature importance (weight in standardized units):")
for name, coef in sorted(zip(FEATURE_NAMES, model.coef_[0]), key=lambda x: -abs(x[1])):
    print(f"  {name:20s} {coef:+.4f}")

# to export it
export = {
    "feature_names": FEATURE_NAMES,
    "scaler_mean": scaler.mean_.tolist(),
    "scaler_scale": scaler.scale_.tolist(),
    "weights": model.coef_[0].tolist(),
    "intercept": float(model.intercept_[0]),
}

with open("move_filter_model.json", "w") as f:
    json.dump(export, f, indent=2)

print("\nSaved in move_filter_model.json")
