import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import cadquery as cq

app = Flask(__name__)
# Enable CORS for all domains so your website can talk to this server
CORS(app)

UPLOAD_FOLDER = '/tmp'  # Use tmp for cloud environments
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# PRICING DATA
MATERIALS = {
    'AL6061': {'base_cost': 0.05, 'machinability': 1.0},
    'SS304':  {'base_cost': 0.15, 'machinability': 2.5},
    'DELRIN': {'base_cost': 0.08, 'machinability': 0.8}
}

TOLERANCES = {
    'ISO-2768-c': 1.0,
    'ISO-2768-m': 1.1,
    'ISO-2768-f': 1.5
}

FINISHES = {
    'As-Machined': 0,
    'Bead Blast': 25,
    'Anodize Type II': 50
}

def analyze_step(filepath):
    try:
        model = cq.importers.importStep(filepath)
        vol_mm3 = model.val().Volume()
        vol_cm3 = vol_mm3 / 1000.0
        
        bb = model.val().BoundingBox()
        stock_vol_cm3 = (bb.xlen * bb.ylen * bb.zlen) / 1000.0
        
        return {'vol_cm3': vol_cm3, 'stock_vol_cm3': stock_vol_cm3}
    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route('/', methods=['GET'])
def health_check():
    return "CNC Engine is Running!", 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    data = analyze_step(filepath)
    # Clean up file to save space
    os.remove(filepath)
    
    if not data:
        return jsonify({'error': 'Invalid STEP file'}), 500
        
    return jsonify({'geometry': data})

@app.route('/quote', methods=['POST'])
def quote():
    data = request.json
    geo = data['geometry']
    
    # Extract Costs
    mat = MATERIALS[data['material']]
    tol_mult = TOLERANCES[data['tolerance']]
    finish_cost = FINISHES[data['finish']]
    qty = int(data['quantity'])
    
    # Calculation
    mat_cost = geo['stock_vol_cm3'] * mat['base_cost']
    machining_cost = (geo['stock_vol_cm3'] - geo['vol_cm3']) * mat['machinability'] * 0.5 # $0.50 per cm3 removed rate
    setup_cost = 50.0
    
    unit_price = ((mat_cost + machining_cost) * tol_mult) + finish_cost + (setup_cost / qty)
    
    return jsonify({
        'unit_price': round(unit_price, 2),
        'total_price': round(unit_price * qty, 2)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
