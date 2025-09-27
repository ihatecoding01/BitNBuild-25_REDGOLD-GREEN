#!/usr/bin/env python3
"""
Generate a CSV file with 50 diverse review entries for sentiment analysis
"""
import csv
import random
from datetime import datetime, timedelta

# Sample data pools
reviewer_names = ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Emily Brown', 
                 'Frank Miller', 'Grace Lee', 'Henry Taylor', 'Ivy Chen', 'Jack Robinson']

positive_reviews = [
    'This product exceeded my expectations! Great quality and fast delivery.',
    'Amazing battery life! Lasts all day even with heavy usage.',
    'Perfect fit and excellent build quality. Highly recommend!',
    'Screen is crystal clear and colors are vibrant. Love it!',
    'Fast charging works perfectly. Great value for money.',
    'Camera quality is outstanding, even in low light conditions.',
    'Bluetooth connectivity is seamless and stable.',
    'Design is sleek and modern. Looks premium.',
    'Excellent customer service and quick response.',
    'Durable construction, survived multiple drops without damage.',
    'Audio quality is exceptional with deep bass.',
    'User interface is intuitive and easy to navigate.',
    'Lightweight yet sturdy. Perfect for daily use.',
    'Wireless connectivity works flawlessly.',
    'Great performance, no lag or slowdowns.',
    'The materials feel premium and high-quality.',
    'Excellent value proposition for the price.',
    'Setup was quick and straightforward.',
    'Beautiful design that complements any style.',
    'Works perfectly with all my devices.'
]

neutral_reviews = [
    'Product works as expected, nothing special but does the job.',
    'Average quality for the price range. Could be better.',
    'It works fine but took a while to get used to.',
    'Decent product, meets basic requirements.',
    'Good enough for casual use, not for heavy users.',
    'Quality is okay, similar to other products in this range.',
    'Works as advertised, no major complaints.',
    'Fair value for money, gets the job done.',
    'Acceptable performance for everyday tasks.',
    'Standard features, nothing groundbreaking.'
]

negative_reviews = [
    'Terrible quality! Broke after just one week of use.',
    'Battery drains too quickly, barely lasts half a day.',
    'Screen is dim and colors look washed out.',
    'Charging is extremely slow, takes forever.',
    'Camera produces blurry and noisy images.',
    'Bluetooth keeps disconnecting randomly.',
    'Poor build quality, feels cheap and flimsy.',
    'Customer service was unhelpful and rude.',
    'Product stopped working after two months.',
    'Audio quality is terrible with lots of static.',
    'Overheats during normal use.',
    'Interface is confusing and hard to navigate.',
    'Too heavy and bulky for everyday carry.',
    'Connectivity issues with most devices.',
    'Very slow performance, constant lag.'
]

def generate_csv_reviews(num_reviews=50):
    """Generate CSV data with review entries"""
    reviews = []
    
    for i in range(num_reviews):
        # Randomly select sentiment distribution (60% positive, 25% neutral, 15% negative)
        rand_val = random.random()
        if rand_val < 0.6:
            review_text = random.choice(positive_reviews)
            rating = random.choice([4, 5])
            sentiment = 'positive'
        elif rand_val < 0.85:
            review_text = random.choice(neutral_reviews)
            rating = 3
            sentiment = 'neutral'
        else:
            review_text = random.choice(negative_reviews)
            rating = random.choice([1, 2])
            sentiment = 'negative'
        
        # Generate random date in last year
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        random_date = start_date + timedelta(days=random.randint(0, 365))
        
        review_data = {
            'review_id': f'R{i+1:03d}',
            'reviewer_name': random.choice(reviewer_names),
            'review_text': review_text,
            'rating': rating,
            'sentiment': sentiment,
            'review_date': random_date.strftime('%Y-%m-%d'),
            'product_category': random.choice(['Electronics', 'Phone Accessories', 'Chargers', 'Cases'])
        }
        reviews.append(review_data)
    
    return reviews

if __name__ == "__main__":
    # Generate 50 reviews
    reviews = generate_csv_reviews(50)
    
    # Write to CSV file
    fieldnames = ['review_id', 'reviewer_name', 'review_text', 'rating', 'sentiment', 'review_date', 'product_category']
    
    with open('reviews.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reviews)
    
    print(f'Created reviews.csv with {len(reviews)} entries')
    print('Columns:', ', '.join(fieldnames))