"""Quick benchmark for README."""
import requests
import sys

context = [
    {"id": "auth.py", "text": "def login(username, password):\n    '''Authenticate user and return JWT token.'''\n    user = database.get_user(username)\n    if not user:\n        return None\n    if not bcrypt.verify(password, user.password_hash):\n        return None\n    token = jwt.encode({'user_id': user.id, 'username': username}, SECRET_KEY)\n    return token\n\ndef verify_token(token):\n    '''Verify JWT token validity.'''\n    try:\n        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])\n        return payload\n    except jwt.InvalidTokenError:\n        return None", "type": "code"},
    {"id": "database.py", "text": "def get_user(username):\n    '''Fetch user from database.'''\n    session = Session()\n    user = session.query(User).filter_by(username=username).first()\n    return user\n\ndef save_user(user_data):\n    '''Save user to database.'''\n    session = Session()\n    user = User(**user_data)\n    session.add(user)\n    session.commit()\n    return user", "type": "code"},
    {"id": "payment.py", "text": "def process_payment(amount, card_token):\n    '''Process credit card payment using Stripe.'''\n    stripe.api_key = STRIPE_KEY\n    charge = stripe.Charge.create(amount=amount, currency='usd', source=card_token)\n    return charge\n\ndef refund_payment(charge_id):\n    '''Refund a payment.'''\n    stripe.api_key = STRIPE_KEY\n    refund = stripe.Refund.create(charge=charge_id)\n    return refund", "type": "code"},
    {"id": "email.py", "text": "def send_email(to, subject, body):\n    '''Send email using SendGrid.'''\n    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_KEY)\n    message = Mail(from_email='noreply@app.com', to_emails=to, subject=subject, html_content=body)\n    response = sg.send(message)\n    return response", "type": "code"},
    {"id": "analytics.py", "text": "def track_event(user_id, event_name, properties):\n    '''Track analytics event.'''\n    mixpanel.track(user_id, event_name, properties)\n\ndef get_user_stats(user_id):\n    '''Get user analytics statistics.'''\n    return analytics_db.query(user_id)", "type": "code"}
]

response = requests.post('http://localhost:8000/optimize', json={
    "query": "How does user authentication and login work?",
    "context": context,
    "targetTokens": 1000,
    "options": {"strategy": "diversity", "minRelevanceScore": 0.2}
}, timeout=30)

if response.status_code == 200:
    result = response.json()
    stats = result['stats']
    print(f"{stats['original_tokens']}|{stats['optimized_tokens']}|{stats['reduction_percent']}|{stats['processing_time_ms']:.0f}|{stats['chunks_analyzed']}|{stats['chunks_selected']}")
else:
    sys.exit(1)

