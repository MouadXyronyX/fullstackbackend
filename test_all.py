"""Quick API test suite."""
import httpx

base = 'http://localhost:8001'

print('=== SERVER TEST ===\n')

# 1. Health
r = httpx.get(base + '/api/health', timeout=10)
print('1. HEALTH:', r.status_code, r.json()['status'])

# 2. Categories
r = httpx.get(base + '/api/categories/', timeout=10)
print('2. CATEGORIES:', r.status_code, '-', len(r.json()), 'categories')

# 3. Products
r = httpx.get(base + '/api/products/', timeout=10)
print('3. PRODUCTS:', r.status_code, '-', len(r.json()), 'products')

# 4. Settings
r = httpx.get(base + '/api/settings/public', timeout=10)
print('4. SETTINGS:', r.status_code, '-', list(r.json().keys()))

# 5. Login
r = httpx.post(base + '/api/auth/login',
    json={'email': 'admin@alquds-store.com', 'password': 'admin123456'}, timeout=10)
print('5. LOGIN:', r.status_code)
token = r.json().get('access_token', '')

# 6. Dashboard (admin)
headers = {'Authorization': 'Bearer ' + token}
r = httpx.get(base + '/api/dashboard/stats', headers=headers, timeout=10)
if r.status_code == 200:
    d = r.json()
    print('6. DASHBOARD:', r.status_code, '- products:', d['total_products'],
          ', orders:', d['total_orders'], ', revenue:', d['total_revenue'])

# 7. Users
r = httpx.get(base + '/api/users/', headers=headers, timeout=10)
print('7. USERS:', r.status_code, '-', len(r.json()), 'users')

print('\nDone!')
