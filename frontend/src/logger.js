export async function log(message) {
  console.log(message);
  try {
    await fetch('/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
  } catch (err) {
    console.error('log failed', err);
  }
}
