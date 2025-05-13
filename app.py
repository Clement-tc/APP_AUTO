from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=["GET"])
def home():
    return render_template('home.html', result=None)

@app.route('/calculer', methods=["POST"])
def calculer():
    try:
        A = float(request.form.get("valeurA"))
        B = float(request.form.get("valeurB"))
        op = request.form.get("operator")

        if op == "+":
            result = A + B
        elif op == "-":
            result = A - B
        elif op == "*":
            result = A * B
        elif op == "/":
            result = A / B if B != 0 else "Division par zéro"
        else:
            result = "Opérateur invalide"
    except Exception as e:
        result = f"Erreur : {e}"

    return render_template('home.html', result=result)

@app.route('/promo', methods=["GET"])
def ma_get_route():
    return "MD5"

if __name__ == '__main__':
    app.run(debug=True)
