import os
from flask import Flask, jsonify, request
import requests
from dotenv import load_dotenv
from pymongo import MongoClient
from cryptography.fernet import Fernet
from datetime import datetime, timezone
from flask_cors import CORS

# --- Load Environment Variables ---
load_dotenv()

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- Environment Variables ---
UPSTOX_CLIENT_ID = os.getenv("UPSTOX_CLIENT_ID")
UPSTOX_CLIENT_SECRET = os.getenv("UPSTOX_CLIENT_SECRET")
UPSTOX_REDIRECT_URI = os.getenv("UPSTOX_REDIRECT_URI")
MONGO_URI = os.getenv("MONGO_URI")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

# --- Error Handling for Missing Config ---
if not all([MONGO_URI, ENCRYPTION_KEY]):
    raise RuntimeError("Missing critical environment variables: MONGO_URI or ENCRYPTION_KEY")

# --- Cryptography & Database Setup ---
fernet = Fernet(ENCRYPTION_KEY.encode())
from database import db, users_collection, option_chain_collection


@app.route("/api/auth/login_url", methods=['GET'])
def get_login_url():
    """Generates the Upstox login URL."""
    if not all([UPSTOX_CLIENT_ID, UPSTOX_REDIRECT_URI]):
        return jsonify({"detail": "Server is not configured for Upstox authentication."}), 500

    auth_url = (
        f"https://api.upstox.com/v2/login/authorization/dialog?"
        f"client_id={UPSTOX_CLIENT_ID}&"
        f"redirect_uri={UPSTOX_REDIRECT_URI}&"
        f"response_type=code"
    )
    return jsonify({"auth_url": auth_url})


@app.route("/api/auth/token", methods=['POST'])
def get_token():
    """Exchanges the authorization code for an access token and stores it."""
    request_data = request.get_json()
    code = request_data.get('code')
    role = request_data.get('role')

    if not code or not role:
        return jsonify({"detail": "Missing code or role."}), 400

    if not all([UPSTOX_CLIENT_ID, UPSTOX_CLIENT_SECRET, UPSTOX_REDIRECT_URI]):
        return jsonify({"detail": "Server is not configured for Upstox authentication."}), 500

    url = "https://api.upstox.com/v2/login/authorization/token"
    headers = {"accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": UPSTOX_CLIENT_ID,
        "client_secret": UPSTOX_CLIENT_SECRET,
        "redirect_uri": UPSTOX_REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": code,
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()

        # Encrypt the access token
        encrypted_token = fernet.encrypt(token_data['access_token'].encode('utf-8'))

        # Store user data in MongoDB, updating if the role already exists
        users_collection.update_one(
            {'role': role},
            {
                '$set': {
                    'user_id': token_data['user_id'],
                    'encrypted_access_token': encrypted_token,
                    'updated_at': datetime.now(timezone.utc)
                }
            },
            upsert=True
        )

        return jsonify({"status": "success", "message": f"Token for {role} has been securely stored."})

    except requests.exceptions.RequestException as e:
        error_detail = str(e)
        try:
            error_detail = response.json().get('errors', [{}])[0].get('message', str(e))
        except Exception:
            pass
        return jsonify({"detail": f"Failed to fetch token: {error_detail}"}), 400
    except Exception as e:
        return jsonify({"detail": f"An unexpected error occurred: {e}"}), 500



@app.route("/api/option_chain/fetch2", methods=['POST'])
def fetch_option_chain():
    """Fetches option chain data from Upstox and stores it in the database."""
    data = request.get_json()
    role = data.get('role')
    instrument_key = data.get('instrument_key')
    expiry_date = data.get('expiry_date')

    # Use expiry_date from request data, not static
    if not all([role, instrument_key, expiry_date]):
        return jsonify({"detail": "Missing role, instrument_key, or expiry_date."}), 400

    user = users_collection.find_one({'role': role})
    if not user:
        return jsonify({"detail": f"Role '{role}' not found."}), 404

    try:
        access_token = fernet.decrypt(user['encrypted_access_token']).decode('utf-8')
    except Exception as e:
        return jsonify({"detail": f"Failed to decrypt access token: {e}"}), 500

    url = "https://api.upstox.com/v2/option/chain"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'instrument_key': instrument_key,
        'expiry_date': expiry_date
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        print("Upstox response:", response.json())
        response.raise_for_status()
        option_chain_data = response.json().get('data')
        underlying_spot_price = response.json().get('underlying', {}).get('spot_price')

        if option_chain_data is None:
            return jsonify({"detail": "No option chain data received from Upstox."}), 404

        # Store data in MongoDB
        option_chain_collection.insert_one({
            'instrument_key': instrument_key,
            'expiry_date': expiry_date,
            'data': option_chain_data,
            'underlying_spot_price': underlying_spot_price,
            'fetched_at': datetime.now(timezone.utc)
        })

        # Trigger metrics calculation after storing new option chain data
        from api_metrics_flask import calculate_metrics_internal
        try:
            calculate_metrics_internal(instrument_key, expiry_date)
        except Exception as e:
            print(f"Error calculating metrics after option chain fetch: {e}")

        return jsonify({"status": "success", "message": "Option chain data fetched and stored."})

    except requests.exceptions.RequestException as e:
        error_detail = str(e)
        try:
            error_detail = response.json().get('errors', [{}])[0].get('message', str(e))
        except Exception:
            pass
        return jsonify({"detail": f"Failed to fetch option chain: {error_detail}"}), 400
    except Exception as e:
        return jsonify({"detail": f"An unexpected error occurred: {e}"}), 500


@app.route("/api/option_chain", methods=['GET'])
def get_option_chain():
    """Retrieves the latest option chain data from the database.""" 
    instrument_key = request.args.get('instrument_key')
    expiry_date = request.args.get('expiry_date')

    if not all([instrument_key, expiry_date]):
        return jsonify({"detail": "Missing instrument_key or expiry_date."}), 400

    latest_data = option_chain_collection.find_one(
        {'instrument_key': instrument_key, 'expiry_date': expiry_date},
        sort=[('fetched_at', -1)]
    )

    if latest_data:
        # Convert ObjectId to string for JSON serialization
        latest_data['_id'] = str(latest_data['_id'])
        return jsonify(latest_data)
    else:
        return jsonify(None)


@app.route("/api/test")
def test_route():
    return "hello"


from api_metrics_flask import metrics_bp

app.register_blueprint(metrics_bp, url_prefix='/api/metrics')

if __name__ == '__main__':
    app.run(port=8000, debug=True)
