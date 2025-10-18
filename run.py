"""
Usage:
1. Clone the repo.
2. Activate your virtual environment with dependencies.
3. Change the working directory to parent directory of this project.
4. Run the following cmd:
    `python run.py`
"""

from blur_suite.interactive import BlurSuiteApp

app = BlurSuiteApp()
app.create_gui()
app.run()
