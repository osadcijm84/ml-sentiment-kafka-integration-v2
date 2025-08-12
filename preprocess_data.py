import json

def preprocess_data(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            data = json.loads(line.strip())
            review_text = data.get('text', '')
            overall_rating = data.get('rating', None)

            sentiment = None
            if overall_rating is not None:
                if overall_rating >= 4:
                    sentiment = 1  # Positive
                elif overall_rating <= 2:
                    sentiment = 0  # Negative
                # Neutral (rating 3) will be excluded for binary classification

            if review_text and sentiment is not None:
                outfile.write(json.dumps({'text': review_text, 'sentiment': sentiment}) + '\n')

if __name__ == '__main__':
    preprocess_data('All_Beauty.jsonl', 'processed_reviews.jsonl')


