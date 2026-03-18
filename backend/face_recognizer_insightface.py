"""
Face recognition using InsightFace (ArcFace embeddings).
Much more robust to appearance changes like glasses, lighting, angles.
Loads face images from faces/images/ directory.
Uses InsightFace as the primary face recognition method.
"""
import os
import re
import numpy as np
import cv2
import pickle
import mysql.connector
from insightface.app import FaceAnalysis

# Import DB config (same file used by app.py)
try:
    from attendance_config import DB_CFG
except ImportError:
    DB_CFG = {"host": "localhost", "user": "root", "password": "", "database": "office_attendance"}

# ── globals ───────────────────────────────────────────────────────────────
_face_app = None
_known_embeddings = {}  # emp_id -> list of embeddings
_trained = False

# Root of the project (one level above backend/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Face images used for recognition are stored here
FACES_IMAGES_DIR = os.path.join(PROJECT_ROOT, "faces", "images")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")

# ── InsightFace initialization ───────────────────────────────────────────────
def _init_insightface():
    global _face_app
    if _face_app is not None:
        return _face_app
    
    try:
        # Set model cache directory
        import os
        os.environ['INSIGHTFACE_HOME'] = os.path.expanduser('~/.insightface')
        
        # Initialize InsightFace - try different model names
        # buffalo_l is the recommended model, but if it fails, try others
        try:
            print("[RECOG] Trying buffalo_l model...")
            _face_app = FaceAnalysis(name='buffalo_l', root=os.path.expanduser('~/.insightface'))
        except:
            print("[RECOG] buffalo_l failed, trying buffalo_sc...")
            try:
                _face_app = FaceAnalysis(name='buffalo_sc', root=os.path.expanduser('~/.insightface'))
            except:
                print("[RECOG] buffalo_sc failed, trying default model...")
                _face_app = FaceAnalysis(name='buffalo_l')
        
        _face_app.prepare(ctx_id=-1, det_thresh=0.5, det_size=(640, 640))
        
        print("[RECOG] 🎯 Using InsightFace with ArcFace embeddings")
        return _face_app
        
    except Exception as e:
        print(f"[RECOG] ❌ InsightFace initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

# ── Load and train faces ───────────────────────────────────────────────────
def _load_known_faces(force=False):
    global _trained, _known_embeddings, _face_app
    
    if _trained and not force:
        return
    
    _face_app = _init_insightface()
    if _face_app is None:
        print("[RECOG] ❌ Cannot load faces - InsightFace not initialized")
        return
    
    if not os.path.exists(FACES_IMAGES_DIR):
        print(f"[RECOG] ❌ Faces directory not found: {FACES_IMAGES_DIR}")
        return
    
    # Load face images and extract embeddings
    _known_embeddings = {}
    total_faces = 0
    
    print("[RECOG] Loading face images and extracting embeddings...")
    
    # ── Get the set of ACTIVE employee IDs from DB to avoid loading orphaned photos ──
    valid_emp_ids = set()
    try:
        db = mysql.connector.connect(**DB_CFG)
        cur = db.cursor()
        cur.execute("SELECT emp_id FROM employees WHERE status = 'Active'")
        valid_emp_ids = {row[0].lower() for row in cur.fetchall()}
        cur.close()
        db.close()
        print(f"[RECOG] ✅ Active employees in DB: {sorted(valid_emp_ids)}")
    except Exception as db_err:
        print(f"[RECOG] ⚠️ Could not fetch employee list from DB ({db_err}); loading ALL face images")
        # If DB is unreachable, fall back to loading everything (safe degraded mode)
        valid_emp_ids = None  # None means "skip DB filter"
    
    for fname in os.listdir(FACES_IMAGES_DIR):
        if not fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
            
        # Only support emp001.jpg format (one image per employee)
        m = re.match(r'^([a-zA-Z0-9]+)\.(jpg|jpeg|png)$', fname, re.I)
        if not m:
            continue
            
        emp_id = m.group(1).lower()
        
        # ── Skip if this emp_id is NOT an active employee in the DB ──
        if valid_emp_ids is not None and emp_id not in valid_emp_ids:
            print(f"[RECOG] ⚠️ Skipping {fname} — '{emp_id}' is not an active employee in DB")
            continue
        
        path = os.path.join(FACES_IMAGES_DIR, fname)
        
        try:
            # Load image
            img = cv2.imread(path)
            if img is None:
                print(f"[RECOG] ❌ Cannot load image: {fname}")
                continue
            
            # Detect and extract face embeddings
            faces = _face_app.get(img)
            
            if len(faces) == 0:
                print(f"[RECOG] ❌ No face detected in {fname}")
                continue
            
            # Use the largest detected face
            face = max(faces, key=lambda f: f.bbox[2] * f.bbox[3])
            embedding = face.embedding
            
            # Store single embedding for this employee
            _known_embeddings[emp_id] = embedding
            total_faces += 1
            
            print(f"[RECOG] ✅ Extracted embedding for {emp_id} from {fname}")
            
        except Exception as e:
            print(f"[RECOG] ❌ Error processing {fname}: {e}")
    
    if len(_known_embeddings) == 0:
        print("[RECOG] ❌ No valid faces found for training")
        return
    
    # Save embeddings
    try:
        os.makedirs(MODEL_DIR, exist_ok=True)
        embeddings_path = os.path.join(MODEL_DIR, "face_embeddings.pkl")
        with open(embeddings_path, 'wb') as f:
            pickle.dump(_known_embeddings, f)
        
        _trained = True
        print(f"[RECOG] ✅ Trained with {total_faces} faces for {len(_known_embeddings)} employees")
        print(f"[RECOG] ✅ Embeddings saved to {embeddings_path}")
        
    except Exception as e:
        print(f"[RECOG] ❌ Failed to save embeddings: {e}")
        _trained = False

# ── Load trained embeddings if exists ────────────────────────────────────────
def _load_trained_embeddings():
    global _trained, _known_embeddings, _face_app
    
    embeddings_path = os.path.join(MODEL_DIR, "face_embeddings.pkl")
    
    if not os.path.exists(embeddings_path):
        return False
    
    try:
        _face_app = _init_insightface()
        if _face_app is None:
            return False
        
        with open(embeddings_path, 'rb') as f:
            _known_embeddings = pickle.load(f)
        
        _trained = True
        print(f"[RECOG] ✅ Loaded trained embeddings from {embeddings_path}")
        print(f"[RECOG] ✅ Loaded {len(_known_embeddings)} employees")
        return True
        
    except Exception as e:
        print(f"[RECOG] ❌ Failed to load embeddings: {e}")
        return False

# ── Cosine similarity ────────────────────────────────────────────────────────
def _cosine_similarity(embedding1, embedding2):
    """Calculate cosine similarity between two embeddings"""
    # Normalize embeddings
    emb1 = embedding1 / np.linalg.norm(embedding1)
    emb2 = embedding2 / np.linalg.norm(embedding2)
    
    # Cosine similarity
    similarity = np.dot(emb1, emb2)
    return similarity

# ── Public API ───────────────────────────────────────────────────────────────
def recognize_face(image_bytes: bytes):
    """
    Identify an employee from a raw image (JPEG/PNG bytes) using InsightFace.
    Returns: (emp_id: str|None, similarity: float)
    """
    try:
        # Initialize InsightFace
        _face_app = _init_insightface()
        if _face_app is None:
            return None, 0.0
        
        # Load trained embeddings or train new ones
        if not _trained:
            if not _load_trained_embeddings():
                _load_known_faces()
                if not _trained:
                    print("[RECOG] ❌ No trained embeddings available")
                    return None, 0.0
        
        # Process input image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("[RECOG] ❌ Cannot decode input image")
            return None, 0.0
        
        # Detect faces and extract embeddings
        faces = _face_app.get(img)
        
        print(f"[RECOG] 🔍 Detected {len(faces)} faces")
        
        if len(faces) == 0:
            print("[RECOG] ❌ No face detected in input image")
            return None, 0.0
        
        # Use the largest detected face
        face = max(faces, key=lambda f: f.bbox[2] * f.bbox[3])
        input_embedding = face.embedding
        
        # Find best match among known embeddings
        best_emp_id = None
        best_similarity = -1.0
        second_best_similarity = -1.0
        threshold = 0.55  # Minimum similarity threshold (ArcFace: genuine match ≥ 0.5)
        confidence_gap = 0.05  # Require at least 5% gap between best and second-best
        
        # Store all matches for debugging
        all_matches = []
        
        for emp_id, known_embedding in _known_embeddings.items():
            # Compare with stored embedding
            similarity = _cosine_similarity(input_embedding, known_embedding)
            all_matches.append((emp_id, similarity))
            
            if similarity > best_similarity:
                second_best_similarity = best_similarity
                best_similarity = similarity
                best_emp_id = emp_id
            elif similarity > second_best_similarity:
                second_best_similarity = similarity
        
        # Log all matches for debugging
        print(f"[RECOG] 🔍 All matches:")
        for emp_id, sim in sorted(all_matches, key=lambda x: x[1], reverse=True):
            print(f"  - {emp_id}: {sim:.3f}")
        
        print(f"[RECOG] 🔍 Best match: {best_emp_id} (similarity: {best_similarity:.3f})")
        print(f"[RECOG] 🔍 Second best: {second_best_similarity:.3f}")
        print(f"[RECOG] 🔍 Gap: {(best_similarity - second_best_similarity):.3f}, Threshold: {threshold}, Min Gap: {confidence_gap}")
        
        # Check both threshold and confidence gap
        if best_similarity >= threshold and (best_similarity - second_best_similarity) >= confidence_gap:
            print(f"[RECOG] ✅ Recognized {best_emp_id} (similarity: {best_similarity:.3f}, gap: {(best_similarity - second_best_similarity):.3f})")
            return best_emp_id, best_similarity
        
        if best_similarity >= threshold and (best_similarity - second_best_similarity) < confidence_gap:
            print(f"[RECOG] ❌ Face ambiguous - too close to another employee (gap: {(best_similarity - second_best_similarity):.3f} < {confidence_gap})")
        else:
            print(f"[RECOG] ❌ Face not recognized (similarity: {best_similarity:.3f} below threshold {threshold})")
        return None, 0.0
        
    except Exception as e:
        print(f"[RECOG] ❌ Recognition error: {e}")
        import traceback
        traceback.print_exc()
        return None, 0.0

def reload_faces():
    """Force-reload and retrain all face embeddings (DB-filtered)."""
    global _trained
    _trained = False
    _load_known_faces(force=True)
    print(f"[RECOG] Reloaded — {len(_known_embeddings)} employee(s) trained")

def remove_embedding(emp_id: str):
    """
    Remove a stale embedding for emp_id from memory and disk.
    Called automatically when face recognition returns an emp_id
    that no longer exists in the employees table.
    """
    global _known_embeddings
    emp_id_lower = emp_id.lower()
    if emp_id_lower in _known_embeddings:
        del _known_embeddings[emp_id_lower]
        print(f"[RECOG] 🧹 Removed stale embedding for '{emp_id_lower}' from memory")
        # Persist updated embeddings to disk
        try:
            embeddings_path = os.path.join(MODEL_DIR, "face_embeddings.pkl")
            with open(embeddings_path, 'wb') as f:
                pickle.dump(_known_embeddings, f)
            print(f"[RECOG] 🧹 Saved cleaned embeddings ({len(_known_embeddings)} employees remaining)")
        except Exception as e:
            print(f"[RECOG] ⚠️ Could not save cleaned embeddings: {e}")
    else:
        print(f"[RECOG] ℹ️ '{emp_id_lower}' not in embeddings — nothing to remove")

# ── Initialize on import ───────────────────────────────────────────────────────
# Try to load existing embeddings first, otherwise train new ones
if not _load_trained_embeddings():
    _load_known_faces()
