const BASE_URL = import.meta.env.VITE_API_URL;

export async function login(email, password) {
  try {
    const res = await fetch(`${BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) throw new Error('Login failed');

    const data = await res.json(); // use .json instead of .text + JSON.parse
    console.log('Parsed data:', data);

    if (!data.user || !data.user.id) {
      throw new Error('User ID missing in response');
    }

    // Try explicitly logging before storing
    console.log('Saving userId to localStorage:', data.user.id);
    localStorage.setItem('userId', data.user.id);
    localStorage.setItem('email', data.user.email);

    // Confirm storage
    console.log('Stored userId:', localStorage.getItem('userId'));

    return data;

  } catch (err) {
    console.error('Login error:', err);
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

  // Same assumption as login
  if (!data.user || !data.user.id) throw new Error('Invalid register response');

  localStorage.setItem('userId', data.user.id);
  localStorage.setItem('email', data.user.email);

  console.log('User ID:', data.user.id);
  return data;
}
