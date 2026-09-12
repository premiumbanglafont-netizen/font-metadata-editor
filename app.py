import io
from flask import Flask, render_template, request, send_file, jsonify
from fontTools.ttLib import TTFont

app = Flask(__name__)

def get_name_record(name_table, name_id):
    """মেটাডেটা আইডি থেকে মান এক্সট্রাক্ট করার সেফ ফাংশন"""
    rec = name_table.getName(name_id, 3, 1, 0x409) or name_table.getName(name_id, 1, 0, 0)
    if not rec:
        for r in name_table.names:
            if r.nameID == name_id:
                rec = r
                break
    if rec:
        try:
            return rec.toUnicode()
        except Exception:
            return str(rec.string.decode('latin-1', errors='ignore'))
    return ""

def set_name_record(name_table, name_id, value):
    """মেটাডেটা আইডিতে নতুন মান সেট করার সেফ ফাংশন"""
    if value is None:
        return
    name_table.setName(value, name_id, 3, 1, 0x409)
    name_table.setName(value, name_id, 1, 0, 0)

@app.route('/')
def index():
    return render_template('index.html')

# ১. ফন্ট সিলেক্ট করার পর মেটাডেটা ফেচ করার রুট
@app.route('/get-metadata', methods=['POST'])
def get_metadata():
    if 'font_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['font_file']
    
    try:
        font = TTFont(file)
        name_table = font['name']
        
        metadata = {
            'fontFamily': get_name_record(name_table, 1),
            'fontSubfamily': get_name_record(name_table, 2) or 'Regular',
            'uniqueID': get_name_record(name_table, 3),
            'fullName': get_name_record(name_table, 4),
            'version': get_name_record(name_table, 5) or 'Version 1.00',
            'postScriptName': get_name_record(name_table, 6),
            'manufacturer': get_name_record(name_table, 8),
            'designer': get_name_record(name_table, 9),
            'copyright': get_name_record(name_table, 0),
            'license': get_name_record(name_table, 13)
        }
        return jsonify(metadata)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ২. এডিট করার পর ফন্ট সেভ ও ডাউনলোড করার রুট
@app.route('/edit', methods=['POST'])
def edit_font():
    if 'font_file' not in request.files:
        return "No file uploaded", 400
    file = request.files['font_file']
    
    try:
        font = TTFont(file)
        name_table = font['name']

        set_name_record(name_table, 1, request.form.get('fontFamily'))
        set_name_record(name_table, 2, request.form.get('fontSubfamily'))
        set_name_record(name_table, 3, request.form.get('uniqueID'))
        set_name_record(name_table, 4, request.form.get('fullName'))
        set_name_record(name_table, 5, request.form.get('version'))
        set_name_record(name_table, 6, request.form.get('postScriptName'))
        set_name_record(name_table, 8, request.form.get('manufacturer'))
        set_name_record(name_table, 9, request.form.get('designer'))
        set_name_record(name_table, 0, request.form.get('copyright'))
        set_name_record(name_table, 13, request.form.get('license'))

        output = io.BytesIO()
        font.save(output)
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name=f"edited_{file.filename}",
            mimetype='font/ttf'
        )
    except Exception as e:
        return f"Error: {str(e)}", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
