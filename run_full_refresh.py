"""Run the complete Python model and refresh the browser application data."""
from run_pipeline import main as run_model
from sync_web_app_data import main as sync_web_app


if __name__ == "__main__":
    print("Running SARIMA forecasting, intervention scenarios, costing, and plots...")
    run_model()
    print("Refreshing the HTML/CSS/JavaScript application data...")
    sync_web_app()
    print("Complete. Start the app with: python web_app/serve_app.py")
