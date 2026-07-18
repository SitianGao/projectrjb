export async function authFetch(input, init = {}) {
  const token = localStorage.getItem('auth_token')
  const headers = new Headers(init.headers || {})
  if (token) headers.set('Authorization', `Bearer ${token}`)

  return fetch(input, {
    ...init,
    headers,
  })
}
