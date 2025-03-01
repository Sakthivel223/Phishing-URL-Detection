import joblib
import numpy as np
from flask import Flask, request, jsonify
import xgboost as xgb
import re
from urllib.parse import urlparse
import tldextract

app = Flask(__name__)


model = xgb.Booster()
model.load_model('model/phishing_detection_model.json')
scaler = joblib.load('model/scaler.pkl')
selected_features = joblib.load('model/selected_features.pkl')

def extract_features(url):
    """Extract meaningful features from a URL for phishing detection."""
    features_dict = {}
    
    # Parse the URL
    parsed_url = urlparse(url)
    extracted = tldextract.extract(url)
    
    # Basic URL properties
    features_dict['url_length'] = len(url)
    features_dict['domain_length'] = len(extracted.domain)
    features_dict['tld_length'] = len(extracted.suffix) if extracted.suffix else 0
    
    # Number of subdomains
    features_dict['subdomain_count'] = len(extracted.subdomain.split('.')) if extracted.subdomain else 0
    
    # Check for suspicious patterns
    features_dict['has_ip_address'] = 1 if re.search(r'\d+\.\d+\.\d+\.\d+', url) else 0
    features_dict['has_at_symbol'] = 1 if '@' in url else 0
    features_dict['has_double_slash'] = 1 if '//' in parsed_url.path else 0
    features_dict['has_dash_in_domain'] = 1 if '-' in extracted.domain else 0
    features_dict['has_multiple_subdomains'] = 1 if features_dict['subdomain_count'] > 1 else 0
    
    # URL path features
    features_dict['path_length'] = len(parsed_url.path)
    features_dict['path_depth'] = len(parsed_url.path.split('/')) - 1 if parsed_url.path else 0
    features_dict['has_suspicious_tld'] = 1 if extracted.suffix in ['xyz', 'top', 'ml', 'ga', 'cf', 'gq', 'tk'] else 0
    
    # Query parameters
    features_dict['query_length'] = len(parsed_url.query)
    features_dict['query_count'] = len(parsed_url.query.split('&')) if parsed_url.query else 0
    
    # Brand-based features
    common_brands = ['paypal', 'apple', 'microsoft', 'amazon', 'google', 'facebook', 'instagram', 'netflix']
    features_dict['has_brand_name'] = any(brand in extracted.domain.lower() for brand in common_brands)
    features_dict['has_suspicious_words'] = 1 if any(word in url.lower() for word in ['secure', 'account', 'login', 'verify', 'signin', 'security', 'confirm', 'update']) else 0
    
    # Common phishing techniques
    features_dict['has_multiple_tlds'] = 1 if len(re.findall(r'(?:\.[a-z]{2,}){2,}', url)) > 0 else 0
    features_dict['subdomain_contains_brand'] = 1 if extracted.subdomain and any(brand in extracted.subdomain.lower() for brand in common_brands) else 0
    features_dict['domain_with_support'] = 1 if 'support' in url.lower() and any(brand in url.lower() for brand in common_brands) else 0
    
    # Ensure we're using the same features in the same order as during training
    ordered_features = []
    for feature_name in selected_features:
        if feature_name in features_dict:
            ordered_features.append(features_dict[feature_name])
        else:
            # If a feature from training isn't calculated here, use 0 as default
            ordered_features.append(0)
    
    return np.array(ordered_features).reshape(1, -1)

@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.json
    url = data.get("url")
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    features = extract_features(url)
    
    # Check feature size
    if features.shape[1] != len(selected_features):
        return jsonify({"error": f"Feature size mismatch: expected {len(selected_features)}, got {features.shape[1]}"}), 400
    
    # Scale features
    features_scaled = scaler.transform(features)
    
    # Convert to DMatrix for XGBoost
    dfeatures = xgb.DMatrix(features_scaled)
    
    # Make prediction
    prediction = model.predict(dfeatures)[0]
    confidence = float(prediction) * 100  
    
    
    is_phishing = int(prediction > 0.5)
    
   
    if 'paypal' in url.lower() and 'paypal.com' not in url.lower():
        is_phishing = 1
        confidence = max(confidence, 85.0)  
    
    return jsonify({"prediction": is_phishing, "confidence": confidence})

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)