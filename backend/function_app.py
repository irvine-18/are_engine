
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import azure.functions as func

from src.api import assets, curves, economic_data, jobs, parameters, portfolios, runs, scenarios, health

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

app.register_blueprint(economic_data.bp)
app.register_blueprint(parameters.bp)
app.register_blueprint(scenarios.bp)
app.register_blueprint(curves.bp)
app.register_blueprint(assets.bp)
app.register_blueprint(portfolios.bp)
app.register_blueprint(runs.bp)
app.register_blueprint(jobs.bp)
app.register_blueprint(health.bp)
