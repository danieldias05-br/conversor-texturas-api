from flask import Flask, request, send_file
import os, uuid, zipfile, shutil, json
from PIL import Image

app = Flask(__name__)

def convert_pack(input_zip, output_dir):
    temp_id = str(uuid.uuid4())
    extract_path = f"/tmp/{temp_id}_extract"
    os.makedirs(extract_path, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(input_zip, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    bedrock_textures_path = os.path.join(output_dir, 'textures')
    os.makedirs(bedrock_textures_path, exist_ok=True)

    java_texture_path = os.path.join(extract_path, "assets", "minecraft", "textures")

    for root, _, files in os.walk(java_texture_path):
        for file in files:
            if file.endswith(('.png', '.tga')):
                src = os.path.join(root, file)
                rel_path = os.path.relpath(src, java_texture_path)
                dest = os.path.join(bedrock_textures_path, rel_path)
                os.makedirs(os.path.dirname(dest), exist_ok=True)

                if file.endswith('.tga'):
                    img = Image.open(src)
                    dest = dest.replace('.tga', '.png')
                    img.save(dest)
                else:
                    shutil.copy2(src, dest)

    manifest = {
        "format_version": 2,
        "header": {
            "name": "Java para Bedrock Textures",
            "uuid": str(uuid.uuid4()),
            "version": [1, 0, 0]
        },
        "modules": [{
            "type": "resources",
            "uuid": str(uuid.uuid4()),
            "version": [1, 0, 0]
        }]
    }

    with open(os.path.join(output_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=4)

    mcpack_path = f"/tmp/{temp_id}.mcpack"
    shutil.make_archive(mcpack_path.replace('.mcpack', ''), 'zip', output_dir)
    os.rename(mcpack_path + ".zip", mcpack_path)
    return mcpack_path

@app.route('/convert', methods=['POST'])
def convert():
    file = request.files['file']
    temp_zip = f"/tmp/{uuid.uuid4()}.zip"
    file.save(temp_zip)

    output_dir = f"/tmp/{uuid.uuid4()}_output"
    mcpack = convert_pack(temp_zip, output_dir)
    return send_file(mcpack, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
