import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("firestore_key.json")
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    
    print("Fetching work_sessions...")
    docs = db.collection('work_sessions').stream()
    
    count = 0
    for doc in docs:
        data = doc.to_dict()
        print(f"ID: {doc.id}")
        print(f"Task: {data.get('task')}")
        print(f"Date: {data.get('date')}")
        print(f"Created At: {data.get('created_at')}")
        print("-" * 20)
        count += 1
        if count >= 5: break
        
    if count == 0:
        print("No sessions found.")

except Exception as e:
    print(f"Error: {e}")
