import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

def train_model(input_file, model_output_path, vectorizer_output_path):
    texts = []
    sentiments = []
    with open(input_file, 'r') as f:
        for line in f:
            data = json.loads(line.strip())
            texts.append(data['text'])
            sentiments.append(data['sentiment'])

    X_train, X_test, y_train, y_test = train_test_split(texts, sentiments, test_size=0.2, random_state=42)

    vectorizer = TfidfVectorizer(max_features=5000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train_vec, y_train)

    y_pred = model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)

    print(f"Model Accuracy: {accuracy}")
    print("Classification Report:\n", report)

    joblib.dump(model, model_output_path)
    joblib.dump(vectorizer, vectorizer_output_path)

if __name__ == '__main__':
    train_model('processed_reviews.jsonl', 'sentiment_model.pkl', 'tfidf_vectorizer.pkl')


