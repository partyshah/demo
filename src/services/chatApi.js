export async function sendMessageToBackend(messages) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ messages }),
  });
  if (!response.ok) {
    throw new Error('Failed to get response from backend');
  }
  return response.json();
} 