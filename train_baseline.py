import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import xgboost as xgb

INPUT_FILE = "account_features.csv"
MODEL_FILE = "baseline_model.json"

FEATURE_COLS = [
    "in_degree", "out_degree", "unique_senders", "unique_receivers",
    "total_in", "total_out", "pass_through_ratio", "velocity_hours",
    "in_span_hours", "avg_in_amount", "avg_out_amount",
]


def main():
    df = pd.read_csv(INPUT_FILE)

    X = df[FEATURE_COLS]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # Fraud is rare (~5%) -- without this, model happily predicts
    # "normal" for everyone and still looks 95% accurate while catching
    # zero actual fraud.
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        eval_metric="aucpr",
        random_state=42,
    )
    model.fit(X_train, y_train)

    probs = model.predict_proba(X_test)[:, 1]
    preds = model.predict(X_test)

    print("=== Classification report ===")
    print(classification_report(y_test, preds, target_names=["normal", "mule-ring"]))

    print(f"AUROC: {roc_auc_score(y_test, probs):.4f}")

    print("\n=== Feature importance ===")
    importance = pd.Series(model.feature_importances_, index=FEATURE_COLS).sort_values(ascending=False)
    print(importance.to_string())

    model.save_model(MODEL_FILE)
    print(f"\nModel saved to {MODEL_FILE}")


if __name__ == "__main__":
    main()