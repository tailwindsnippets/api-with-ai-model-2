import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
import joblib

# change path to match your saved CSV
CSV_PATH = "malawi_predictions_20250820T184711Z.csv"
df = pd.read_csv(CSV_PATH)

# --- choose features and targets ---
meta_cols = ["district", "food_group", "simulation"]
baseline_cols = [c for c in df.columns if c.startswith("baseline_")]
pred_cols = [c for c in df.columns if c.startswith("pred_")]

# features: simulation (numeric), baseline nutrients, and categorical district/food_group
X = df[["simulation"] + baseline_cols + ["district", "food_group"]].copy()
y = df[pred_cols].copy()  # multi-target: all predicted nutrients

# fill or drop NaNs (example: simple imputation with median for numeric)
X[baseline_cols] = X[baseline_cols].fillna(X[baseline_cols].median())
X["simulation"] = X["simulation"].fillna(0)

# split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Preprocessing:
numeric_features = ["simulation"] + baseline_cols
categorical_features = ["district", "food_group"]

numeric_transformer = Pipeline(steps=[
    ("scaler", StandardScaler()),
])


categorical_transformer = Pipeline(steps=[
    ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
])

preprocessor = ColumnTransformer(transformers=[
    ("num", numeric_transformer, numeric_features),
    ("cat", categorical_transformer, categorical_features),
])

# Model pipeline (RandomForest wrapped for multi-output)
model = Pipeline(steps=[
    ("preproc", preprocessor),
    ("reg", MultiOutputRegressor(RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)))
])

# train (this may take a while depending on data/model size)
model.fit(X_train, y_train)

# evaluate quickly (R^2 per nutrient)
r2_scores = model.score(X_test, y_test)
print("Overall R^2 (scikit-learn's multioutput aggregate):", r2_scores)

# save the trained pipeline
joblib.dump(model, "malawi_nutrient_model.joblib")
print("Model saved: malawi_nutrient_model.joblib")
