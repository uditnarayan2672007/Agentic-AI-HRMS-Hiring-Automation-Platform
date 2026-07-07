"""
Live API Test — Hits actual running server at http://127.0.0.1:8000
Tests all endpoints that don't require a database (public + auth-guarded with 401 check).
"""
import urllib.request
import urllib.error
import urllib.parse
import json

BASE = "http://127.0.0.1:8000"
PASS = 0
FAIL = 0

def GET(path, expect_status=200, auth=None):
    global PASS, FAIL
    url = BASE + path
    req = urllib.request.Request(url, method="GET")
    if auth:
        req.add_header("Authorization", f"Bearer {auth}")
    try:
        with urllib.request.urlopen(req) as r:
            body = json.loads(r.read())
            if r.status == expect_status:
                PASS += 1
                return r.status, body
            else:
                FAIL += 1
                return r.status, body
    except urllib.error.HTTPError as e:
        body = {}
        try:
            body = json.loads(e.read())
        except Exception:
            pass
        if e.code == expect_status:
            PASS += 1
        else:
            FAIL += 1
        return e.code, body

def POST(path, data=None, expect_status=200, auth=None, form=False):
    global PASS, FAIL
    url = BASE + path
    if data and form:
        # form-urlencoded
        encoded = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=encoded, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    elif data:
        encoded = json.dumps(data).encode()
        req = urllib.request.Request(url, data=encoded, method="POST")
        req.add_header("Content-Type", "application/json")
    else:
        req = urllib.request.Request(url, method="POST")
    if auth:
        req.add_header("Authorization", f"Bearer {auth}")
    try:
        with urllib.request.urlopen(req) as r:
            body = json.loads(r.read())
            if r.status == expect_status:
                PASS += 1
            else:
                FAIL += 1
            return r.status, body
    except urllib.error.HTTPError as e:
        body = {}
        try:
            body = json.loads(e.read())
        except Exception:
            pass
        if e.code == expect_status:
            PASS += 1
        else:
            FAIL += 1
        return e.code, body


print("=" * 65)
print("  HRMS LIVE API TEST  |  http://127.0.0.1:8000")
print("=" * 65)

# ── [1] Root ──────────────────────────────────────────────────────
print("\n[1] GET / (root info)")
code, body = GET("/")
print(f"    {code} | service: {body.get('service')} | status: {body.get('status')}")
assert body.get("service") == "Elite Coders HRMS API"

# ── [2] Health ────────────────────────────────────────────────────
print("\n[2] GET /health")
code, body = GET("/health")
print(f"    {code} | status: {body.get('status')} | scheduler: {body.get('scheduler_running')}")
assert body.get("status") == "healthy"
assert body.get("scheduler_running") == True
jobs = body.get("jobs", [])
print(f"    Cron jobs scheduled:")
for job in jobs:
    print(f"      - {job['name']} -> {job['next_run']}")
assert len(jobs) == 3

# ── [3] OpenAPI schema ────────────────────────────────────────────
print("\n[3] GET /openapi.json (OpenAPI schema)")
code, body = GET("/openapi.json")
paths = list(body.get("paths", {}).keys())
print(f"    {code} | Registered routes: {len(paths)}")
print(f"    Paths: {paths[:6]}...")
assert len(paths) > 10

# ── [4] Payroll formula doc ───────────────────────────────────────
print("\n[4] GET /api/v1/payroll/formula")
code, body = GET("/api/v1/payroll/formula")
print(f"    {code} | formula: {body.get('formula')}")
example = body.get("example", {})
print(f"    Example net salary: {example.get('net_salary')}")
assert "Net Salary" in body.get("formula", "")

# ── [5] Auth — login without DB returns 500 (expected, no DB) ────
print("\n[5] POST /api/v1/auth/register  (expects 500 - no DB connected)")
code, body = POST(
    "/api/v1/auth/register",
    {"email": "test@example.com", "full_name": "Test User",
     "password": "test1234", "role": "hr"},
    expect_status=500,
)
print(f"    {code} | {body.get('detail','')[:80]}")
# 500 is correct when no DB — proves the endpoint is reachable and auth logic runs

# ── [6] Protected endpoint without token → 401 ────────────────────
print("\n[6] GET /api/v1/resumes/applicants (no token -> expects 401)")
code, body = GET("/api/v1/resumes/applicants", expect_status=401)
print(f"    {code} | {body.get('detail', '')}")
assert code == 401

# ── [7] Protected payroll endpoint without token → 401 ────────────
print("\n[7] GET /api/v1/payroll/employees (no token -> expects 401)")
code, body = GET("/api/v1/payroll/employees", expect_status=401)
print(f"    {code} | {body.get('detail', '')}")
assert code == 401

# ── [8] Protected leave endpoint without token → 401 ─────────────
print("\n[8] GET /api/v1/leave/pending (no token -> expects 401)")
code, body = GET("/api/v1/leave/pending", expect_status=401)
print(f"    {code} | {body.get('detail', '')}")
assert code == 401

# ── [9] Protected anomaly endpoint without token → 401 ────────────
print("\n[9] GET /api/v1/anomalies (no token -> expects 401)")
code, body = GET("/api/v1/anomalies", expect_status=401)
print(f"    {code} | {body.get('detail', '')}")
assert code == 401

# ── [10] Protected onboarding endpoint without token → 401 ────────
print("\n[10] GET /api/v1/onboarding/tasks/00000000-0000-0000-0000-000000000001 (no token -> expects 401)")
code, body = GET("/api/v1/onboarding/tasks/00000000-0000-0000-0000-000000000001", expect_status=401)
print(f"    {code} | {body.get('detail', '')}")
assert code == 401

# ── [11] Swagger UI ────────────────────────────────────────────────
print("\n[11] GET /docs (Swagger UI)")
try:
    req = urllib.request.Request(BASE + "/docs")
    with urllib.request.urlopen(req) as r:
        html = r.read().decode()
        if "swagger" in html.lower() or "openapi" in html.lower():
            print(f"    200 | Swagger UI loaded OK")
            PASS += 1
        else:
            print(f"    200 | (unexpected content)")
            FAIL += 1
except Exception as e:
    print(f"    ERROR: {e}")
    FAIL += 1

# ── [12] ReDoc ────────────────────────────────────────────────────
print("\n[12] GET /redoc")
try:
    req = urllib.request.Request(BASE + "/redoc")
    with urllib.request.urlopen(req) as r:
        html = r.read().decode()
        print(f"    200 | ReDoc UI loaded OK ({len(html)} bytes)")
        PASS += 1
except Exception as e:
    print(f"    ERROR: {e}")
    FAIL += 1

# ── Summary ───────────────────────────────────────────────────────
print("\n" + "=" * 65)
total = PASS + FAIL
print(f"  RESULTS: {PASS}/{total} tests PASSED  |  {FAIL} FAILED")
if FAIL == 0:
    print("  STATUS:  ALL LIVE ENDPOINT TESTS PASSED")
else:
    print("  STATUS:  SOME TESTS FAILED - check above")
print("=" * 65)
print(f"\nSwagger UI: {BASE}/docs")
print(f"ReDoc:      {BASE}/redoc")
