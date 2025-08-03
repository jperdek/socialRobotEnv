import sys
from flask import Flask
import flask_cors



app = Flask(
    __name__,
    static_url_path="",
    static_folder="web/static",
    template_folder="web/templates",
)

flask_cors.CORS(app)
app.register_blueprint(ast_convertion_api, url_prefix="/tests")
app.register_blueprint(python_complexity_api, url_prefix="/robotMovement")
app.register_blueprint(python_complexity_api, url_prefix="/exercises")


@app.route("/", methods=["GET"])
def check_if_service_is_up():
    return "OK", 200, {"content-type": "text/html"}


with app.app_context():
    print("Preparing for requests execution...")
    # g.fully_automated_product_lines_knowledge_manager = FullyAutomatedProductLinesKnowledgeManager()
    print("Preparation completed successfully!")


def launch():
    app.run(host="0.0.0.0", debug=False)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "production":
        app.run(host="0.0.0.0", debug=False, port=8080)
    else:
        app.run(host="0.0.0.0", debug=True)