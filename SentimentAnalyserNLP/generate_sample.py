#!/usr/bin/env python3
"""
Generate a sample.json file with 100 diverse review entries
"""
import json
import random
from datetime import datetime, timedelta

# Sample data pools
reviewer_names = ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Emily Brown', 'Frank Miller', 'Grace Lee', 'Henry Taylor', 'Ivy Chen', 'Jack Robinson', 'Karen White', 'Liam Garcia', 'Maya Patel', 'Nathan Kim', 'Olivia Martinez', 'Peter Clark', 'Quinn Anderson', 'Rachel Thomas', 'Sam Rodriguez', 'Tina Lopez']

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
    'Works perfectly with all my devices.',
    'Outstanding customer support team.',
    'Impressive build quality for the price.',
    'Love the sleek design and functionality.',
    'Battery performance is absolutely incredible.',
    'Screen quality is top-notch and bright.',
    'Super fast charging capabilities.',
    'Camera takes amazing photos in all conditions.',
    'Bluetooth pairing is instant and stable.',
    'Premium feel and excellent craftsmanship.',
    'Best purchase I have made this year!'
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
    'Standard features, nothing groundbreaking.',
    'Does what it says, but nothing more.',
    'Reasonable quality for the price point.',
    'Functional but not impressive.',
    'Average product, works fine.',
    'Meets expectations, nothing special.'
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
    'Very slow performance, constant lag.',
    'Materials feel cheap and plasticky.',
    'Overpriced for what you get.',
    'Complex setup process with poor instructions.',
    'Ugly design that looks outdated.',
    'Incompatible with many common devices.',
    'Complete waste of money.',
    'Defective product, returned immediately.',
    'Worst purchase ever made.',
    'Quality control is non-existent.',
    'Broke on the first day of use.'
]

products = ['B08N5WRWNW', '120401325X', 'B07G2K3T4R', 'B09KMHPX7J', 'B076BDKZ89']

def generate_reviews(num_reviews=100):
    """Generate specified number of review entries"""
    reviews = []
    
    for i in range(num_reviews):
        # Randomly select sentiment distribution (70% positive, 20% neutral, 10% negative)
        rand_val = random.random()
        if rand_val < 0.7:
            review_text = random.choice(positive_reviews)
            rating = random.choice([4.0, 5.0])
            summary_words = ['Great', 'Excellent', 'Love it', 'Perfect', 'Amazing']
        elif rand_val < 0.9:
            review_text = random.choice(neutral_reviews)
            rating = 3.0
            summary_words = ['Okay', 'Average', 'Decent', 'Fair']
        else:
            review_text = random.choice(negative_reviews)
            rating = random.choice([1.0, 2.0])
            summary_words = ['Disappointed', 'Poor', 'Terrible', 'Bad']
        
        summary_prefix = random.choice(summary_words)
        summary_suffix = random.choice(['product', 'purchase', 'item', 'device', 'quality'])
        
        # Generate random date in last 2 years
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        random_date = start_date + timedelta(days=random.randint(0, 730))
        unix_time = int(random_date.timestamp())
        
        review = {
            'reviewerID': f'A{random.randint(10000000, 99999999)}',
            'asin': random.choice(products),
            'reviewerName': random.choice(reviewer_names),
            'helpful': [random.randint(0, 10), random.randint(0, 15)],
            'reviewText': review_text,
            'overall': rating,
            'summary': f'{summary_prefix} {summary_suffix}',
            'unixReviewTime': unix_time,
            'reviewTime': random_date.strftime('%m %d, %Y')
        }
        reviews.append(review)
    
    return reviews

if __name__ == "__main__":
    # Generate 100 reviews
    reviews = generate_reviews(100)
    
    # Write to file
    with open('sample.json', 'w', encoding='utf-8') as f:
        for review in reviews:
            f.write(json.dumps(review) + '\n')
    
    print(f'Created sample.json with {len(reviews)} entries')