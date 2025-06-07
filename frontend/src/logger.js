import axios from 'axios';

export async function log(message) {
  console.log(message);
  try {
    await axios.post('/log', { message });
  } catch (err) {
    console.error('log failed', err);
  }
}
