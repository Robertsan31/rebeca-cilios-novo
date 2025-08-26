from pathlib import Path

dashboard_view_code = """from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def dashboard(request):
    return render(request, 'agendamentos/dashboard.html')
"""

dashboard_view_path = "/mnt/data/dashboard_view.py"
Path(dashboard_view_path).write_text(dashboard_view_code, encoding="utf-8")
dashboard_view_path

