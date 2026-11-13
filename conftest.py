import os
import tempfile

# Point the app at a throwaway database before app.py is imported.
os.environ["LEAVE_DB"] = os.path.join(tempfile.mkdtemp(), "test_leave.db")
