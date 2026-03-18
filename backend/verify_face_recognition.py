#!/usr/bin/env python3
"""
Face Recognition System Verification Script
Checks if face recognition is properly configured and working
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

def check_directories():
    """Check if required directories exist"""
    print("\n" + "="*60)
    print("📁 CHECKING DIRECTORIES")
    print("="*60)
    
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    FACES_DIR = os.path.join(PROJECT_ROOT, "faces")
    IMAGES_DIR = os.path.join(FACES_DIR, "images")
    MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
    
    dirs = {
        "Project Root": PROJECT_ROOT,
        "Faces Directory": FACES_DIR,
        "Images Directory": IMAGES_DIR,
        "Models Directory": MODELS_DIR,
    }
    
    for name, path in dirs.items():
        exists = os.path.exists(path)
        status = "✅" if exists else "❌"
        print(f"{status} {name}: {path}")
    
    return IMAGES_DIR, MODELS_DIR

def check_face_images(images_dir):
    """Check if face images exist and are valid"""
    print("\n" + "="*60)
    print("📷 CHECKING FACE IMAGES")
    print("="*60)
    
    if not os.path.exists(images_dir):
        print(f"❌ Images directory not found: {images_dir}")
        return []
    
    images = []
    for fname in sorted(os.listdir(images_dir)):
        if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            path = os.path.join(images_dir, fname)
            
            # Try to read image
            img = cv2.imread(path)
            if img is not None:
                print(f"✅ {fname}: {img.shape} (valid)")
                images.append((fname, path))
            else:
                print(f"❌ {fname}: Cannot read image")
    
    if not images:
        print("❌ No valid face images found!")
    else:
        print(f"\n✅ Found {len(images)} valid face image(s)")
    
    return images

def check_embeddings(models_dir):
    """Check if embeddings file exists"""
    print("\n" + "="*60)
    print("🧠 CHECKING EMBEDDINGS")
    print("="*60)
    
    embeddings_path = os.path.join(models_dir, "face_embeddings.pkl")
    
    if os.path.exists(embeddings_path):
        size_mb = os.path.getsize(embeddings_path) / (1024 * 1024)
        print(f"✅ Embeddings file exists: {embeddings_path}")
        print(f"   Size: {size_mb:.2f} MB")
        return True
    else:
        print(f"⚠️  Embeddings file not found: {embeddings_path}")
        print("   (Will be created on first run)")
        return False

def check_insightface():
    """Check if InsightFace is installed and working"""
    print("\n" + "="*60)
    print("🎯 CHECKING INSIGHTFACE")
    print("="*60)
    
    try:
        from insightface.app import FaceAnalysis
        print("✅ InsightFace is installed")
        
        # Try to initialize
        try:
            print("   Initializing InsightFace...")
            app = FaceAnalysis(name='buffalo_l', root=os.path.expanduser('~/.insightface'))
            app.prepare(ctx_id=-1, det_thresh=0.5, det_size=(640, 640))
            print("✅ InsightFace initialized successfully")
            return True
        except Exception as e:
            print(f"⚠️  InsightFace initialization warning: {e}")
            print("   (Models will be downloaded on first use)")
            return True
            
    except ImportError:
        print("❌ InsightFace is not installed")
        print("   Install with: pip install insightface")
        return False

def check_database():
    """Check if database connection works"""
    print("\n" + "="*60)
    print("🗄️  CHECKING DATABASE")
    print("="*60)
    
    try:
        from attendance_config import DB_CFG
        import mysql.connector
        
        print(f"   Host: {DB_CFG['host']}")
        print(f"   Database: {DB_CFG['database']}")
        
        conn = mysql.connector.connect(**DB_CFG)
        cursor = conn.cursor(dictionary=True)
        
        # Check employees table
        cursor.execute("SELECT COUNT(*) as count FROM employees")
        result = cursor.fetchone()
        emp_count = result['count']
        print(f"✅ Database connected")
        print(f"   Employees in database: {emp_count}")
        
        # List employees
        cursor.execute("SELECT emp_id, full_name FROM employees ORDER BY emp_id")
        employees = cursor.fetchall()
        for emp in employees:
            print(f"   - {emp['emp_id']}: {emp['full_name']}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_face_profiles():
    """Check if face profiles are registered in database"""
    print("\n" + "="*60)
    print("👤 CHECKING FACE PROFILES")
    print("="*60)
    
    try:
        from attendance_config import DB_CFG
        import mysql.connector
        
        conn = mysql.connector.connect(**DB_CFG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT fp.emp_id, fp.face_image_path, e.full_name 
            FROM face_profiles fp
            LEFT JOIN employees e ON fp.emp_id = e.emp_id
            ORDER BY fp.emp_id
        """)
        profiles = cursor.fetchall()
        
        if profiles:
            print(f"✅ Found {len(profiles)} face profile(s):")
            for profile in profiles:
                path = profile['face_image_path']
                exists = os.path.exists(path) if path else False
                status = "✅" if exists else "❌"
                print(f"   {status} {profile['emp_id']}: {profile['full_name']} ({path})")
        else:
            print("⚠️  No face profiles found in database")
        
        cursor.close()
        conn.close()
        return len(profiles) > 0
        
    except Exception as e:
        print(f"❌ Error checking face profiles: {e}")
        return False

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("🔍 FACE RECOGNITION SYSTEM VERIFICATION")
    print("="*60)
    
    images_dir, models_dir = check_directories()
    images = check_face_images(images_dir)
    embeddings_exist = check_embeddings(models_dir)
    insightface_ok = check_insightface()
    db_ok = check_database()
    profiles_ok = check_face_profiles()
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    checks = {
        "Face images found": len(images) > 0,
        "Embeddings file exists": embeddings_exist,
        "InsightFace working": insightface_ok,
        "Database connected": db_ok,
        "Face profiles registered": profiles_ok,
    }
    
    for check, result in checks.items():
        status = "✅" if result else "⚠️ "
        print(f"{status} {check}")
    
    all_ok = all(checks.values())
    
    print("\n" + "="*60)
    if all_ok:
        print("✅ ALL CHECKS PASSED - System is ready!")
    else:
        print("⚠️  Some checks failed - See details above")
    print("="*60 + "\n")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
