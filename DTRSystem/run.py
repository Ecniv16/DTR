from app import app


app.secret_key = "super secret key"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8969)
