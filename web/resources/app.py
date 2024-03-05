from flask import Flask, render_template, jsonify
import subprocess

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_project', methods=['POST'])
def start_project():
    try:
        # Start your Python project and capture the output, AnythingTrackerUI, src/anything_tracker/web_connect_specific/
        result = subprocess.run(['python', 'web/resources/hello.py'], stdout=subprocess.PIPE, text=True)
        output = result.stdout
        print(output)
        response = jsonify({'output': output}).get_data(as_text=True)
        print(response)
        # Return the output to the webpage
        return response
        # return jsonify({'output': output})
    except:
        return jsonify({'success': False, 'error': "hhh"})


if __name__ == '__main__':
    app.run(debug=True, port=5002)
