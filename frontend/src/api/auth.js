const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';
export async function login(email, password) {
  try {
    const res = await fetch(`${BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) throw new Error('Login failed');

    const data = await res.json();
    if (!data.user || !data.user.id || !data.token) {
      throw new Error('User ID or token missing in response');
    }

    localStorage.setItem('token', data.token);
    localStorage.setItem('userId', data.user.id);
    localStorage.setItem('email', data.user.email);

    return data;

  } catch (err) {
    alert(err.message);
  }
}

export async function register(email, password) {
  const res = await fetch(`${BASE_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error('Register failed');
  const data = await res.json();
  if (!data.user || !data.user.id || !data.token) throw new Error('Invalid register response');

  localStorage.setItem('token', data.token);
  localStorage.setItem('userId', data.user.id);
  localStorage.setItem('email', data.user.email);

  return data;
}
