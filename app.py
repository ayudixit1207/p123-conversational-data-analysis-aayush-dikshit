from flask import Flask
from Backend.routes import routes
from Backend.database import create_tables

app = Flask(
    __name__,
    template_folder="Frontend/Templates",
    static_folder="Frontend/Static"
)

app.register_blueprint(routes)


@app.route("/health")
def health():

    return {
        "status": "running",
        "project": "Conversational Data Analysis Assistant"
    }


if __name__ == "__main__":

    create_tables()

    app.run(debug=False)